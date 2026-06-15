"""OWID ingestor tests (HTTP mocked with grapher CSV text)."""

from __future__ import annotations

from app.ingest import http, owid
from app.ingest.registry import INDICATORS, IndicatorSpec


def _spec(key):
    return next(s for s in INDICATORS if s.key == key)


def test_owid_categorical_parsing(monkeypatch):
    csv_text = (
        "entity,code,year,stand_alone_policy_or_plan_for_mental_health\n"
        "United States,USA,2020,Yes\n"
        "World,OWID_WRL,2020,Yes\n"  # aggregate kept at fetch, dropped by normalize
        "France,FRA,2017,No\n"
    )
    monkeypatch.setattr(http, "get_text", lambda *a, **k: csv_text)

    raws = owid.fetch(_spec("mh_policy"))
    got = {(r.country_code, r.year, r.value_text) for r in raws}
    assert got == {("USA", 2020, "Yes"), ("OWID_WRL", 2020, "Yes"), ("FRA", 2017, "No")}
    assert all(r.value is None for r in raws)


def test_owid_numeric_parsing(monkeypatch):
    csv_text = "entity,code,year,some_metric\nUnited States,USA,2020,3.5\nBad,USA,2021,n/a\n"
    monkeypatch.setattr(http, "get_text", lambda *a, **k: csv_text)

    spec = IndicatorSpec(
        key="tmp_numeric", source_key="owid", name="Tmp", unit="x",
        category="context", provider_code="some-slug", value_type="numeric",
        extra={"owid_column": "some_metric"},
    )
    raws = owid.fetch(spec)
    # The non-numeric "n/a" row is skipped.
    assert [(r.country_code, r.value) for r in raws] == [("USA", 3.5)]
