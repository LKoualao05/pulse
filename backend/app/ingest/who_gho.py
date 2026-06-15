"""WHO Global Health Observatory (GHO) OData API ingestor.

Endpoint shape:
    https://ghoapi.azureedge.net/api/{IndicatorCode}
returns ``{"value": [ {SpatialDim, TimeDim, Dim1..3, NumericValue, ...}, ... ]}``.

We request only country-level rows and keep "total" breakdowns (both sexes,
all ages), discarding sex/age sub-rows so each (country, year) is aggregate.
"""

from __future__ import annotations

from app.ingest import http
from app.ingest.base import RawObservation
from app.ingest.registry import IndicatorSpec

_BASE = "https://ghoapi.azureedge.net/api"

# Dimension values that represent an aggregate "total" rather than a breakdown.
_TOTAL_MARKERS = ("BTSX", "ALL", "TOTL", "TOTAL")


def _is_total(value: str | None) -> bool:
    if value is None:
        return True
    v = value.upper()
    return any(marker in v for marker in _TOTAL_MARKERS)


def _row_is_aggregate(row: dict, required: dict[str, str]) -> bool:
    """True if a row is a country-level aggregate matching required dims."""
    for dim in ("Dim1", "Dim2", "Dim3"):
        val = row.get(dim)
        if dim in required:
            if val != required[dim]:
                return False
        elif not _is_total(val):
            return False
    return True


def fetch(spec: IndicatorSpec) -> list[RawObservation]:
    required: dict[str, str] = dict(spec.extra.get("who_dims", {}))

    # OData $filter: country rows only, plus any explicitly required dimension.
    filter_parts = ["SpatialDimType eq 'COUNTRY'"]
    for dim, val in required.items():
        filter_parts.append(f"{dim} eq '{val}'")
    params = {"$filter": " and ".join(filter_parts)}

    payload = http.get_json(
        f"{_BASE}/{spec.provider_code}",
        params=params,
        cache_key=f"who_{spec.key}.json",
    )

    out: list[RawObservation] = []
    for row in payload.get("value", []):
        if not _row_is_aggregate(row, required):
            continue
        code = row.get("SpatialDim")
        year = row.get("TimeDim")
        value = row.get("NumericValue")
        if code is None or year is None or value is None:
            continue
        out.append(RawObservation(country_code=code, year=year, value=float(value)))
    return out
