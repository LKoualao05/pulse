# Pulse — a Mental-Health & Well-Being Data Observatory

**Pulse** is a full-stack, deployed web application that ingests **public,
aggregate, openly-licensed** mental-health and well-being datasets, processes
them through a typed Python pipeline, and presents them through an interactive
dashboard with a small Claude-powered "Explain this chart" feature.

It's built as a *public-health observatory* — not a social-media scraper. Every
figure is aggregate, country-level, traceable to its source, and shown alongside
its license. Pages with distressing statistics always display crisis-resource
information.

> **Why I built it.** I'm a data-science student who built an NLP pipeline at a
> medical center analyzing mental-health discourse. Pulse is my attempt to make
> well-being data legible to ordinary people and to the small nonprofits that
> serve them — with honesty about data provenance and licensing as a first-class
> concern.

---

## Screenshots

> _Run the app locally (below) to see it live. To embed images here, drop
> `dashboard.png` and `about.png` into `docs/` — see [`docs/README.md`](docs/README.md)._

![Pulse dashboard](docs/dashboard.png)
![About & sources](docs/about.png)

The dashboard: eight indicator stat cards, an indicator + country picker, an
adaptive chart (multi-year line / single-year bar / categorical table), a
plain-language "Explain this chart" panel, and a per-chart source-and-license
badge. A crisis-resources footer is present on every page.

---

## What it does (mapped to the build checklist)

1. **A script that cleans / merges / analyzes data** → the ingestion + transform
   pipeline (`backend/app/ingest/`, `backend/app/transform/`).
2. **A dashboard / data visualization** → the React + Recharts frontend.
3. **A web app** → the deployed FastAPI API + React SPA.
4. **A workflow connecting two tools** → scheduled GitHub Action → fetch → DB → live site.
5. **Something that uses an API** → WHO GHO, World Bank, and OWID data APIs.
6. **A tool that uses an LLM** → the Claude-powered "Explain this chart" endpoint.

---

## Data sources

| Pillar | Indicator(s) | Source | License |
|---|---|---|---|
| Outcome | Suicide mortality rate (age-standardized) | WHO GHO | CC BY-NC-SA 3.0 IGO |
| Burden | Estimated prevalence of depression (2015 snapshot) | WHO GHO | CC BY-NC-SA 3.0 IGO |
| Capacity | Psychiatrists per 100k | WHO GHO | CC BY-NC-SA 3.0 IGO |
| Context | Health expenditure, unemployment, GDP, life expectancy | World Bank | CC BY 4.0 |
| Governance | Stand-alone mental-health policy | OWID (WHO-sourced) | CC BY 4.0 |

Full provenance, endpoints, access dates, and the **deliberate exclusion of
OWID's non-redistributable IHME prevalence data** are documented in
[`DATA_SOURCES.md`](DATA_SOURCES.md). Because WHO data is non-commercial, the
project as a whole is non-commercial and educational.

---

## Architecture

```
            Daily GitHub Action (cron)
                      │  runs pytest, then re-fetches
                      ▼
  WHO GHO ┐
  World Bank ├─► ingest/ ─► transform/ (ISO-3 normalize, dedup)
  OWID ┘                         │
                                 ▼
                 backend/data/processed/*.csv + summary.json
                  (committed only if the data actually changed)
                                 │  seed-on-startup
                                 ▼
   FastAPI ──  SQLite (local) / Postgres-ready  ──  parameterized queries
     │  /api/health · /sources · /summary · /indicators · /series · /explain
     │  CORS-locked · rate-limited · Pydantic-validated
     ▼
   React + Vite + TS + Recharts dashboard
     charts · ExplainPanel (Claude) · SourceBadge · CrisisFooter
```

**Key design choice:** the API seeds its database from the committed
`data/processed` CSVs on startup, so serving never depends on a live upstream
API call. The daily Action refreshes those CSVs; the deployed site reads them.

### Repository layout

```
pulse/
├── backend/
│   ├── app/
│   │   ├── config.py            # env-only settings (pydantic-settings)
│   │   ├── db.py · models.py · schemas.py · crud.py · seed.py
│   │   ├── ingest/              # base · http · registry · who_gho · world_bank · owid · run
│   │   ├── transform/normalize.py   # pycountry ISO-3 validation
│   │   ├── services/explain.py  # Claude "Explain this chart"
│   │   └── api/routers/         # meta · indicators · explain
│   ├── data/processed/          # committed CSVs + summary.json (the daily Action updates these)
│   ├── tests/                   # pytest: ingest (mocked) · transform · API · explain · ethics guard
│   └── requirements*.txt        # pinned, pip-audit-clean
├── frontend/                    # Vite + React + TS + Recharts
├── .github/workflows/           # ci.yml · daily-refresh.yml
├── DATA_SOURCES.md · SECURITY.md · LICENSE
```

---

## Running locally

### Prerequisites
- Python 3.11+ and Node.js 18+

### Backend
```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# Fetch the live datasets and build data/processed/* (optional — sample data is committed)
.venv/bin/python -m app.ingest.run

# Run the test suite
.venv/bin/python -m pytest            # ~36 tests

# Start the API  → http://127.0.0.1:8000/docs
.venv/bin/uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                            # → http://localhost:5173
```
In dev, Vite proxies `/api` → `http://127.0.0.1:8000`, so no CORS setup is
needed. For the Claude feature, copy `backend/.env.example` to `backend/.env`
and set `ANTHROPIC_API_KEY` (the app works without it — it falls back to a
templated summary).

---

## The "Explain this chart" feature (Claude)

`POST /api/explain` builds a compact, **numeric** prompt from the selected
series (first/last/change per country — never a raw data dump) and asks Claude
(`claude-haiku-4-5` by default) to summarize the trend for a non-expert. The key
is read only from `ANTHROPIC_API_KEY`. If the key is absent or the call fails,
the endpoint returns a deterministic templated summary flagged
`generated_by: "fallback"`, so the UI is always honest about what produced the text.

---

## Tests, security & quality

- **~36 pytest tests** (~90% coverage) over ingestion (mocked HTTP), ISO-3
  normalization, the API, the explain service (mocked Anthropic SDK), seeding,
  and an **ethics-guard test** that fails the build if a non-redistributable /
  IHME source is ever added.
- **`pip-audit` clean** — all dependencies pinned to patched versions.
- **Secrets** via environment variables only; CORS locked; rate-limited;
  parameterized SQL. See [`SECURITY.md`](SECURITY.md).

---

## Deployment & automation

- **Suggested free-tier hosting:** FastAPI on [Render](https://render.com)
  (free web service), React on [Vercel](https://vercel.com). See
  [`docs/DEPLOY.md`](docs/DEPLOY.md).
- **Daily data refresh:** `.github/workflows/daily-refresh.yml` runs on a
  schedule, runs the tests first, re-ingests the datasets, and **commits the
  refreshed `data/` artifacts only if they changed** — never touching source
  code, never making empty/noise commits.

---

## License

Application **code** is licensed under the [MIT License](LICENSE).
The **data** remains under each provider's license (see `DATA_SOURCES.md`);
because WHO GHO data is CC BY-NC-SA 3.0 IGO, the project is **non-commercial and
educational**.

---

## Crisis resources

If you or someone you know is struggling: in the US, call or text **988**
(Suicide & Crisis Lifeline). Internationally, find a helpline at
[findahelpline.com](https://findahelpline.com).
