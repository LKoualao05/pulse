"""Guardrail tests encoding the project's non-negotiable data rules.

These fail loudly if someone later adds a non-redistributable or individual-level
source to the registry.
"""

from __future__ import annotations

from app.ingest.registry import INDICATORS, SOURCES


def test_no_ihme_or_nonredistributable_slugs():
    # OWID's IHME prevalence series are non-redistributable and must never appear.
    for spec in INDICATORS:
        code = spec.provider_code.lower()
        assert "ihme" not in code, f"IHME-derived source not allowed: {spec.key}"
        assert "prevalence-ihme" not in code


def test_every_indicator_has_a_licensed_source():
    for spec in INDICATORS:
        assert spec.source_key in SOURCES, spec.key
        src = SOURCES[spec.source_key]
        assert src.license, f"missing license for {src.key}"
        assert src.license_url.startswith("http")
        assert src.attribution


def test_owid_source_documents_the_exclusion():
    # The reason IHME is excluded is recorded for provenance.
    assert "non-redistributable" in SOURCES["owid"].notes.lower()
