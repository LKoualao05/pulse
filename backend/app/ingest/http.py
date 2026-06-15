"""Tiny HTTP helper with retries and optional on-disk caching.

Source modules call ``http.get_json`` / ``http.get_text`` (referencing the
module, not importing the functions) so tests can monkeypatch them cleanly.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from app.config import RAW_DIR

_USER_AGENT = "Pulse-Observatory/0.1 (+https://github.com/; data ingestion; contact via repo)"
_TIMEOUT = 30
_RETRIES = 3
_BACKOFF = 2.0


class FetchError(RuntimeError):
    """Raised when a source cannot be fetched after retries."""


def _request(url: str, params: dict[str, Any] | None) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(1, _RETRIES + 1):
        try:
            resp = requests.get(
                url,
                params=params,
                headers={"User-Agent": _USER_AGENT},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:  # network / HTTP error
            last_exc = exc
            if attempt < _RETRIES:
                time.sleep(_BACKOFF * attempt)
    raise FetchError(f"Failed to fetch {url} after {_RETRIES} attempts: {last_exc}")


def _cache_write(cache_key: str | None, text: str) -> None:
    if not cache_key:
        return
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / cache_key).write_text(text, encoding="utf-8")


def get_json(
    url: str, params: dict[str, Any] | None = None, cache_key: str | None = None
) -> Any:
    """GET a URL and parse JSON, retrying on transient failures."""
    resp = _request(url, params)
    _cache_write(cache_key, resp.text)
    return resp.json()


def get_text(
    url: str, params: dict[str, Any] | None = None, cache_key: str | None = None
) -> str:
    """GET a URL and return the body as text, retrying on transient failures."""
    resp = _request(url, params)
    _cache_write(cache_key, resp.text)
    return resp.text
