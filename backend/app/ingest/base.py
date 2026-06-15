"""Shared dataclasses and the source contract for ingestion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RawObservation:
    """A single value as returned by a provider, before normalization.

    ``country_code`` is the provider's code (almost always ISO-3166 alpha-3).
    """

    country_code: str
    year: int
    value: float | None = None
    value_text: str | None = None


@dataclass(slots=True)
class NormalizedObservation:
    """An aggregate observation after ISO-3 validation and naming."""

    indicator_key: str
    country_iso3: str
    country_name: str
    year: int
    value: float | None = None
    value_text: str | None = None
