"""Seed the database from the committed ``data/processed`` CSV artifacts.

This decouples serving from ingestion: the daily GitHub Action refreshes the
CSVs, and the app rebuilds its database from them on startup. No live API call
is needed to boot the API.
"""

from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import PROCESSED_DIR
from app.db import SessionLocal, engine
from app.models import Base, Indicator, Observation, Source


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def database_is_populated(db: Session) -> bool:
    return db.scalar(select(func.count()).select_from(Observation)) > 0


def seed(db: Session, processed_dir: Path = PROCESSED_DIR, force: bool = False) -> int:
    """Load processed CSVs into the DB. Returns number of observations loaded.

    Idempotent: if the DB already has data and ``force`` is False, it is a no-op.
    """
    if not force and database_is_populated(db):
        return 0

    # Clear existing rows (order matters for FK integrity).
    db.query(Observation).delete()
    db.query(Indicator).delete()
    db.query(Source).delete()
    db.flush()

    for row in _read_csv(processed_dir / "sources.csv"):
        db.add(Source(**row))

    for row in _read_csv(processed_dir / "indicators.csv"):
        db.add(Indicator(**row))
    db.flush()

    count = 0
    for row in _read_csv(processed_dir / "observations.csv"):
        value = row.get("value") or ""
        value_text = row.get("value_text") or ""
        db.add(
            Observation(
                indicator_key=row["indicator_key"],
                country_iso3=row["country_iso3"],
                country_name=row["country_name"],
                year=int(row["year"]),
                value=float(value) if value != "" else None,
                value_text=value_text if value_text != "" else None,
            )
        )
        count += 1

    db.commit()
    return count


def init_and_seed() -> int:
    """Create tables (if needed) and seed from processed artifacts."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        return seed(db)
