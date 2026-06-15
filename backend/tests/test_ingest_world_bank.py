"""World Bank ingestor tests (HTTP mocked, including pagination)."""

from __future__ import annotations

from app.ingest import http, world_bank
from app.ingest.registry import INDICATORS


def _spec(key):
    return next(s for s in INDICATORS if s.key == key)


def test_world_bank_parses_and_paginates(monkeypatch):
    pages = {
        1: [
            {"page": 1, "pages": 2, "per_page": 20000, "total": 4},
            [
                {"countryiso3code": "USA", "date": "2020", "value": 12000.0},
                {"countryiso3code": "WLD", "date": "2020", "value": 9000.0},
            ],
        ],
        2: [
            {"page": 2, "pages": 2, "per_page": 20000, "total": 4},
            [
                {"countryiso3code": "GBR", "date": "2019", "value": 5000.0},
                {"countryiso3code": "USA", "date": "2019", "value": None},  # skipped
            ],
        ],
    }

    def fake_get_json(url, params=None, cache_key=None):
        return pages[params["page"]]

    monkeypatch.setattr(http, "get_json", fake_get_json)

    raws = world_bank.fetch(_spec("health_expenditure_pc"))
    # WLD is kept at fetch stage (filtered later by normalize); null is skipped.
    triples = {(r.country_code, r.year, r.value) for r in raws}
    assert triples == {("USA", 2020, 12000.0), ("WLD", 2020, 9000.0), ("GBR", 2019, 5000.0)}


def test_world_bank_handles_error_payload(monkeypatch):
    # API sometimes returns a message dict instead of [meta, rows].
    monkeypatch.setattr(http, "get_json", lambda *a, **k: {"message": "bad"})
    assert world_bank.fetch(_spec("unemployment")) == []
