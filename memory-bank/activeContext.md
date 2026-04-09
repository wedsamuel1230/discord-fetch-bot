# Active Context

## Current Focus

Wave-1 source expansion validation (v1.7.0): staged X + YouTube onboarding and Discord message refactor verification before optional Wave-2 enablement.

## Latest Delta (v1.7.0)

- Added staged source rollout controls:
  - `SOURCE_ROLLOUT_MODE=wave1|wave2` (default wave1) with topic overlays for additional X and YouTube seeds.
  - Runtime source expansion helpers: `_topic_runtime_x_handles()` and `_topic_runtime_youtube_channels()`.
- Added topic-level YouTube ingestion path:
  - New controls: `TOPIC_YOUTUBE_ENABLED`, `YOUTUBE_LOOKBACK_HOURS`, `YOUTUBE_MAX_ITEMS_PER_CHANNEL`.
  - New fetchers: `_resolve_youtube_channel_id()`, `_fetch_topic_youtube_channel_posts()`, `fetch_topic_youtube_posts()`.
  - Hybrid merge path now combines `topic-X + YouTube + RSS` for non-AI categories.
- Refactored Discord message composition pipeline:
  - Decomposed bullet compaction into `_split_summary_bullets()` + `_compact_bullet_for_discord()`.
  - Added centralized `DISCORD_RENDER_LIMITS` and deterministic topic ordering in `build_all_embeds()`.
  - Updated compact line format to `• body ｜ URL` for improved scanability.
- Added RED→GREEN regression coverage for:
  - source rollout wave behavior (`SourceRolloutTests`)
  - deterministic embed ordering and visual link separator (`DigestFormatTests`)
- Verification:
  - Focused RED captured before code (`SourceRolloutTests`, `DigestFormatTests` failed as expected)
  - Focused GREEN after implementation
  - Full suite GREEN: `python -m unittest tests.test_main -v` now 26/26

## Latest Delta (v1.6.1)

- Made init webhook optional in env validation:
  - `DISCORD_INIT_WEBHOOK_URL` now falls back to `DISCORD_WEBHOOK_URL` when missing/empty.
- Hardened follow-builders source retrieval:
  - Added `FOLLOW_BUILDERS_BASE_URLS` mirror list with ordered failover.
  - Feed fetch now tries candidate URLs per feed (`x`, `podcasts`, `blogs`) before failing.
- Added follow-builders cache fallback:
  - New controls: `FOLLOW_BUILDERS_CACHE_ENABLED`, `FOLLOW_BUILDERS_CACHE_TTL_HOURS`, `FOLLOW_BUILDERS_CACHE_PATH`.
  - When all upstream candidates fail and cache is fresh, bot uses cached normalized payload.
- Added AI source fallback behavior:
  - When follow-builders returns no AI posts, orchestrator fetches AI RSS sources and continues summary generation.
  - Expanded AI RSS fallback catalog with `reddit_openai` and `reddit_chatgpt`.
- Added and verified regression coverage for:
  - init fallback-to-main webhook behavior
  - missing-init env acceptance
  - follow-builders mirror failover
  - follow-builders cache fallback
- Verification:
  - Focused suite GREEN: 8/8 (`InitWebhookTests`, `MigrationConfigTests`, `FollowBuildersFeedTests`)
  - Full suite GREEN: 19/19 (`python -m unittest tests.test_main -v`)

## Latest Delta (v1.6.0)

- Added `x_handles` lists to every topic in `TOPICS` with at least 10 handles each.
  - AI list explicitly includes requested handles: `Khazix0918`, `dotey`, `vista8`.
- Added topic-X ingestion path via public RSS mirrors:
  - `fetch_topic_x_posts()` collects per-handle posts with mirror fallback.
  - New env controls: `TOPIC_X_ENABLED`, `TOPIC_X_LOOKBACK_HOURS`, `TOPIC_X_RSS_BASE_URLS`.
- Updated non-AI hybrid orchestrator path to merge `topic-X + RSS` before `ai_filter` summarization.
- Updated `ai_filter()` output contract to target `fetch_limit` items (default 10) instead of 3-5.
- Increased AI fallback/local summary defaults to align with 10-item target.
- Added regression tests enforcing per-category Xer minimums and required AI handles.
- Verification:
  - Focused RED: new topic distribution tests failed before implementation.
  - Focused GREEN: topic distribution tests passed after implementation.
  - Full suite GREEN: `python -m unittest tests.test_main -v` => 15 tests passing.

## Latest Delta (v1.5.0)

- Removed legacy X ingestion code entirely from `main.py`:
  - deleted DuckDuckGo/X discovery helpers and FxTwitter hydration path
  - deleted legacy digest mode support (`DIGEST_MODE=legacy` no longer accepted)
