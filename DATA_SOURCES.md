# Data Sources & Provenance

Pulse uses **only aggregate, country-level, publicly available and openly
licensed** data. It never ingests, stores, or displays individual-level data,
personal posts, names, or identifiable crisis content.

Each indicator below records its source, the exact API/endpoint used, the
license, and the access date. The live values, license, and attribution are also
served by the API at `GET /api/sources` and shown beneath every chart in the UI.

> **Access date for the figures currently committed in `backend/data/processed/`:
> 2026-06-14.** The daily GitHub Action re-fetches and updates these files (and
> the `accessed_at` field) whenever the upstream data changes.

---

## 1. WHO Global Health Observatory (GHO)

- **Provider:** World Health Organization — Global Health Observatory
- **API:** OData API — `https://ghoapi.azureedge.net/api/{IndicatorCode}`
- **Docs:** https://www.who.int/data/gho/info/gho-odata-api
- **License:** **CC BY-NC-SA 3.0 IGO** — https://creativecommons.org/licenses/by-nc-sa/3.0/igo/
- **Attribution:** *World Health Organization, Global Health Observatory.*
- **Terms note:** Non-commercial reuse with attribution and share-alike. WHO
  material must not be used to imply WHO endorsement of any product or
  organization. **Because of the non-commercial clause, Pulse is a
  non-commercial project.**

| Pulse indicator | GHO code | Notes |
|---|---|---|
| Suicide mortality rate (age-standardized) | `MH_12` | Both sexes (`SEX_BTSX`), country-level. Time series. |
| Psychiatrists in the mental-health sector | `MH_6` | Per 100,000 population. |
| Estimated prevalence of depression | `GDO_q35` | **Single-year (2015) snapshot**, not a time series — labelled as such in the UI. |

We query only `SpatialDimType eq 'COUNTRY'` rows and keep "total" breakdowns
(both sexes / all ages), discarding sex/age sub-rows.

---

## 2. World Bank Open Data (World Development Indicators)

- **Provider:** The World Bank
- **API:** Indicators API — `https://api.worldbank.org/v2/country/all/indicator/{code}?format=json`
- **Docs:** https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- **License:** **CC BY 4.0** — https://creativecommons.org/licenses/by/4.0/
- **Attribution:** *The World Bank: World Development Indicators.*
- **Terms note:** Free reuse (including commercial) with attribution. A small
  number of third-party indicators carry separate terms; Pulse uses only
  first-party WDI series.

| Pulse indicator | World Bank code |
|---|---|
| Current health expenditure per capita (US$) | `SH.XPD.CHEX.PC.CD` |
| Unemployment rate (% of labor force) | `SL.UEM.TOTL.ZS` |
| GDP per capita (US$) | `NY.GDP.PCAP.CD` |
| Life expectancy at birth (years) | `SP.DYN.LE00.IN` |

---

## 3. Our World in Data (OWID)

- **Provider:** Our World in Data
- **Endpoint:** Grapher CSV — `https://ourworldindata.org/grapher/{slug}.csv?csvType=full&useColumnShortNames=true`
- **Topic page:** https://ourworldindata.org/mental-health
- **License:** **CC BY 4.0** — https://creativecommons.org/licenses/by/4.0/ (for OWID's own processing)
- **Attribution:** *Our World in Data, based on the WHO Mental Health Atlas.*

| Pulse indicator | OWID slug |
|---|---|
| Stand-alone mental-health policy or plan | `stand-alone-policy-or-plan-for-mental-health` |

### ⚠️ Deliberate exclusion — IHME prevalence data is NOT redistributable

OWID's mental-health **prevalence** series (depression/anxiety, sourced from the
IHME Global Burden of Disease study) are explicitly **non-redistributable**.
Requesting their CSV returns:

```
HTTP 403 — "This chart contains non-redistributable data that we are not
allowed to re-share and it therefore cannot be downloaded as a CSV."
```

Pulse **does not ingest, cache, or display these series.** This is enforced in
code: `app/ingest/registry.py` contains no IHME slug, and
`tests/test_ethics_guard.py` fails the build if one is ever added. The
"burden" pillar uses WHO's own depression estimate (`GDO_q35`) instead.

---

## Licensing summary

| Source | License | Commercial use? |
|---|---|---|
| WHO GHO | CC BY-NC-SA 3.0 IGO | ❌ Non-commercial only |
| World Bank | CC BY 4.0 | ✅ |
| OWID (WHO-sourced) | CC BY 4.0 | ✅ |

Because WHO GHO data is non-commercial, **the Pulse project as a whole is
non-commercial and educational.** The application *code* is MIT-licensed; the
*data* remains under each source's license, tagged per-source in the database
and surfaced per-chart in the UI.
