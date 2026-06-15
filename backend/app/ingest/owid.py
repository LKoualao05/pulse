"""Our World in Data (grapher CSV) ingestor.

Only series that OWID is permitted to redistribute are used. OWID's
IHME-derived prevalence charts return HTTP 403 ("non-redistributable") and are
intentionally excluded from the registry — we never attempt to fetch them.

CSV shape:
    entity,code,year,<value_column>
"""

from __future__ import annotations

import csv
import io

from app.ingest import http
from app.ingest.base import RawObservation
from app.ingest.registry import IndicatorSpec

_BASE = "https://ourworldindata.org/grapher"


def fetch(spec: IndicatorSpec) -> list[RawObservation]:
    value_col = spec.extra.get("owid_column")
    text = http.get_text(
        f"{_BASE}/{spec.provider_code}.csv",
        params={"csvType": "full", "useColumnShortNames": "true"},
        cache_key=f"owid_{spec.key}.csv",
    )

    reader = csv.DictReader(io.StringIO(text))
    if value_col is None:
        # Fall back to the 4th column if not specified.
        non_key = [c for c in (reader.fieldnames or []) if c not in ("entity", "code", "year")]
        value_col = non_key[0] if non_key else None

    out: list[RawObservation] = []
    for row in reader:
        code = row.get("code")
        year = row.get("year")
        if not code or not year:
            continue
        cell = row.get(value_col) if value_col else None
        if cell is None or cell == "":
            continue
        try:
            year_int = int(year)
        except ValueError:
            continue

        if spec.value_type == "numeric":
            try:
                out.append(
                    RawObservation(country_code=code, year=year_int, value=float(cell))
                )
            except ValueError:
                continue
        else:
            out.append(
                RawObservation(country_code=code, year=year_int, value_text=str(cell))
            )
    return out
