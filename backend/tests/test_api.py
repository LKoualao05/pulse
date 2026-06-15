"""API endpoint tests against an isolated seeded database."""

from __future__ import annotations

import json

from app.api.routers import meta


def test_api_root_lists_endpoints_and_crisis_info(client):
    body = client.get("/api").json()
    assert body["name"] == "Pulse API"
    assert "/api/indicators/{key}/series" in body["endpoints"]
    assert "988" in body["crisis_resources"]["us_988"]


def test_summary_endpoint_serves_generated_file(client, tmp_path, monkeypatch):
    payload = {
        "generated_at": "2026-06-14",
        "indicators": [
            {
                "indicator_key": "suicide_rate", "name": "Suicide rate",
                "unit": "per 100k", "category": "outcome", "value_type": "numeric",
                "observation_count": 4, "countries": 2, "year_min": 2019,
                "year_max": 2020, "latest_year": 2020, "global_latest_mean": 14.0,
                "top_country": "United States", "top_value": 14.0,
            }
        ],
    }
    (tmp_path / "summary.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(meta, "PROCESSED_DIR", tmp_path)

    r = client.get("/api/summary")
    assert r.status_code == 200
    assert r.json()["indicators"][0]["indicator_key"] == "suicide_rate"


def test_summary_missing_returns_503(client, tmp_path, monkeypatch):
    monkeypatch.setattr(meta, "PROCESSED_DIR", tmp_path)  # empty dir, no summary.json
    assert client.get("/api/summary").status_code == 503


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["observations"] == 4
    assert body["sources"] == 2


def test_sources_include_license(client):
    r = client.get("/api/sources")
    assert r.status_code == 200
    licenses = {s["key"]: s["license"] for s in r.json()}
    assert licenses["who_gho"] == "CC BY-NC-SA 3.0 IGO"
    assert licenses["owid"] == "CC BY 4.0"


def test_list_and_filter_indicators(client):
    assert len(client.get("/api/indicators").json()) == 2
    outcome = client.get("/api/indicators", params={"category": "outcome"}).json()
    assert [i["key"] for i in outcome] == ["suicide_rate"]


def test_indicator_detail_and_404(client):
    assert client.get("/api/indicators/suicide_rate").json()["unit"] == "per 100,000 population"
    assert client.get("/api/indicators/nope").status_code == 404


def test_series_groups_by_country(client):
    r = client.get("/api/indicators/suicide_rate/series")
    assert r.status_code == 200
    body = r.json()
    assert body["indicator"]["key"] == "suicide_rate"
    assert body["source"]["key"] == "who_gho"  # joined source + license travels with it
    by_country = {s["country_iso3"]: s for s in body["series"]}
    assert set(by_country) == {"USA", "GBR"}
    usa_years = [p["year"] for p in by_country["USA"]["points"]]
    assert usa_years == [2019, 2020]  # ordered


def test_series_country_filter_and_year_range(client):
    r = client.get(
        "/api/indicators/suicide_rate/series",
        params={"countries": "usa", "year_from": 2020},
    )
    body = r.json()
    assert len(body["series"]) == 1
    assert body["series"][0]["country_iso3"] == "USA"
    assert [p["year"] for p in body["series"][0]["points"]] == [2020]


def test_series_rejects_bad_country_code(client):
    r = client.get("/api/indicators/suicide_rate/series", params={"countries": "USAA"})
    assert r.status_code == 422


def test_categorical_series_carries_text(client):
    r = client.get("/api/indicators/mh_policy/series")
    point = r.json()["series"][0]["points"][0]
    assert point["value_text"] == "Yes"
    assert point["value"] is None


def test_countries_endpoint(client):
    r = client.get("/api/indicators/suicide_rate/countries")
    names = {c["iso3"] for c in r.json()}
    assert names == {"USA", "GBR"}
