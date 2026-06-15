"""The Claude-powered "Explain this chart" feature.

Design notes:
  * The prompt is built from PRE-COMPUTED numbers (first/last/change per
    country), never a raw data dump — this keeps tokens low and stops the model
    inventing figures.
  * The Anthropic API key is read ONLY from the environment (via Settings).
  * If no key is configured, or the API call fails, we degrade gracefully to a
    deterministic templated summary and flag it as ``generated_by="fallback"``
    so the UI can be honest about it.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.models import Indicator, Source
from app.schemas import CountrySeries

_SYSTEM_PROMPT = (
    "You explain public mental-health and well-being statistics to non-experts "
    "in plain, calm, accurate language. You will be given pre-computed figures — "
    "use ONLY those numbers and do not invent or estimate any others. Write 2-3 "
    "short paragraphs. Be measured and non-sensational, especially with sensitive "
    "topics such as suicide; never give medical advice or causal claims the data "
    "does not support. If the data is a single-year snapshot, say so. Do not add a "
    "crisis hotline (the page already shows one)."
)


@dataclass
class ExplainResult:
    summary: str
    model: str
    generated_by: str  # "claude" | "fallback"


def _series_facts(
    indicator: Indicator, source: Source, series: list[CountrySeries]
) -> str:
    """Render the selected data as compact, model-friendly facts."""
    lines = [
        f"Indicator: {indicator.name} (unit: {indicator.unit}; "
        f"category: {indicator.category}).",
        f"Source: {source.attribution} (license: {source.license}).",
        "",
        "Per-country figures:",
    ]
    if indicator.value_type == "categorical":
        for cs in series:
            last = cs.points[-1] if cs.points else None
            if last is None:
                continue
            lines.append(f"- {cs.country_name}: {last.value_text} (as of {last.year})")
    else:
        for cs in series:
            pts = [p for p in cs.points if p.value is not None]
            if not pts:
                continue
            first, last = pts[0], pts[-1]
            if first.year == last.year:
                lines.append(
                    f"- {cs.country_name}: {last.value:.2f} in {last.year} "
                    f"(single-year snapshot)"
                )
            else:
                change = last.value - first.value
                pct = (change / first.value * 100) if first.value else 0.0
                lines.append(
                    f"- {cs.country_name}: {first.value:.2f} in {first.year} "
                    f"-> {last.value:.2f} in {last.year} "
                    f"(change {change:+.2f}, {pct:+.1f}%)"
                )
    return "\n".join(lines)


def _fallback_summary(
    indicator: Indicator, series: list[CountrySeries], facts: str
) -> str:
    """A deterministic, non-AI explanation used when Claude is unavailable."""
    intro = (
        f"This chart shows {indicator.name.lower()} measured in "
        f"{indicator.unit}. Here is what the selected data indicates:"
    )
    bullets = facts.split("Per-country figures:\n", 1)[-1]
    note = (
        "\n\n(AI explanations are unavailable because no API key is configured, "
        "so this is a plain numeric summary. Always check figures against the "
        "cited source.)"
    )
    return f"{intro}\n\n{bullets}{note}"


def generate_explanation(
    settings: Settings,
    indicator: Indicator,
    source: Source,
    series: list[CountrySeries],
) -> ExplainResult:
    facts = _series_facts(indicator, source, series)

    if not settings.anthropic_enabled:
        return ExplainResult(
            summary=_fallback_summary(indicator, series, facts),
            model=settings.anthropic_model,
            generated_by="fallback",
        )

    user_prompt = (
        f"{facts}\n\n"
        "Explain this chart to a non-expert reader in plain language."
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model=settings.anthropic_model,  # claude-haiku-4-5 by default
            max_tokens=600,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(
            block.text for block in message.content if block.type == "text"
        ).strip()
        if not text:
            raise ValueError("empty response")
        return ExplainResult(
            summary=text, model=settings.anthropic_model, generated_by="claude"
        )
    except Exception:
        # Any failure (bad key, network, rate limit) → honest fallback.
        return ExplainResult(
            summary=_fallback_summary(indicator, series, facts),
            model=settings.anthropic_model,
            generated_by="fallback",
        )
