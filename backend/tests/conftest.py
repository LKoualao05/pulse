"""Shared pytest fixtures: an isolated in-memory DB and a configured client."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Base, Indicator, Observation, Source


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared in-memory connection
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def Session(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def db(Session):
    session = Session()
    try:
        yield session
    finally:
        session.close()


def seed_sample(session) -> None:
    session.add_all(
        [
            Source(
                key="who_gho", name="WHO GHO", url="https://who.int",
                license="CC BY-NC-SA 3.0 IGO", license_url="https://cc/by-nc-sa",
                attribution="WHO", accessed_at="2026-06-14", notes="non-commercial",
            ),
            Source(
                key="owid", name="Our World in Data", url="https://ourworldindata.org",
                license="CC BY 4.0", license_url="https://cc/by", attribution="OWID",
                accessed_at="2026-06-14", notes="",
            ),
        ]
    )
    session.add_all(
        [
            Indicator(
                key="suicide_rate", source_key="who_gho",
                name="Suicide mortality rate", unit="per 100,000 population",
                category="outcome", description="d", value_type="numeric",
            ),
            Indicator(
                key="mh_policy", source_key="owid",
                name="Stand-alone MH policy", unit="status",
                category="governance", description="d", value_type="categorical",
            ),
        ]
    )
    session.flush()
    session.add_all(
        [
            Observation(indicator_key="suicide_rate", country_iso3="USA",
                        country_name="United States", year=2019, value=14.5),
            Observation(indicator_key="suicide_rate", country_iso3="USA",
                        country_name="United States", year=2020, value=14.0),
            Observation(indicator_key="suicide_rate", country_iso3="GBR",
                        country_name="United Kingdom", year=2019, value=7.0),
            Observation(indicator_key="mh_policy", country_iso3="USA",
                        country_name="United States", year=2020, value_text="Yes"),
        ]
    )
    session.commit()


@pytest.fixture
def client(engine, Session):
    seeder = Session()
    seed_sample(seeder)
    seeder.close()

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # Not used as a context manager, so the lifespan/seed hook does not run.
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
