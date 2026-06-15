"""World Bank Indicators API ingestor.

Endpoint shape:
    https://api.worldbank.org/v2/country/all/indicator/{code}?format=json
returns ``[ {meta...}, [ {countryiso3code, date, value, ...}, ... ] ]``.
The first element is pagination metadata; the second is the data rows.
"""

from __future__ import annotations

from app.ingest import http
from app.ingest.base import RawObservation
from app.ingest.registry import IndicatorSpec

_BASE = "https://api.worldbank.org/v2"
_PER_PAGE = 20000


def fetch(spec: IndicatorSpec) -> list[RawObservation]:
    out: list[RawObservation] = []
    page = 1
    while True:
        payload = http.get_json(
            f"{_BASE}/country/all/indicator/{spec.provider_code}",
            params={"format": "json", "per_page": _PER_PAGE, "page": page},
            cache_key=f"wb_{spec.key}_p{page}.json",
        )

        # Defensive: API returns [meta, rows]; a bad request returns a dict/message.
        if not isinstance(payload, list) or len(payload) < 2:
            break
        meta, rows = payload[0], payload[1]
        if not rows:
            break

        for row in rows:
            code = row.get("countryiso3code")
            date = row.get("date")
            value = row.get("value")
            if not code or date is None or value is None:
                continue
            try:
                out.append(
                    RawObservation(country_code=code, year=int(date), value=float(value))
                )
            except (TypeError, ValueError):
                continue

        total_pages = int(meta.get("pages", 1) or 1)
        if page >= total_pages:
            break
        page += 1

    return out
