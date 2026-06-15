"""Tests for the ingestion orchestrator (fetchers mocked)."""

from __future__ import annotations

import csv
import json

from app.ingest import run
from app.ingest.base import RawObservation


def _fake_fetchers():
    def numeric(spec):
        return [
            RawObservation("USA", 2020, 10.0),
            RawObservation("WLD", 2020, 5.0),   # aggregate -> dropped by normalize
            RawObservation("GBR", 2019, 8.0),
        ]

    def categorical(spec):
        return [RawObservation("USA", 2020, value_text="Yes")]

    def dispatch(spec):
        return categorical(spec) if spec.value_type == "categorical" else numeric(spec)

    return {"who_gho": dispatch, "world_bank": dispatch, "owid": dispatch}


def test_build_and_write_artifacts(monkeypatch, tmp_path):
    monkeypatch.setattr(run, "_FETCHERS", _fake_fetchers())
    monkeypatch.setattr(run, "PROCESSED_DIR", tmp_path)

    report = run.build_dataset()
    run.write_artifacts(report)

    # All four artifacts exist.
    for name in ("sources.csv", "indicators.csv", "observations.csv", "summary.json"):
        assert (tmp_path / name).exists(), name

    # Aggregates filtered: every observation row is a real country.
    with (tmp_path / "observations.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows, "expected observation rows"
    assert all(r["country_iso3"] != "WLD" for r in rows)

    # Summary is well-formed and reflects the data.
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert "generated_at" in summary
    suicide = next(s for s in summary["indicators"] if s["indicator_key"] == "suicide_rate")
    assert suicide["countries"] == 2  # USA + GBR
    assert suicide["latest_year"] == 2020
