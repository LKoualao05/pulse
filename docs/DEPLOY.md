# Deployment Guide

Pulse deploys on free tiers: the **FastAPI backend on [Render](https://render.com)**
and the **React frontend on [Vercel](https://vercel.com)**. Both read from the
GitHub repo, so once pushed, deployment is a few clicks.

> These steps require your own Render and Vercel accounts — they can't be done
> headlessly. The repo already contains everything needed (`render.yaml`,
> `frontend/vercel.json`); you just connect the repo and set two env vars.

---

## 1. Backend → Render

1. Push this repo to GitHub.
2. In Render: **New + → Blueprint**, select the repo. Render reads
   [`render.yaml`](../render.yaml) and provisions a free web service named
   `pulse-api` with:
   - root dir `backend`, build `pip install -r requirements.txt`
   - start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - health check `/api/health`
3. Set environment variables (marked `sync: false` in the blueprint):
   - `PULSE_CORS_ORIGINS` → your Vercel URL (e.g. `https://pulse-xyz.vercel.app`).
     You'll know this after step 2 below — come back and set it, then redeploy.
   - `ANTHROPIC_API_KEY` → *(optional)* enables the Claude explainer. Without it
     the app still works (templated fallback).
4. Deploy. Note the API URL, e.g. `https://pulse-api.onrender.com`.

**Notes**
- The free tier spins down when idle; the first request after a sleep takes
  ~30–60s (cold start). Fine for a portfolio demo.
- The SQLite database is rebuilt from the committed `backend/data/processed/*.csv`
  on each startup — no persistent disk required. To use Postgres instead, set
  `PULSE_DATABASE_URL` to a `postgresql://` URL (the code is already
  Postgres-ready).

---

## 2. Frontend → Vercel

1. In Vercel: **Add New → Project**, import the repo.
2. Set **Root Directory** to `frontend`. Vercel auto-detects Vite via
   [`frontend/vercel.json`](../frontend/vercel.json) (build `npm run build`,
   output `dist`, SPA rewrites).
3. Add an environment variable:
   - `VITE_API_BASE` → your Render API URL from step 1 (e.g.
     `https://pulse-api.onrender.com`).
4. Deploy. Note the URL, e.g. `https://pulse-xyz.vercel.app`.
5. **Go back to Render** and set `PULSE_CORS_ORIGINS` to that Vercel URL, then
   redeploy the API so the browser is allowed to call it.

---

## 3. Verify

- `https://<your-api>.onrender.com/api/health` → `{"status":"ok", ...}`
- Open the Vercel URL → the dashboard loads charts from the live API.
- The daily GitHub Action (`.github/workflows/daily-refresh.yml`) keeps the
  committed data fresh; Render redeploys on each push, so the live site picks up
  new data automatically.

---

## Alternative hosts

- **Backend:** [Fly.io](https://fly.io) (always-on small VM, no cold starts) or
  [Railway](https://railway.app). Use the same start command.
- **Frontend:** [Netlify](https://netlify.com) or GitHub Pages (set
  `VITE_API_BASE` at build time; add an SPA redirect).
