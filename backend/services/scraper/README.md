---
title: SupremeAI Scraper
emoji: 🕷️
colorFrom: blue
colorTo: indigo
sdk: docker
dockerfile_path: Dockerfile
app_port: 8080
healthcheck: /health
---

# SupremeAI Scraper Microservice

Standalone browser-automation + web-scraping API, hosted **free** on Hugging Face
Spaces. The Space sleeps when idle and wakes on the first request — a true $0
cost scale-to-zero host (replacing the now paid-only Koyeb tier).

## Endpoints
- `GET /health` — liveness probe (`playwright_available: true` when chromium is ready)
- `POST /scrape` — fetch a URL, return cleaned text + links
- `POST /browse` — full Playwright automation (click / type / screenshot / fetch)
- `POST /recipe` — multi-step automation recipe

## How it's wired
The SupremeAI backend calls this service via `SCRAPER_SERVICE_URL` (set to this
Space's public URL on the Render dashboard). The backend also caches idempotent
`/scrape` + default `/browse` calls via Upstash, so a Space waking from sleep
only costs one cold start per cache miss.

## Build notes
- `Dockerfile` installs Playwright Chromium with system deps (`--with-deps`).
- Chromium launches with `--no-sandbox --disable-dev-shm-usage` (required in
  containerized / HF runtimes).
- Listens on `0.0.0.0:$PORT`; HF uses the image `ENV PORT=8080`, so `app_port`
  above matches the running server.
