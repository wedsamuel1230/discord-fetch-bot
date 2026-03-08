# Active Context

## Current Focus
Post-implementation stabilization (v1.1.0): address missing X posts in production logs.

## Latest Delta (v1.2.0)
- Applied user fix list:
   - RSS URL keys changed to requested values:
      - `thingiverse`: `https://www.thingiverse.com/newest/rss`
      - `printables`: `https://www.printables.com/feed.xml`
   - Merged RP2350 into RP2040 topic/query/keyword routing
   - OpenRouter model order fixed and added extra free fallback model
   - Suppressed verbose httpx request URL logs (`logging.getLogger("httpx").setLevel(logging.WARNING)`)
- Verification evidence:
   - Runtime test after rebuild confirms feed fallback works:
      - `printables_entries=1` (fallback to `https://blog.prusa3d.com/feed/`)
      - `thingiverse_entries=5` (fallback parse via `https://www.thingiverse.com/rss`)

## Status
- ✅ T1  Project scaffold (requirements.txt, Dockerfile, docker-compose.yml, .env.example, .gitignore, data/)
- ✅ T2  twscrape account setup
- ✅ T3  Tweet fetching with min_faves fallback
- ✅ T3b RSS fetching (11 feeds, concurrent httpx + feedparser)
- ✅ T4  OpenRouter AI filtering (StepFun Step 3.5 Flash → Arcee Trinity Large Preview)
- ✅ T5  Discord embed builder (6000-char enforcement)
- ✅ T6  Discord webhook sender (429 retry)
- ✅ T7  Orchestrator (RSS + X merge, per-topic error isolation)
- ✅ T8  Scheduler (APScheduler AsyncIOScheduler, 13:30 HKT)
- ✅ T9  Dockerfile + docker-compose.yml
- ✅ T10 Logging + env var validation + startup checks
- ✅ T11 Validation checklist in README + plan
- ✅ X-ingestion fix: twscrape active-account validation + Nitter RSS fallback when Cloudflare blocks login
- ✅ AI parsing fix: handles null OpenRouter content safely (prevents `'NoneType' has no attribute 'strip'`)

## Next Steps
1. Copy `.env.example` → `.env` and fill in all 6 values
2. **Verify** OpenRouter fallback model IDs at https://openrouter.ai/models:
   - `stepfun-ai/step-3.5-flash` and `arcee-ai/arcee-trinity-large-preview`
   - Update `OPENROUTER_MODELS` in `main.py` if IDs differ
3. `docker-compose up -d` and watch logs
4. `docker-compose up -d --build` and watch logs
5. Confirm X posts appear from either twscrape or Nitter fallback path
6. Confirm 7 embeds appear in Discord channel
7. If fallback still returns 0, set `NITTER_BASE_URLS` in `.env` to working mirrors and restart container

## Notes
- Plan: `memory-bank/plans/2026-03-04-discord-daily-tech-bot.md`
- Single file: `main.py` (~600 lines)
- APScheduler 3.x chosen (4.x alpha has incompatible API)
- Consider $5 OpenRouter credits for ~200 req/day margin vs ~20 free
- Root cause observed: twscrape login blocked by Cloudflare (`403`, no active accounts)
- Mitigation implemented: fallback to Nitter search RSS mirrors for X topic coverage
- Added optional env override: `NITTER_BASE_URLS` (comma-separated) for network-specific mirror routing

---
*Last Updated: 2026-03-04*
