"""The Claude-powered "Explain this chart" endpoint.

Rate-limited more strictly than the data routes because each call may hit the
Anthropic API.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.config import get_settings
from app.db import get_db
from app.schemas import (
    CountrySeries,
    ExplainRequest,
    ExplainResponse,
    SeriesPoint,
)
from app.services.explain import generate_explanation

# The global SlowAPIMiddleware rate limit (PULSE_RATE_LIMIT) applies to this
# route too, throttling calls that reach the Anthropic API.
router = APIRouter(tags=["explain"])

_MAX_COUNTRIES = 12


@router.post("/explain", response_model=ExplainResponse)
def explain(
    payload: ExplainRequest,
    db: Session = Depends(get_db),
) -> ExplainResponse:
    indicator = crud.get_indicator(db, payload.indicator_key)
    if indicator is None:
        raise HTTPException(status_code=404, detail="Indicator not found.")

    codes: list[str] = []
    for raw in payload.countries:
        code = raw.strip().upper()
        if not code:
            continue
        if len(code) != 3 or not code.isalpha():
            raise HTTPException(status_code=422, detail=f"Invalid country code: {raw!r}")
        if code not in codes:
            codes.append(code)
    if len(codes) > _MAX_COUNTRIES:
        raise HTTPException(status_code=422, detail=f"Too many countries (max {_MAX_COUNTRIES}).")

    observations = crud.get_observations(
        db, payload.indicator_key, countries=codes or None, year_from=payload.year_from
    )
    if not observations:
        raise HTTPException(status_code=404, detail="No data for this selection.")

    grouped: dict[str, CountrySeries] = {}
    for obs in observations:
        series = grouped.get(obs.country_iso3)
        if series is None:
            series = CountrySeries(
                country_iso3=obs.country_iso3,
                country_name=obs.country_name,
                points=[],
            )
            grouped[obs.country_iso3] = series
        series.points.append(
            SeriesPoint(year=obs.year, value=obs.value, value_text=obs.value_text)
        )

    result = generate_explanation(
        settings=get_settings(),
        indicator=indicator,
        source=indicator.source,
        series=list(grouped.values()),
    )
    return ExplainResponse(
        summary=result.summary,
        model=result.model,
        generated_by=result.generated_by,
    )
