"""Pydantic response models for the public API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    name: str
    url: str
    license: str
    license_url: str
    attribution: str
    accessed_at: str
    notes: str = ""


class IndicatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    source_key: str
    name: str
    unit: str
    category: str
    description: str = ""
    value_type: str = "numeric"


class SeriesPoint(BaseModel):
    year: int
    value: float | None = None
    value_text: str | None = None


class CountrySeries(BaseModel):
    country_iso3: str
    country_name: str
    points: list[SeriesPoint]


class SeriesResponse(BaseModel):
    """A series for one indicator, optionally across several countries."""

    indicator: IndicatorOut
    source: SourceOut
    series: list[CountrySeries]


class HealthResponse(BaseModel):
    status: str
    indicators: int
    observations: int
    sources: int


class IndicatorSummary(BaseModel):
    indicator_key: str
    name: str
    unit: str
    category: str
    value_type: str
    observation_count: int
    countries: int
    year_min: int | None = None
    year_max: int | None = None
    latest_year: int | None = None
    global_latest_mean: float | None = None
    top_country: str | None = None
    top_value: float | None = None


class SummaryResponse(BaseModel):
    generated_at: str
    indicators: list[IndicatorSummary]


class ExplainRequest(BaseModel):
    indicator_key: str = Field(..., max_length=60)
    countries: list[str] = Field(default_factory=list, max_length=12)
    year_from: int | None = Field(default=None, ge=1900, le=2100)


class ExplainResponse(BaseModel):
    summary: str
    model: str
    generated_by: str  # "claude" | "fallback"