- Maker category removed from `TOPICS`; former Maker feeds redistributed to non-AI categories (ESP32/RP2040/Arduino/3D列印).
- Added additional RSS sources where feasible:
  - AI: `reddit_localllama`, `reddit_singularity`
  - Embedded: `reddit_microcontrollers`, `reddit_embedded`
  - 3D: `all3dp`, `reddit_additivemanufacturing`
- Updated AI section rendering to pass follow-builders items through `ai_filter`, ensuring Traditional Chinese digest output for the builder section as well.
- Updated orchestrator to remain follow-builders-first for AI and RSS-only for non-AI hybrid categories.
- Removed obsolete dependency `duckduckgo-search`.
- Updated regression suite to enforce:
  - legacy mode rejected
  - legacy X helper removal
  - Maker category removal + feed redistribution
  - expanded RSS catalog keys
- Verification: `python -m unittest tests.test_main -v` => 13 tests passing.

## Latest Delta (v1.4.0)

- Added migration toggles in runtime config/env:
  - `DIGEST_MODE`: `legacy`, `follow-builders-hybrid`, `follow-builders-only`
  - `FOLLOW_BUILDERS_SOURCE_MODE`: `central` or `pinned`
  - `FOLLOW_BUILDERS_PINNED_REF` required in pinned follow-builders mode
  - Optional feed URL overrides (`FOLLOW_BUILDERS_FEED_X_URL`, `FOLLOW_BUILDERS_FEED_PODCASTS_URL`, `FOLLOW_BUILDERS_FEED_BLOGS_URL`)
  - Maker controls (`MAKER_RSS_ENABLED`, `MAKER_RSS_TOPIC_SET`)
- Added follow-builders adapter pipeline:
  - `fetch_follow_builders_feeds()` normalizes upstream feed JSON and captures non-fatal errors
  - `build_ai_builder_summary()` renders concise linked AI-builder bullets
- Updated orchestrator (`run_daily_job`) to support hybrid and follow-builders-only modes.
- Preserved legacy mode for rollback safety (`DIGEST_MODE=legacy`).
- Updated `.env.example` and `README.md` for migration/cutover configuration.
- Expanded regression tests (11 passing) with migration behavior coverage.

## Prior Delta (v1.3.0)

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
- ✅ Migration toggle validation with pinned-source guard
- ✅ follow-builders feed intake and AI summary rendering
- ✅ Hybrid-mode orchestration path and Discord payload flow
- ✅ README/.env migration docs and settings table refresh
- ✅ Legacy X path fully removed from runtime
- ✅ Maker category removed and feed distribution applied
- ✅ Expanded RSS catalog for AI/embedded/3D categories
- ✅ Per-category Xer catalogs added (>=10 per category)
- ✅ Topic-X + RSS merge path for non-AI hybrid categories
- ✅ 10-item digest target wiring via topic `fetch_limit`
- ✅ Optional init webhook fallback to main webhook
- ✅ follow-builders multi-origin feed failover
- ✅ follow-builders cached fallback during transient upstream outages

## Next Steps

1. Set `.env` for migration run: `DIGEST_MODE=follow-builders-hybrid` and choose `FOLLOW_BUILDERS_SOURCE_MODE`
2. Run staged HAOS deployment and verify AI section quality for 2-3 scheduled digests
3. Confirm topic-X + RSS blended quality for ESP32/RP2040/Arduino/3D categories over 2-3 runs
4. Add deterministic source pinning runbook for production (`FOLLOW_BUILDERS_SOURCE_MODE=pinned`)
5. Tune `TOPIC_X_RSS_BASE_URLS` mirror order if any mirror becomes unstable in HAOS runtime
6. Tune `FOLLOW_BUILDERS_BASE_URLS` ordering for fastest stable origin in HAOS runtime

## Notes

- Plan: `memory-bank/plans/2026-03-04-discord-daily-tech-bot.md`
- Migration plan snapshot: `/memories/session/plan.md`
- Single file: `main.py` (~1700 lines)
- APScheduler 3.x chosen (4.x alpha has incompatible API)
- Consider $5 OpenRouter credits for ~200 req/day margin vs ~20 free
- Root cause observed: any direct X ingestion path increased fragility and maintenance burden.
- Current mitigation: centralized follow-builders AI feed + topic-X/RSS blended non-AI pipeline.
- Self-update intentionally refuses to pull over a dirty working tree.
- HAOS deploy flow uses `docker run` with only `/app/data` mounted, so app changes require `docker build -t discord-bot .` on the host before restart.
- Digest embed descriptions now normalize wrapped AI output into compact single-line bullets and preserve URLs.

Last Updated: 2026-03-31
