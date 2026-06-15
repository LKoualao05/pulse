"""Ingestion orchestrator.

Run with::

    python -m app.ingest.run

For every indicator in the registry it fetches the provider data, normalizes
it to clean country-level rows, and writes three committed artifacts plus a
regenerated summary:

    data/processed/sources.csv
    data/processed/indicators.csv
    data/processed/observations.csv
    data/processed/summary.json

These artifacts (not live API calls) are what the deployed app and the daily
GitHub Action consume.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import statistics
from collections import defaultdict
from dataclasses import dataclass

from app.config import PROCESSED_DIR
from app.ingest import owid, who_gho, world_bank
from app.ingest.base import NormalizedObservation
from app.ingest.registry import INDICATORS, SOURCES, IndicatorSpec
from app.transform.normalize import normalize_observations

# Dispatch table: provider key -> fetch function.
_FETCHERS = {
    "who_gho": who_gho.fetch,
    "world_bank": world_bank.fetch,
    "owid": owid.fetch,
}


@dataclass
class IngestReport:
    accessed_at: str
    observations: list[NormalizedObservation]
    per_indicator_counts: dict[str, int]


def _today() -> str:
    return dt.date.today().isoformat()


def build_dataset(specs: list[IndicatorSpec] | None = None) -> IngestReport:
    """Fetch + normalize all indicators. Network-bound; mocked in tests."""
    specs = specs if specs is not None else INDICATORS
    all_obs: list[NormalizedObservation] = []
    counts: dict[str, int] = {}

    for spec in specs:
        fetcher = _FETCHERS[spec.source_key]
        raws = fetcher(spec)
        normalized = normalize_observations(spec.key, raws)
        counts[spec.key] = len(normalized)
        all_obs.extend(normalized)
        print(f"  {spec.key:<24} {len(normalized):>6} rows  ({spec.source_key})")

    return IngestReport(
        accessed_at=_today(), observations=all_obs, per_indicator_counts=counts
    )


def _summarize(report: IngestReport) -> dict:
    by_indicator: dict[str, list[NormalizedObservation]] = defaultdict(list)
    for obs in report.observations:
        by_indicator[obs.indicator_key].append(obs)

    summaries = []
    for spec in INDICATORS:
        rows = by_indicator.get(spec.key, [])
        if not rows:
            summaries.append(
                {
                    "indicator_key": spec.key,
                    "name": spec.name,
                    "unit": spec.unit,
                    "category": spec.category,
                    "value_type": spec.value_type,
                    "observation_count": 0,
                    "countries": 0,
                    "year_min": None,
                    "year_max": None,
                    "latest_year": None,
                    "global_latest_mean": None,
                    "top_country": None,
                    "top_value": None,
                }
            )
            continue

        years = [r.year for r in rows]
        latest_year = max(years)
        countries = {r.country_iso3 for r in rows}

        latest_numeric = [
            r for r in rows if r.year == latest_year and r.value is not None
        ]
        global_mean = (
            round(statistics.fmean(r.value for r in latest_numeric), 3)
            if latest_numeric
            else None
        )
        top = max(latest_numeric, key=lambda r: r.value, default=None)

        summaries.append(
            {
                "indicator_key": spec.key,
                "name": spec.name,
                "unit": spec.unit,
                "category": spec.category,
                "value_type": spec.value_type,
                "observation_count": len(rows),
                "countries": len(countries),
                "year_min": min(years),
                "year_max": max(years),
                "latest_year": latest_year,
                "global_latest_mean": global_mean,
                "top_country": top.country_name if top else None,
                "top_value": round(top.value, 3) if top and top.value is not None else None,
            }
        )

    return {"generated_at": report.accessed_at, "indicators": summaries}


def write_artifacts(report: IngestReport) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # sources.csv
    with (PROCESSED_DIR / "sources.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["key", "name", "url", "license", "license_url", "attribution",
             "accessed_at", "notes"]
        )
        for src in SOURCES.values():
            w.writerow([
                src.key, src.name, src.url, src.license, src.license_url,
                src.attribution, report.accessed_at, src.notes,
            ])

    # indicators.csv
    with (PROCESSED_DIR / "indicators.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["key", "source_key", "name", "unit", "category", "description", "value_type"]
        )
        for spec in INDICATORS:
            w.writerow([
                spec.key, spec.source_key, spec.name, spec.unit, spec.category,
                spec.description, spec.value_type,
            ])

    # observations.csv
    with (PROCESSED_DIR / "observations.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["indicator_key", "country_iso3", "country_name", "year", "value", "value_text"]
        )
        for o in report.observations:
            w.writerow([
                o.indicator_key, o.country_iso3, o.country_name, o.year,
                "" if o.value is None else o.value,
                "" if o.value_text is None else o.value_text,
            ])

    # summary.json
    summary = _summarize(report)
    (PROCESSED_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    print("Pulse ingestion — fetching public datasets...")
    report = build_dataset()
    write_artifacts(report)
    print(
        f"Done. {len(report.observations)} observations across "
        f"{len(report.per_indicator_counts)} indicators "
        f"-> {PROCESSED_DIR}"
    )


if __name__ == "__main__":
    main()
