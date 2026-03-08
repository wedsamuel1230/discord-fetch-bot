# Active Context

## Current Focus
Post-implementation stabilization (v1.3.0): validate X discovery coverage, startup notifications, and safe self-update behavior.

## Latest Delta (v1.3.0)

- Removed `twscrape` and Nitter fallback entirely.
- Replaced X ingestion with x-tweet-fetcher-style discovery:
  - DuckDuckGo search for public X status URLs
  - FxTwitter public API hydration for full tweet text/metrics
- Added `DISCORD_INIT_WEBHOOK_URL` for boot and self-update notices.
- Added safe daily git self-update with clean-working-tree guard and fast-forward only pulls.
- Added Docker git dependency and graceful fallback when `git` is unavailable.
- Deployment note: uploading source files alone is insufficient on HAOS; the `discord-bot` image must be rebuilt after code or Dockerfile changes.
- Digest formatting now compacts AI output into short one-line Traditional Chinese bullets in a "why it matters" style before sending to Discord.
- Expanded RSS catalog with higher-signal sources:
  - OpenAI News, Hugging Face Blog, Google AI Blog
  - Arduino Blog, Raspberry Pi News
  - Prusa Blog, 3D Printing Industry, VoxelMatters, 3Dnatives

## Status

- ✅ T1  Project scaffold (requirements.txt, Dockerfile, docker-compose.yml, .env.example, .gitignore, data/)
- ✅ T2  Public X discovery without login
- ✅ T3  FxTwitter hydration + fallback snippet extraction
- ✅ T3b RSS fetching (expanded catalog, concurrent httpx + feedparser)
- ✅ T4  OpenRouter AI filtering (StepFun Step 3.5 Flash → Arcee Trinity Large Preview)
- ✅ T5  Discord embed builder (6000-char enforcement)
- ✅ T6  Discord webhook sender (429 retry)
- ✅ T7  Orchestrator (RSS + X merge, per-topic error isolation)
- ✅ T8  Scheduler (APScheduler AsyncIOScheduler, 13:30 HKT)
- ✅ T9  Dockerfile + docker-compose.yml
- ✅ T10 Logging + env var validation + startup checks
- ✅ T11 Validation checklist in README + plan
- ✅ Init channel notification on startup
- ✅ Daily self-update check (git fetch/ff-only pull/restart)
- ✅ AI parsing fix: handles null OpenRouter content safely (prevents `'NoneType' has no attribute 'strip'`)

## Next Steps

1. Copy `.env.example` → `.env` and fill in the webhook/API values
2. **Verify** OpenRouter fallback model IDs at <https://openrouter.ai/models>:
   - `stepfun-ai/step-3.5-flash` and `arcee-ai/arcee-trinity-large-preview`
   - Update `OPENROUTER_MODELS` in `main.py` if IDs differ
3. `docker-compose up -d` and watch logs
4. `docker-compose up -d --build` and watch logs
5. Confirm init webhook receives boot message
6. Confirm X posts appear from discovery + FxTwitter hydration path
7. Confirm 6 embeds appear in Discord channel
8. Confirm self-update skips when repo is dirty and fast-forwards when clean

## Notes

- Plan: `memory-bank/plans/2026-03-04-discord-daily-tech-bot.md`
- Single file: `main.py` (~600 lines)
- APScheduler 3.x chosen (4.x alpha has incompatible API)
- Consider $5 OpenRouter credits for ~200 req/day margin vs ~20 free
- Root cause observed: logged-in X scraping path was brittle and produced missing-post gaps in production.
- Current mitigation: public discovery + hydration avoids account/session management entirely.
- Self-update intentionally refuses to pull over a dirty working tree.
- HAOS deploy flow uses `docker run` with only `/app/data` mounted, so app changes require `docker build -t discord-bot .` on the host before restart.
- Digest embed descriptions now normalize wrapped AI output into compact single-line bullets and preserve URLs.

Last Updated: 2026-03-08
