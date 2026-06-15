"""Normalize raw provider rows into clean, country-level observations.

Responsibilities:
  * Validate that a code is a real ISO-3166-1 alpha-3 *country* (this is how
    we drop provider aggregates like WHO regions, World Bank "WLD"/"AFE",
    or OWID "OWID_*" rows).
  * Attach a human-readable country name.
  * Drop empty values and collapse duplicate (country, year) rows.
"""

from __future__ import annotations

from functools import lru_cache

import pycountry

from app.ingest.base import NormalizedObservation, RawObservation

# Codes used by these providers that are valid countries/areas but missing
# from (or named differently in) pycountry. Kept tiny and explicit.
_SUPPLEMENTAL_NAMES: dict[str, str] = {
    "XKX": "Kosovo",  # World Bank uses XKX
    "KOS": "Kosovo",
}


@lru_cache(maxsize=1024)
def country_name(code: str | None) -> str | None:
    """Return the country name for an ISO-3 code, or None if not a country.

    A return value of ``None`` is the signal that a row is an aggregate /
    region and must be excluded.
    """
    if not code:
        return None
    code = code.strip().upper()
    if len(code) != 3:
        return None
    if code in _SUPPLEMENTAL_NAMES:
        return _SUPPLEMENTAL_NAMES[code]
    match = pycountry.countries.get(alpha_3=code)
    if match is None:
        return None
    # Prefer the common name when pycountry provides one.
    return getattr(match, "common_name", None) or match.name


def is_country(code: str | None) -> bool:
    return country_name(code) is not None


def normalize_observations(
    indicator_key: str, raws: list[RawObservation]
) -> list[NormalizedObservation]:
    """Validate, name, and de-duplicate raw rows for one indicator."""
    seen: set[tuple[str, int]] = set()
    out: list[NormalizedObservation] = []

    for raw in raws:
        name = country_name(raw.country_code)
        if name is None:
            continue  # aggregate / region / unknown code → excluded
        if raw.value is None and not raw.value_text:
            continue  # nothing to record
        try:
            year = int(raw.year)
        except (TypeError, ValueError):
            continue

        iso3 = raw.country_code.strip().upper()
        dedup_key = (iso3, year)
        if dedup_key in seen:
            continue  # first value for a (country, year) wins
        seen.add(dedup_key)

        out.append(
            NormalizedObservation(
                indicator_key=indicator_key,
                country_iso3=iso3,
                country_name=name,
                year=year,
                value=raw.value,
                value_text=raw.value_text,
            )
        )

    out.sort(key=lambda o: (o.country_name, o.year))
    return out
