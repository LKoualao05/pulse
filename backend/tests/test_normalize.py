"""Tests for ISO-3 validation and observation normalization."""

from __future__ import annotations

from app.ingest.base import RawObservation
from app.transform.normalize import country_name, is_country, normalize_observations


def test_country_name_resolves_real_countries():
    assert country_name("USA") == "United States"
    assert country_name("gbr") == "United Kingdom"  # case-insensitive
    assert country_name("XKX") == "Kosovo"  # supplemental code


def test_country_name_rejects_aggregates_and_junk():
    assert country_name("WLD") is None  # World Bank world aggregate
    assert country_name("AFE") is None  # WB region
    assert country_name("OWID_WRL") is None  # OWID aggregate (wrong length)
    assert country_name("") is None
    assert country_name(None) is None
    assert is_country("USA") is True
    assert is_country("WLD") is False


def test_normalize_filters_aggregates_and_empties():
    raws = [
        RawObservation("USA", 2020, 14.0),
        RawObservation("WLD", 2020, 9.0),     # aggregate -> dropped
        RawObservation("FRA", 2020, None),    # empty -> dropped
        RawObservation("GBR", 2019, 7.0),
    ]
    out = normalize_observations("suicide_rate", raws)
    iso3 = {o.country_iso3 for o in out}
    assert iso3 == {"USA", "GBR"}
    assert all(o.indicator_key == "suicide_rate" for o in out)


def test_normalize_dedupes_country_year():
    raws = [
        RawObservation("USA", 2020, 14.0),
        RawObservation("USA", 2020, 99.0),  # duplicate (country, year) -> first wins
    ]
    out = normalize_observations("suicide_rate", raws)
    assert len(out) == 1
    assert out[0].value == 14.0


def test_normalize_keeps_categorical_text():
    raws = [RawObservation("USA", 2020, value_text="Yes")]
    out = normalize_observations("mh_policy", raws)
    assert len(out) == 1
    assert out[0].value is None
    assert out[0].value_text == "Yes"
    assert out[0].country_name == "United States"
