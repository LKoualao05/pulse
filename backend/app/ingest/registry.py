"""Catalog of data sources and indicators — the single source of truth.

Every indicator declares which provider it comes from and the provider-specific
code/parameters needed to fetch it. Licensing is recorded per source so it can
be surfaced in the API and UI (WHO data is non-commercial; World Bank and the
OWID-served WHO data are CC BY).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SourceSpec:
    key: str
    name: str
    url: str
    license: str
    license_url: str
    attribution: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    key: str  # our stable slug
    source_key: str
    name: str
    unit: str
    category: str  # burden|outcome|capacity|context|governance
    provider_code: str  # WHO indicator code / WB code / OWID slug
    description: str = ""
    value_type: str = "numeric"  # numeric|categorical
    extra: dict = field(default_factory=dict)


SOURCES: dict[str, SourceSpec] = {
    "who_gho": SourceSpec(
        key="who_gho",
        name="WHO Global Health Observatory (GHO)",
        url="https://www.who.int/data/gho/info/gho-odata-api",
        license="CC BY-NC-SA 3.0 IGO",
        license_url="https://creativecommons.org/licenses/by-nc-sa/3.0/igo/",
        attribution="World Health Organization, Global Health Observatory.",
        notes=(
            "Non-commercial reuse with attribution and share-alike. Must not be "
            "used to imply WHO endorsement of any product or organization."
        ),
    ),
    "world_bank": SourceSpec(
        key="world_bank",
        name="World Bank Open Data (Indicators API)",
        url="https://datahelpdesk.worldbank.org/knowledgebase/articles/889392",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution="The World Bank: World Development Indicators.",
        notes="Free reuse (incl. commercial) with attribution.",
    ),
    "owid": SourceSpec(
        key="owid",
        name="Our World in Data",
        url="https://ourworldindata.org/mental-health",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution=(
            "Our World in Data, based on WHO Mental Health Atlas. "
            "Only redistributable (non-IHME) series are used."
        ),
        notes=(
            "OWID's IHME-derived prevalence series are explicitly "
            "non-redistributable and are deliberately NOT ingested."
        ),
    ),
}


INDICATORS: list[IndicatorSpec] = [
    # --- WHO GHO (CC BY-NC-SA 3.0 IGO) ---
    IndicatorSpec(
        key="suicide_rate",
        source_key="who_gho",
        name="Suicide mortality rate (age-standardized)",
        unit="per 100,000 population",
        category="outcome",
        provider_code="MH_12",
        description=(
            "Age-standardized suicide deaths per 100,000 people, both sexes. "
            "A core mental-health outcome indicator."
        ),
        extra={"who_dims": {"Dim1": "SEX_BTSX"}},
    ),
    IndicatorSpec(
        key="psychiatrists",
        source_key="who_gho",
        name="Psychiatrists working in the mental-health sector",
        unit="per 100,000 population",
        category="capacity",
        provider_code="MH_6",
        description="Density of psychiatrists — a proxy for mental-health system capacity.",
    ),
    IndicatorSpec(
        key="depression_prevalence",
        source_key="who_gho",
        name="Estimated prevalence of depression",
        unit="% of population",
        category="burden",
        provider_code="GDO_q35",
        description=(
            "WHO estimated population-based prevalence of depression. "
            "Note: a single-year (2015) cross-sectional snapshot, not a time series."
        ),
    ),
    # --- World Bank (CC BY 4.0) ---
    IndicatorSpec(
        key="health_expenditure_pc",
        source_key="world_bank",
        name="Current health expenditure per capita",
        unit="current US$",
        category="context",
        provider_code="SH.XPD.CHEX.PC.CD",
        description="Total health spending per person — system-investment context.",
    ),
    IndicatorSpec(
        key="unemployment",
        source_key="world_bank",
        name="Unemployment rate",
        unit="% of total labor force",
        category="context",
        provider_code="SL.UEM.TOTL.ZS",
        description="Modeled ILO estimate — a socioeconomic stressor often linked to well-being.",
    ),
    IndicatorSpec(
        key="gdp_per_capita",
        source_key="world_bank",
        name="GDP per capita",
        unit="current US$",
        category="context",
        provider_code="NY.GDP.PCAP.CD",
        description="Economic output per person — broad prosperity context.",
    ),
    IndicatorSpec(
        key="life_expectancy",
        source_key="world_bank",
        name="Life expectancy at birth",
        unit="years",
        category="context",
        provider_code="SP.DYN.LE00.IN",
        description="Overall population health context.",
    ),
    # --- OWID (CC BY 4.0; WHO-sourced, redistributable) ---
    IndicatorSpec(
        key="mh_policy",
        source_key="owid",
        name="Stand-alone mental-health policy or plan",
        unit="status",
        category="governance",
        provider_code="stand-alone-policy-or-plan-for-mental-health",
        value_type="categorical",
        description=(
            "Whether a country reports a stand-alone mental-health policy or plan "
            "(WHO Mental Health Atlas, served by Our World in Data)."
        ),
        extra={"owid_column": "stand_alone_policy_or_plan_for_mental_health"},
    ),
]


def indicators_for(source_key: str) -> list[IndicatorSpec]:
    return [spec for spec in INDICATORS if spec.source_key == source_key]
