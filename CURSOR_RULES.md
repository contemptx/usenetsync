# Cursor RulePack — Live Usenet, Full-Stack (Py/Rust/React/SQLite/Postgres)

## Non-negotiables
- All tests must hit **real Usenet**: `news.newshosting.com:563` with SSL.
- Use **pynntp** imported as `nntp`. **Block `nntplib`**.
- Live group: **`alt.binaries.test`**.
- Frontend↔Backend↔Usenet E2E must pass. No mocks, no skips.
- Zero warnings (treat as errors) in Python, Rust, React.
- CI/dev tests use PostgreSQL. SQLite only for local manual dev, never CI.
- If required env/infra missing → **fail** (never skip/simulate).

## Required Env (.env must exist)

```
NNTP_HOST=news.newshosting.com
NNTP_PORT=563
NNTP_USERNAME=contemptx
NNTP_PASSWORD=REPLACE_ME_LOCALLY # never commit
NNTP_SSL=true
NNTP_GROUP=alt.binaries.test
NNTP_TIMEOUT_SECS=30
NNTP_CONNECT_RETRY=3
NNTP_READ_CHUNK_SIZE=65536
NNTP_USER_AGENT=YourTool/1.0 (+contact)

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
APP_ENV=live

DATABASE_URL=postgresql://app:app@localhost:5432/app
SQLITE_PATH=./data/app.db # not used in CI

FRONTEND_BASE_URL=http://localhost:5173

VITE_BACKEND_URL=http://localhost:8000

# Production NNTP client import path (module:Class) — update to your real one
PRODUCTION_NNTP_CLIENT_IMPORT=your_project.usenet.client:NNTPClient
```

## Make Commands (must pass)
- `make live` runs: Postgres up → migrations → Python lint/type/tests (incl. live) → Rust lint/tests → React typecheck/build → Playwright E2E.

## Usenet Must-Haves
- Enforce SSL:563 and `pynntp` (`import nntp`).
- Handle `CAPABILITIES`, reader mode, multi-line bodies, dot-stuffing.
- Backoff/retry, bounded streaming, respectful throttling, resume.

## Never Do
- Don't import `nntplib`.
- Don't mock or skip live NNTP tests.
- Don't use SQLite in CI.
- Don't mute/ignore warnings.
- Don't post binaries in automation.

## Final Check
- ✅ Zero warnings; ✅ Python/Rust/React checks green
- ✅ Unit/integration + live tests all pass
- ✅ E2E passes against live backend → live Usenet
- ✅ README updated; no TODO/FIXME; no secrets committed