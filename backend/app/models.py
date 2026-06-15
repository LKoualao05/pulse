"""SQLAlchemy ORM models.

The schema is deliberately tiny and stores **only aggregate, country-level
observations** — never individual-level data. Each observation is keyed by
(indicator, ISO-3 country, year).
"""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Source(Base):
    """A data provider, with its licensing recorded for provenance."""

    __tablename__ = "sources"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(500))
    license: Mapped[str] = mapped_column(String(120))
    license_url: Mapped[str] = mapped_column(String(500))
    attribution: Mapped[str] = mapped_column(String(500))
    accessed_at: Mapped[str] = mapped_column(String(30))  # ISO date of last fetch
    notes: Mapped[str] = mapped_column(String(500), default="")

    indicators: Mapped[list["Indicator"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Indicator(Base):
    """A single measurable series (e.g. age-standardized suicide rate)."""

    __tablename__ = "indicators"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    source_key: Mapped[str] = mapped_column(ForeignKey("sources.key"), index=True)
    name: Mapped[str] = mapped_column(String(300))
    unit: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40))  # burden|outcome|capacity|context|governance
    description: Mapped[str] = mapped_column(String(1000), default="")
    value_type: Mapped[str] = mapped_column(String(20), default="numeric")  # numeric|categorical

    source: Mapped[Source] = relationship(back_populates="indicators")
    observations: Mapped[list["Observation"]] = relationship(
        back_populates="indicator", cascade="all, delete-orphan"
    )


class Observation(Base):
    """One aggregate value for an indicator, country and year."""

    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint(
            "indicator_key", "country_iso3", "year", name="uq_obs_indicator_country_year"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_key: Mapped[str] = mapped_column(
        ForeignKey("indicators.key"), index=True
    )
    country_iso3: Mapped[str] = mapped_column(String(3), index=True)
    country_name: Mapped[str] = mapped_column(String(120))
    year: Mapped[int] = mapped_column(Integer, index=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(200), nullable=True)

    indicator: Mapped[Indicator] = relationship(back_populates="observations")
