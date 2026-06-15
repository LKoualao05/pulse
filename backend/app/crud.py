"""Read-only data-access helpers.

All queries use SQLAlchemy's parameterized query builder (no string-formatted
SQL), so user input cannot be interpolated into a statement.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Indicator, Observation, Source


def list_sources(db: Session) -> list[Source]:
    return list(db.scalars(select(Source).order_by(Source.name)))


def get_source(db: Session, key: str) -> Source | None:
    return db.get(Source, key)


def list_indicators(db: Session, category: str | None = None) -> list[Indicator]:
    stmt = select(Indicator).order_by(Indicator.category, Indicator.name)
    if category:
        stmt = stmt.where(Indicator.category == category)
    return list(db.scalars(stmt))


def get_indicator(db: Session, key: str) -> Indicator | None:
    return db.get(Indicator, key)


def counts(db: Session) -> dict[str, int]:
    return {
        "sources": db.scalar(select(func.count()).select_from(Source)) or 0,
        "indicators": db.scalar(select(func.count()).select_from(Indicator)) or 0,
        "observations": db.scalar(select(func.count()).select_from(Observation)) or 0,
    }


def get_observations(
    db: Session,
    indicator_key: str,
    countries: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[Observation]:
    stmt = select(Observation).where(Observation.indicator_key == indicator_key)
    if countries:
        stmt = stmt.where(Observation.country_iso3.in_(countries))
    if year_from is not None:
        stmt = stmt.where(Observation.year >= year_from)
    if year_to is not None:
        stmt = stmt.where(Observation.year <= year_to)
    stmt = stmt.order_by(Observation.country_name, Observation.year)
    return list(db.scalars(stmt))


def available_countries(db: Session, indicator_key: str) -> list[dict[str, str]]:
    stmt = (
        select(Observation.country_iso3, Observation.country_name)
        .where(Observation.indicator_key == indicator_key)
        .distinct()
        .order_by(Observation.country_name)
    )
    return [{"iso3": iso3, "name": name} for iso3, name in db.execute(stmt)]
