"""Indicator and time-series endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.db import get_db
from app.schemas import (
    CountrySeries,
    IndicatorOut,
    SeriesPoint,
    SeriesResponse,
    SourceOut,
)

router = APIRouter(tags=["indicators"])

_MAX_COUNTRIES = 12


def _parse_countries(countries: str | None) -> list[str] | None:
    """Validate and normalize a comma-separated ISO-3 list."""
    if not countries:
        return None
    codes: list[str] = []
    for raw in countries.split(","):
        code = raw.strip().upper()
        if not code:
            continue
        if len(code) != 3 or not code.isalpha():
            raise HTTPException(
                status_code=422, detail=f"Invalid country code: {raw!r}"
            )
        if code not in codes:
            codes.append(code)
    if len(codes) > _MAX_COUNTRIES:
        raise HTTPException(
            status_code=422,
            detail=f"Too many countries (max {_MAX_COUNTRIES}).",
        )
    return codes or None


@router.get("/indicators", response_model=list[IndicatorOut])
def list_indicators(
    category: str | None = Query(default=None, max_length=40),
    db: Session = Depends(get_db),
) -> list[IndicatorOut]:
    return [
        IndicatorOut.model_validate(i) for i in crud.list_indicators(db, category)
    ]


@router.get("/indicators/{key}", response_model=IndicatorOut)
def get_indicator(key: str, db: Session = Depends(get_db)) -> IndicatorOut:
    indicator = crud.get_indicator(db, key)
    if indicator is None:
        raise HTTPException(status_code=404, detail="Indicator not found.")
    return IndicatorOut.model_validate(indicator)


@router.get("/indicators/{key}/countries")
def get_countries(key: str, db: Session = Depends(get_db)) -> list[dict[str, str]]:
    if crud.get_indicator(db, key) is None:
        raise HTTPException(status_code=404, detail="Indicator not found.")
    return crud.available_countries(db, key)


@router.get("/indicators/{key}/series", response_model=SeriesResponse)
def get_series(
    key: str,
    countries: str | None = Query(default=None, max_length=200),
    year_from: int | None = Query(default=None, ge=1900, le=2100),
    year_to: int | None = Query(default=None, ge=1900, le=2100),
    db: Session = Depends(get_db),
) -> SeriesResponse:
    indicator = crud.get_indicator(db, key)
    if indicator is None:
        raise HTTPException(status_code=404, detail="Indicator not found.")

    code_list = _parse_countries(countries)
    observations = crud.get_observations(
        db, key, countries=code_list, year_from=year_from, year_to=year_to
    )

    # Group ordered observations into per-country series.
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

    return SeriesResponse(
        indicator=IndicatorOut.model_validate(indicator),
        source=SourceOut.model_validate(indicator.source),
        series=list(grouped.values()),
    )
