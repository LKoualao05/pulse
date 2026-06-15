"""Shared slowapi limiter instance.

Kept in its own module so both ``main`` and individual routers can apply
per-route limits without a circular import.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
