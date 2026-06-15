# Security Policy

Pulse is a small, data-first public-health observatory. It serves only public,
aggregate data and holds no user accounts or personal data — but it still
follows defensive defaults throughout.

## Reporting a vulnerability

If you find a security issue, please **do not open a public issue**. Email the
maintainer (see the GitHub profile) with details and steps to reproduce. You'll
get an acknowledgement within a few days.

## Secrets

- The only secret is the **Anthropic API key**, read **exclusively** from the
  `ANTHROPIC_API_KEY` environment variable (see `backend/app/config.py`).
- No secret is ever hardcoded or committed. `.env` is git-ignored; only
  `.env.example` (with empty values) is tracked.
- The app runs fine **without** the key — the "Explain this chart" endpoint
  falls back to a deterministic, non-AI summary.

## Application hardening

| Area | Measure |
|---|---|
| **Input validation** | All request inputs are validated with Pydantic; country codes are checked against ISO-3 (length + alpha) and capped at 12 per request. |
| **SQL injection** | All database access uses SQLAlchemy's parameterized query builder — no string-formatted SQL anywhere (`app/crud.py`). |
| **CORS** | Restricted to the configured frontend origin(s) via `PULSE_CORS_ORIGINS`; only `GET`/`POST` allowed. |
| **Rate limiting** | A per-client rate limit (`slowapi`, default `60/minute`) is applied to every route by middleware, throttling abuse and the Anthropic-backed endpoint. |
| **No individual data** | By design the schema stores only aggregate country/year rows; there is no PII to leak. |
| **LLM prompt** | The explain endpoint sends only pre-computed numeric facts to Claude — never raw user input echoed into a shell, query, or filesystem. |

## Dependencies

- All runtime and dev dependencies are **pinned** (`backend/requirements*.txt`).
- The project is scanned with [`pip-audit`](https://pypi.org/project/pip-audit/):

  ```bash
  cd backend && .venv/bin/pip-audit
  # → No known vulnerabilities found
  ```

- A secret scan (pattern-based) is run before each push; no secrets are present
  in the repository.
- Dependency and secret checks also run in CI (`.github/workflows/ci.yml`).

## Data integrity

- The deployed app rebuilds its database from the committed
  `backend/data/processed/*.csv` artifacts on startup — there is no writable
  user-facing data path.
- The daily refresh GitHub Action runs the test suite first and only commits
  data (never source code), and only when the data actually changed.
