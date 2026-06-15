"""Tests for seeding the database from processed CSV artifacts."""

from __future__ import annotations

from app.models import Observation
from app.seed import database_is_populated, seed


def _write_processed(dirpath):
    (dirpath / "sources.csv").write_text(
        "key,name,url,license,license_url,attribution,accessed_at,notes\n"
        "who_gho,WHO,https://who.int,CC BY-NC-SA 3.0 IGO,https://cc,WHO,2026-06-14,note\n",
        encoding="utf-8",
    )
    (dirpath / "indicators.csv").write_text(
        "key,source_key,name,unit,category,description,value_type\n"
        "suicide_rate,who_gho,Suicide rate,per 100k,outcome,desc,numeric\n",
        encoding="utf-8",
    )
    (dirpath / "observations.csv").write_text(
        "indicator_key,country_iso3,country_name,year,value,value_text\n"
        "suicide_rate,USA,United States,2020,14.0,\n"
        "suicide_rate,GBR,United Kingdom,2019,7.0,\n",
        encoding="utf-8",
    )


def test_seed_loads_and_is_idempotent(db, tmp_path):
    _write_processed(tmp_path)
    assert database_is_populated(db) is False

    loaded = seed(db, processed_dir=tmp_path)
    assert loaded == 2
    assert db.query(Observation).count() == 2

    # Second call is a no-op because data already exists.
    again = seed(db, processed_dir=tmp_path)
    assert again == 0
    assert db.query(Observation).count() == 2


def test_seed_force_reloads(db, tmp_path):
    _write_processed(tmp_path)
    seed(db, processed_dir=tmp_path)
    reloaded = seed(db, processed_dir=tmp_path, force=True)
    assert reloaded == 2
