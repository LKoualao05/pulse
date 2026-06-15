"""Tests for the Claude 'Explain this chart' endpoint and service.

The Anthropic SDK is never called for real — we exercise the fallback path and
monkeypatch a fake client for the 'claude' path.
"""

from __future__ import annotations

import sys
import types

from app.config import get_settings
from app.models import Indicator, Source
from app.schemas import CountrySeries, SeriesPoint
from app.services import explain as explain_service


def _series():
    return [
        CountrySeries(
            country_iso3="USA",
            country_name="United States",
            points=[
                SeriesPoint(year=2015, value=12.8, value_text=None),
                SeriesPoint(year=2021, value=14.2, value_text=None),
            ],
        )
    ]


def _indicator_and_source():
    src = Source(
        key="who_gho", name="WHO GHO", url="u", license="CC BY-NC-SA 3.0 IGO",
        license_url="lu", attribution="WHO", accessed_at="2026-06-14", notes="",
    )
    ind = Indicator(
        key="suicide_rate", source_key="who_gho", name="Suicide rate",
        unit="per 100,000 population", category="outcome", description="d",
        value_type="numeric",
    )
    ind.source = src
    return ind, src


# ---- service-level unit tests ----

def test_fallback_when_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.anthropic_enabled is False

    ind, src = _indicator_and_source()
    result = explain_service.generate_explanation(settings, ind, src, _series())
    assert result.generated_by == "fallback"
    assert "12.80 in 2015" in result.summary  # uses the real numbers
    get_settings.cache_clear()


def test_claude_path_with_fake_sdk(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.anthropic_enabled is True

    # Build a fake `anthropic` module with the minimal surface we use.
    fake = types.ModuleType("anthropic")

    class _Block:
        type = "text"
        text = "Suicide rates in the US rose modestly between 2015 and 2021."

    class _Msg:
        content = [_Block()]

    class _Messages:
        def create(self, **kwargs):
            assert kwargs["model"] == "claude-haiku-4-5"
            assert "United States" in kwargs["messages"][0]["content"]
            return _Msg()

    class _Client:
        def __init__(self, api_key=None):
            assert api_key == "sk-test-123"  # key comes from env via settings
            self.messages = _Messages()

    fake.Anthropic = _Client
    monkeypatch.setitem(sys.modules, "anthropic", fake)

    ind, src = _indicator_and_source()
    result = explain_service.generate_explanation(settings, ind, src, _series())
    assert result.generated_by == "claude"
    assert result.model == "claude-haiku-4-5"
    assert "rose modestly" in result.summary
    get_settings.cache_clear()


def test_claude_failure_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
    get_settings.cache_clear()
    settings = get_settings()

    fake = types.ModuleType("anthropic")

    class _Client:
        def __init__(self, api_key=None):
            self.messages = self

        def create(self, **kwargs):
            raise RuntimeError("boom")

    fake.Anthropic = _Client
    monkeypatch.setitem(sys.modules, "anthropic", fake)

    ind, src = _indicator_and_source()
    result = explain_service.generate_explanation(settings, ind, src, _series())
    assert result.generated_by == "fallback"
    get_settings.cache_clear()


# ---- endpoint tests (fallback path, no key in test env) ----

def test_explain_endpoint_fallback(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_settings.cache_clear()
    r = client.post(
        "/api/explain",
        json={"indicator_key": "suicide_rate", "countries": ["USA"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["generated_by"] == "fallback"
    assert "United States" in body["summary"]
    get_settings.cache_clear()


def test_explain_endpoint_unknown_indicator(client):
    r = client.post("/api/explain", json={"indicator_key": "nope"})
    assert r.status_code == 404


def test_explain_endpoint_bad_country(client):
    r = client.post(
        "/api/explain",
        json={"indicator_key": "suicide_rate", "countries": ["TOOLONG"]},
    )
    assert r.status_code == 422
