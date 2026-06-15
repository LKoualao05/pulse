"""WHO GHO ingestor tests (HTTP mocked with realistic OData payloads)."""

from __future__ import annotations

from app.ingest import http, who_gho
from app.ingest.registry import INDICATORS


def _spec(key):
    return next(s for s in INDICATORS if s.key == key)


def test_who_keeps_both_sexes_drops_sex_breakdowns(monkeypatch):
    payload = {
        "value": [
            {"SpatialDim": "USA", "TimeDim": 2019, "Dim1": "SEX_BTSX",
             "Dim2": None, "Dim3": None, "NumericValue": 14.5},
            {"SpatialDim": "USA", "TimeDim": 2019, "Dim1": "SEX_MLE",
             "Dim2": None, "Dim3": None, "NumericValue": 22.0},  # filtered
            {"SpatialDim": "FRA", "TimeDim": 2018, "Dim1": "SEX_BTSX",
             "Dim2": None, "Dim3": None, "NumericValue": 13.0},
        ]
    }
    monkeypatch.setattr(http, "get_json", lambda *a, **k: payload)

    raws = who_gho.fetch(_spec("suicide_rate"))
    by_country = {r.country_code: r.value for r in raws}
    assert by_country == {"USA": 14.5, "FRA": 13.0}


def test_who_indicator_without_sex_dim_drops_breakdowns(monkeypatch):
    payload = {
        "value": [
            {"SpatialDim": "USA", "TimeDim": 2019, "Dim1": None,
             "Dim2": None, "Dim3": None, "NumericValue": 10.0},
            {"SpatialDim": "USA", "TimeDim": 2019, "Dim1": "SEX_MLE",
             "Dim2": None, "Dim3": None, "NumericValue": 12.0},  # not total -> drop
            {"SpatialDim": "FRA", "TimeDim": 2019, "Dim1": None,
             "Dim2": "AGEGROUP_YEARS25-34", "Dim3": None, "NumericValue": 9.0},  # drop
        ]
    }
    monkeypatch.setattr(http, "get_json", lambda *a, **k: payload)

    raws = who_gho.fetch(_spec("psychiatrists"))
    assert [(r.country_code, r.value) for r in raws] == [("USA", 10.0)]


def test_who_skips_rows_missing_value(monkeypatch):
    payload = {
        "value": [
            {"SpatialDim": "USA", "TimeDim": 2019, "Dim1": "SEX_BTSX",
             "Dim2": None, "Dim3": None, "NumericValue": None},  # no value
        ]
    }
    monkeypatch.setattr(http, "get_json", lambda *a, **k: payload)
    assert who_gho.fetch(_spec("suicide_rate")) == []
