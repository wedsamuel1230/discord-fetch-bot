# Master Plan — Discord Daily Tech Bot

## Milestones
1. [x] Planning and research (v0.1.0)
2. [x] Plan updated for OpenRouter + RSS feeds (v0.2.0)
3. [x] Project scaffold and Docker setup (Phase A: T1, T9)
4. [x] twscrape integration and tweet fetching (Phase B: T2, T3)
5. [x] RSS feed fetching with feedparser (Phase B: T3b)
6. [x] OpenRouter AI filtering with model fallback (Phase C: T4)
7. [x] Discord embed builder and webhook sender (Phase D: T5, T6)
8. [x] Orchestrator, scheduler, error handling (Phase E: T7, T8, T10)
9. [x] Integration testing and validation (Phase F: T11)
10. [x] X-ingestion resilience fix: Nitter fallback + null-safe AI parsing (v1.1.0)
11. [x] User fix-list patch: RSS URL update, RP merge, model order, logging noise suppression (v1.2.0)
12. [x] Follow-builders hybrid migration kickoff: config toggles + feed adapter + orchestrator wiring + regression coverage (v1.4.0)
13. [x] Legacy X removal + Maker feed redistribution + RSS expansion (v1.5.0)
14. [x] AI builder section now remixed to Traditional Chinese via OpenRouter path (v1.5.1)
15. [x] Per-category Xer catalogs (>=10 each) + topic-X/RSS merge + 10-item digest targeting (v1.6.0)
16. [x] Init-webhook fallback + follow-builders mirror failover + cache fallback hardening (v1.6.1)
17. [x] Staged source expansion (wave1/wave2 overlays), YouTube channel ingestion, and Discord message refactor (v1.7.0)

## Upcoming Work

- [ ] Deploy `DIGEST_MODE=follow-builders-hybrid` to HAOS and validate 2-3 scheduled digests
- [ ] Add deterministic source pinning runbook (`FOLLOW_BUILDERS_SOURCE_MODE=pinned` + ref management)
- [ ] Complete Wave-1 digest quality observation and tune noisy overlay sources
- [ ] Decide Wave-2 enablement threshold and rollout date (`SOURCE_ROLLOUT_MODE=wave2`)
- [ ] Add Windows one-command deployment helper script for upload/build/restart
- [ ] Validate topic-X + RSS blended category quality (ESP32/RP2040/Arduino/3D) over 2-3 runs
- [ ] Tune and pin stable `TOPIC_X_RSS_BASE_URLS` mirror order for HAOS production
- [ ] Tune and pin stable `FOLLOW_BUILDERS_BASE_URLS` order for HAOS production

## Completed

- [x] Implementation plan created (2026-03-04)
- [x] Plan updated: Perplexity → OpenRouter, added RSS feeds (2026-03-04)
- [x] Full implementation completed (v1.0.0)
- [x] X fallback reliability patch completed (v1.1.0)
- [x] Follow-builders hybrid implementation started (v1.4.0)
- [x] Legacy X path retired and Maker category removed (v1.5.0)
- [x] AI builder section switched to Traditional Chinese remix path (v1.5.1)
- [x] Category-X integration and 10-item digest target implementation (v1.6.0)
- [x] Init fallback + follow-builders mirror/cache resilience implementation (v1.6.1)
- [x] Wave rollout overlays + YouTube ingestion + Discord message refactor (v1.7.0)

## Target Versions

- v0.1.0 — Planning complete
- v0.2.0 — Plan updated (OpenRouter + RSS)
- v1.0.0 — End-to-end daily bot operational
- v1.1.0 — X retrieval hardened with Nitter fallback + null-safe AI parse
- v1.4.0 — Hybrid mode enabled (follow-builders AI + maker RSS)
- v1.5.0 — Legacy X path retired, Maker feeds redistributed, RSS catalog expanded
- v1.5.1 — Full digest (including AI builder section) rendered in Traditional Chinese path
- v1.6.0 — >=10 Xers per category, topic-X/RSS blending, and 10-item-per-category digest target
- v1.6.1 — Optional init-webhook fallback, follow-builders mirror failover, and cache fallback
- v1.7.0 — Staged source expansion (`wave1`/`wave2`), topic YouTube ingestion, and deterministic Discord formatting refactor

---
Last Updated: 2026-04-10
