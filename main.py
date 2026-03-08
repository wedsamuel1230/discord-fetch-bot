#!/usr/bin/env python3
"""Discord Daily Tech Bot

Daily tech news digest from X (Twitter) and RSS feeds, filtered and
summarised into Traditional Chinese via OpenRouter AI, then delivered as
6 themed Discord embeds every afternoon at 13:30 HKT.

Architecture : single-file async Python app
Data sources : twscrape (X/Twitter) + feedparser (RSS, fetched via httpx)
AI           : OpenRouter free-tier models (OpenAI-compatible REST)
Delivery     : Discord webhook — single POST, all 7 embeds
Scheduler    : APScheduler AsyncIOScheduler + CronTrigger at 13:30 HKT

AI model fallback chain (verify IDs at https://openrouter.ai/models):
    1. stepfun/step-3.5-flash:free            (StepFun Step 3.5 Flash — primary)
    2. arcee-ai/trinity-large-preview:free    (Arcee Trinity Large Preview — fallback)
    3. meta-llama/llama-3.2-3b-instruct:free  (extra free fallback)
"""
from __future__ import annotations

import asyncio
import calendar
import html
import logging
import os
import re
import sys
import time
from urllib.parse import quote_plus
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import feedparser
import httpx
import pytz
import twscrape
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ─── Constants ────────────────────────────────────────────────────────────────
HKT = pytz.timezone("Asia/Hong_Kong")
USER_AGENT = "DiscordTechBot/1.0"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
NITTER_BASE_URLS = [
    # 官方 instance，2025年2月重新上線並持續維護
    "https://nitter.net",
    # 以下為目前 wiki 確認 ✅✅ 狀態的 instances
    "https://nitter.privacyredirect.com",
    "https://nitter.space",
    "https://nitter.tiekoetter.com",
    "https://lightbrd.com",
    "https://nuku.trabun.org",
    "https://nitter.kuuro.net",
    # 其他長期存活的備用
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
]

NITTER_TOPIC_QUERY: dict[str, str] = {
    "AI": "AI OR LLM OR open source AI",
    "ESP32": "ESP32 OR esp-idf",
    "RP2040": "RP2040 OR RP2350 OR pico w OR pico 2",
    "Arduino": "Arduino project",
    "Maker": "maker project OR diy build",
    "3D列印": "3D printing OR FDM OR resin print",
}

# AI model fallback cascade — update IDs if they differ on openrouter.ai/models
OPENROUTER_MODELS: list[str] = [
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]

# ─── Environment Validation ───────────────────────────────────────────────────
_REQUIRED_ENV = [
    "DISCORD_WEBHOOK_URL",
    "OPENROUTER_API_KEY",
    "X_USERNAME",
    "X_PASSWORD",
    "X_EMAIL",
    "X_EMAIL_PW",
]


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse truthy/falsy env values safely."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def validate_env() -> dict[str, str]:
    """Fail fast if any required env var is missing. Logs names only (no values)."""
    missing = [k for k in _REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        log.error("❌ Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)
    cfg = {k: os.environ[k] for k in _REQUIRED_ENV}
    log.info("✅ All env vars present: %s", ", ".join(_REQUIRED_ENV))
    return cfg


def get_nitter_bases() -> list[str]:
    """Return ordered Nitter mirrors from env override or defaults."""
    raw = os.environ.get("NITTER_BASE_URLS", "").strip()
    if not raw:
        return NITTER_BASE_URLS
    mirrors = [m.strip().rstrip("/") for m in raw.split(",") if m.strip()]
    return mirrors or NITTER_BASE_URLS


# ─── Topic Configuration ──────────────────────────────────────────────────────
TOPICS: list[dict[str, Any]] = [
    {
        "name": "AI",
        "emoji": "🤖",
        "color": 0x5865F2,
        "query": (
            "(new AI model OR AI project OR AI tool OR AI release OR AI paper)"
            " -is:retweet -is:reply"
        ),
        "min_faves": 20,
        "fallback_min_faves": 5,
        "fetch_limit": 10,
        "rss_feeds": ["hn_ai"],
    },
    {
        "name": "ESP32",
        "emoji": "🔌",
        "color": 0x57F287,
        "query": (
            "ESP32 (project OR tutorial OR build OR release OR firmware OR library)"
            " -is:retweet -is:reply"
        ),
        "min_faves": 5,
        "fallback_min_faves": 1,
        "fetch_limit": 10,
        "rss_feeds": ["reddit_esp32", "hackster", "adafruit"],
    },
    {
        "name": "RP2040",
        "emoji": "🔌",
        "color": 0x2ECC71,
        "query": (
            "(RP2040 OR RP2350) (project OR tutorial OR build OR release OR firmware OR library)"
            " -is:retweet -is:reply"
        ),
        "min_faves": 5,
        "fallback_min_faves": 1,
        "fetch_limit": 10,
        "rss_feeds": ["reddit_rp2040", "hackster", "adafruit"],
    },
    {
        "name": "Arduino",
        "emoji": "🔌",
        "color": 0x00979D,
        "query": (
            "Arduino (project OR tutorial OR build OR shield OR library OR new)"
            " -is:retweet -is:reply"
        ),
        "min_faves": 10,
        "fallback_min_faves": 1,
        "fetch_limit": 10,
        "rss_feeds": ["reddit_arduino", "hackster", "adafruit"],
    },
    {
        "name": "Maker",
        "emoji": "🛠️",
        "color": 0xFEE75C,
        "query": (
            "(maker project OR DIY build OR hackaday OR hackspace OR makerspace)"
            " -is:retweet -is:reply"
        ),
        "min_faves": 10,
        "fallback_min_faves": 1,
        "fetch_limit": 10,
        "rss_feeds": ["hackaday", "adafruit", "reddit_maker"],
    },
    {
        "name": "3D列印",
        "emoji": "🖨️",
        "color": 0xED4245,
        "query": (
            "(3Dprinting OR 3Dprint OR FDM OR resin print)"
            " (project OR model OR build OR release)"
            " -is:retweet -is:reply"
        ),
        "min_faves": 10,
        "fallback_min_faves": 1,
        "fetch_limit": 10,
        "rss_feeds": ["reddit_3dprinting", "printables", "thingiverse"],
    },
]

# ─── RSS Feed Configuration ───────────────────────────────────────────────────
RSS_FEEDS: dict[str, str] = {
    "hackaday":          "https://hackaday.com/blog/feed/",
    "hackster":          "https://www.hackster.io/feed",
    "adafruit":          "https://blog.adafruit.com/feed/",
    "printables":        "https://www.printables.com/feed.xml",
    "thingiverse":       "https://www.thingiverse.com/newest/rss",
    "hn_ai":             "https://hnrss.org/newest?q=AI+LLM&points=10",
    "reddit_esp32":      "https://www.reddit.com/r/esp32/.rss",
    "reddit_arduino":    "https://www.reddit.com/r/arduino/.rss",
    "reddit_rp2040":     "https://www.reddit.com/r/RP2040/.rss",
    "reddit_3dprinting": "https://www.reddit.com/r/3Dprinting/.rss",
    "reddit_maker":      "https://www.reddit.com/r/maker/.rss",
}

RSS_FEED_FALLBACKS: dict[str, list[str]] = {
    # Primary URLs are user-requested; fallback URLs keep data flowing if primaries fail.
    "printables": ["https://blog.prusa3d.com/feed/"],
    "thingiverse": ["https://www.thingiverse.com/rss"],
}

# Hackster and Adafruit cover multiple topics — keyword match determines assignment
_MULTI_TOPIC_FEEDS: frozenset[str] = frozenset({"hackster", "adafruit"})

_MULTI_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "ESP32":  ["esp32", "esp-32", "esp-idf"],
    "RP2040": ["rp2040", "rp2350", "pico w", "pico 2", "raspberry pi pico", "circuitpython"],
    "Arduino": ["arduino"],
    "Maker":  ["maker", "diy", "hack", "makerspace"],
    "3D列印": ["3d print", "3dprint", "fdm", "resin", "filament", "sla"],
}

# ─── Utilities ────────────────────────────────────────────────────────────────

def strip_html(text: str, max_len: int = 300) -> str:
    """Unescape HTML entities, remove tags, collapse whitespace, truncate."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _entry_datetime(entry: Any) -> Optional[datetime]:
    """Return UTC-aware datetime from a feedparser entry (checks published then updated)."""
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val is not None:
            try:
                return datetime.fromtimestamp(calendar.timegm(val), tz=timezone.utc)
            except Exception:
                pass
    return None


# ─── T2: twscrape — Account Setup ─────────────────────────────────────────────

async def setup_twscrape(cfg: dict[str, str]) -> twscrape.API:
    """Initialise twscrape; add account + login on first run, reuse session after."""
    os.makedirs("data", exist_ok=True)
    api = twscrape.API("data/accounts.db")
    try:
        accounts = await api.pool.get_all()
        if not accounts:
            log.info("twscrape: no accounts — adding account and logging in…")
            await api.pool.add_account(
                username=cfg["X_USERNAME"],
                password=cfg["X_PASSWORD"],
                email=cfg["X_EMAIL"],
                email_password=cfg["X_EMAIL_PW"],
            )
            await api.pool.login_all()
            refreshed = await api.pool.get_all()
            active_count = sum(1 for a in refreshed if getattr(a, "active", False))
            if active_count == 0:
                log.warning(
                    "twscrape login finished but no active accounts (likely Cloudflare/IP block). "
                    "X fetch will use Nitter fallback."
                )
            else:
                log.info("✅ twscrape login complete — active accounts: %d", active_count)
        else:
            active_count = sum(1 for a in accounts if getattr(a, "active", False))
            log.info(
                "✅ twscrape: reusing %d account(s), active=%d",
                len(accounts),
                active_count,
            )
    except Exception as exc:
        log.error("twscrape setup error: %s", exc)
        raise
    return api


# ─── T3: Tweet Fetching ────────────────────────────────────────────────────────

async def fetch_tweets(
    api: twscrape.API, topic: dict[str, Any], client: Optional[httpx.AsyncClient] = None
) -> list[dict[str, Any]]:
    """Search X for a topic; fallback to Nitter RSS if twscrape yields too few posts."""

    async def _search(query: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        try:
            async for tweet in api.search(query, limit=topic["fetch_limit"]):
                results.append(
                    {
                        "source": "x",
                        "author": tweet.user.username,
                        "content": tweet.rawContent,
                        "url": tweet.url,
                        "like_count": tweet.likeCount,
                    }
                )
        except Exception as exc:
            log.warning("Tweet fetch error (%s): %s", topic["name"], exc)
        return results

    primary_q = f"{topic['query']} min_faves:{topic['min_faves']}"
    tweets = await _search(primary_q)

    if len(tweets) < 3:
        log.info(
            "%s: primary → %d tweets; retry with min_faves=%d",
            topic["name"],
            len(tweets),
            topic["fallback_min_faves"],
        )
        fallback_q = f"{topic['query']} min_faves:{topic['fallback_min_faves']}"
        tweets = await _search(fallback_q)

    if len(tweets) < 3 and client is not None:
        nitter_posts = await _fetch_tweets_via_nitter(client, topic)
        seen = {t.get("url", "") for t in tweets}
        for post in nitter_posts:
            if post["url"] not in seen:
                tweets.append(post)
                seen.add(post["url"])
        if nitter_posts:
            log.info(
                "%s: added %d X posts via Nitter fallback",
                topic["name"],
                len(nitter_posts),
            )

    log.info("%s: %d tweets from X", topic["name"], len(tweets))
    return tweets


async def _fetch_tweets_via_nitter(
    client: httpx.AsyncClient, topic: dict[str, Any]
) -> list[dict[str, Any]]:
    """Fetch X-like posts through Nitter search RSS as fallback when twscrape is blocked."""
    # Keep query broad for RSS compatibility; nitter doesn't understand all X operators.
    raw_query = NITTER_TOPIC_QUERY.get(topic["name"], topic["name"])
    q = quote_plus(raw_query)

    for base in get_nitter_bases():
        url = f"{base}/search/rss?f=tweets&q={q}"
        try:
            resp = await client.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=20.0,
                follow_redirects=True,
            )
            resp.raise_for_status()
            parsed = feedparser.parse(resp.text)
            if parsed.get("bozo"):
                log.warning(
                    "Nitter bozo flag [%s]: %s",
                    base,
                    parsed.get("bozo_exception", "unknown"),
                )

            if "cloudflare" in resp.text.lower() or "blocked" in resp.text.lower():
                log.warning("Nitter mirror appears blocked [%s]", base)

            posts: list[dict[str, Any]] = []
            for entry in list(parsed.entries)[: topic.get("fetch_limit", 10)]:
                title = strip_html(getattr(entry, "title", "") or "", 300)
                link = getattr(entry, "link", "") or ""
                author = strip_html(getattr(entry, "author", "") or "nitter", 100)
                if link:
                    posts.append(
                        {
                            "source": "x",
                            "author": author,
                            "content": title,
                            "url": link,
                            "like_count": 0,
                        }
                    )

            if posts:
                log.info("Nitter fallback success [%s]: %d posts", base, len(posts))
                return posts
            log.warning("Nitter fallback [%s] returned 0 entries for query '%s'", base, raw_query)
        except Exception as exc:
            log.warning("Nitter fallback failed [%s]: %s", base, exc)

    return []


# ─── T3b: RSS Feed Fetching ────────────────────────────────────────────────────

async def _fetch_one_feed(
    client: httpx.AsyncClient, key: str, url: str
) -> tuple[str, list[dict[str, Any]]]:
    """Fetch + parse one RSS/Atom feed. Never raises; logs warnings on failure."""
    candidate_urls = [url] + RSS_FEED_FALLBACKS.get(key, [])
    parsed = None
    selected_url = ""
    selected_status = None

    for candidate in candidate_urls:
        try:
            resp = await client.get(
                candidate,
                headers={"User-Agent": USER_AGENT},
                timeout=15.0,
                follow_redirects=True,
            )
            current_parsed = feedparser.parse(resp.text)
            entry_count = len(getattr(current_parsed, "entries", []))

            # Accept normal success, or Thingiverse's odd behavior where /rss may return 404 but still contain feed data.
            if (200 <= resp.status_code < 400 and entry_count > 0) or (
                key == "thingiverse" and entry_count > 0
            ):
                parsed = current_parsed
                selected_url = candidate
                selected_status = resp.status_code
                break

            log.warning(
                "RSS candidate unusable [%s] %s: status=%s entries=%d",
                key,
                candidate,
                resp.status_code,
                entry_count,
            )
        except Exception as exc:
            log.warning("RSS fetch failed [%s] %s: %s", key, candidate, exc)

    if parsed is None:
        return key, []

    if parsed.get("bozo"):
        log.warning(
            "RSS bozo flag [%s]: %s", key, parsed.get("bozo_exception", "unknown")
        )

    now_utc = datetime.now(tz=timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    all_entries = list(parsed.entries)[:20]

    # Prefer recent entries; fall back to latest 3 if none are within 24h
    recent = [
        e
        for e in all_entries
        if (dt := _entry_datetime(e)) is not None and dt >= cutoff
    ]
    if not recent:
        recent = all_entries[:3]
    recent = recent[:5]

    entries: list[dict[str, Any]] = []
    for entry in recent:
        title = strip_html(getattr(entry, "title", "") or "", 200)
        link = getattr(entry, "link", "") or ""
        raw_summary = (
            getattr(entry, "summary", "")
            or (getattr(entry, "content", None) or [{}])[0].get("value", "")
            or ""
        )
        summary = strip_html(raw_summary, 300)
        if title and link:
            entries.append(
                {"source": "rss", "title": title, "link": link, "summary": summary}
            )

    log.info(
        "RSS [%s]: %d entries (url=%s status=%s)",
        key,
        len(entries),
        selected_url,
        selected_status,
    )
    return key, entries


async def fetch_all_rss(
    client: httpx.AsyncClient,
) -> dict[str, list[dict[str, Any]]]:
    """Fetch all 11 RSS feeds concurrently."""
    tasks = [_fetch_one_feed(client, k, u) for k, u in RSS_FEEDS.items()]
    results = await asyncio.gather(*tasks)
    return dict(results)


def _multi_feed_match(entry: dict[str, Any], topic_name: str) -> bool:
    """Return True if entry keywords suggest it belongs to this topic."""
    keywords = _MULTI_TOPIC_KEYWORDS.get(topic_name, [])
    if not keywords:
        # No keyword restriction defined for this topic in multi-topic feeds
        return True
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    return any(kw in text for kw in keywords)


def get_rss_for_topic(
    all_rss: dict[str, list[dict[str, Any]]],
    topic: dict[str, Any],
) -> list[dict[str, Any]]:
    """Collect RSS entries mapped to a topic, applying keyword filter for multi-topic feeds."""
    seen_links: set[str] = set()
    result: list[dict[str, Any]] = []
    for feed_key in topic["rss_feeds"]:
        for entry in all_rss.get(feed_key, []):
            if feed_key in _MULTI_TOPIC_FEEDS and not _multi_feed_match(
                entry, topic["name"]
            ):
                continue
            link = entry.get("link", "")
            if link and link in seen_links:
                continue
            seen_links.add(link)
            result.append(entry)
    return result


# ─── T4: AI Filtering (OpenRouter) ────────────────────────────────────────────

def _format_for_prompt(posts: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, p in enumerate(posts, 1):
        if p["source"] == "x":
            lines.append(
                f"{i}. [X] @{p['author']}: {p['content'][:400]} | {p['url']}"
            )
        else:
            lines.append(
                f"{i}. [RSS] {p['title']}: {p['summary'][:300]} | {p['link']}"
            )
    return "\n".join(lines)


def _raw_fallback(posts: list[dict[str, Any]]) -> str:
    lines = ["⚠️ AI 摘要不可用（原始資料）"]
    for p in posts[:5]:
        if p["source"] == "x":
            snippet = p.get("content", "")[:150]
            lines.append(f"• @{p['author']}: {snippet}…\n  {p['url']}")
        else:
            snippet = p.get("summary", "")[:150]
            lines.append(f"• {p['title']}: {snippet}…\n  {p['link']}")
    return "\n".join(lines)


async def ai_filter(
    client: httpx.AsyncClient,
    posts: list[dict[str, Any]],
    topic: dict[str, Any],
    cfg: dict[str, str],
) -> str:
    """Summarise posts in Traditional Chinese via OpenRouter with model fallback cascade."""
    if not posts:
        return "NO_CONTENT"

    chip_restriction = ""
    if topic["name"] in ("ESP32", "RP2040", "Arduino"):
        chip_restriction = (
            f"Only keep posts specifically about {topic['name']}. "
            "Remove posts about unrelated microcontrollers or SBCs. "
        )

    system_msg = (
        "You are a tech news curator. All output must be in Traditional Chinese "
        "(繁體中文). Be concise and informative."
    )
    user_msg = (
        f"Topic: {topic['emoji']} {topic['name']}\n\n"
        f"Posts:\n{_format_for_prompt(posts)}\n\n"
        "Instructions:\n"
        f"- {chip_restriction}"
        "- Remove ads, promotional content, reposts, and off-topic posts.\n"
        "- Keep the best 3–5 posts.\n"
        "- For each, write 1–2 sentence Traditional Chinese summary followed by URL on the same line.\n"
        "- Format: one post per line, each starting with • \n"
        "- If no posts are valuable, respond with exactly: NO_CONTENT\n"
        "- Total response must be under 650 characters."
    )

    for model in OPENROUTER_MODELS:
        try:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {cfg['OPENROUTER_API_KEY']}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/discord-tech-bot",
                    "X-Title": "Discord Tech Bot",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 600,
                    "temperature": 0.3,
                },
                timeout=60.0,  # free-tier models can be slow
            )

            if resp.status_code != 200:
                log.warning(
                    "OpenRouter [%s] HTTP %d for %s: %s",
                    model,
                    resp.status_code,
                    topic["name"],
                    resp.text[:200],
                )
                continue

            content = (
                resp.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if content is None:
                content = ""
            elif not isinstance(content, str):
                content = str(content)
            content = content.strip()
            if not content:
                log.warning(
                    "OpenRouter [%s] empty/null content for %s", model, topic["name"]
                )
                continue

            # Enforce 700-char budget — trim at last complete bullet
            if len(content) > 700:
                truncated = content[:700].rsplit("\n•", 1)[0]
                content = (
                    truncated.rstrip() + "\n…"
                    if len(truncated) < len(content[:700])
                    else content[:697] + "…"
                )
                log.warning(
                    "Truncated AI output for %s to fit 700-char budget", topic["name"]
                )

            log.info("✅ AI [%s] → %s: %d chars", model, topic["name"], len(content))
            return content

        except Exception as exc:
            log.warning(
                "OpenRouter [%s] error for %s: %s", model, topic["name"], exc
            )
            continue

    log.error("All AI models exhausted for %s — raw fallback", topic["name"])
    return _raw_fallback(posts)


# ─── T5: Discord Embed Builder ────────────────────────────────────────────────

def _embed_for(topic: dict[str, Any], summary: str) -> dict[str, Any]:
    now_hkt = datetime.now(tz=HKT).strftime("%Y-%m-%d %H:%M")
    if not summary or summary.strip() in ("NO_CONTENT", ""):
        description = "⚠️ 今日暫無相關內容"
    else:
        description = summary[:4096]  # hard Discord per-embed limit
    return {
        "title": f"{topic['emoji']} {topic['name']} 每日精選",
        "description": description,
        "color": topic["color"],
        "footer": {"text": f"更新時間：{now_hkt} HKT"},
    }


def _error_embed(topic: dict[str, Any]) -> dict[str, Any]:
    now_hkt = datetime.now(tz=HKT).strftime("%Y-%m-%d %H:%M")
    return {
        "title": f"{topic['emoji']} {topic['name']} 每日精選",
        "description": "❌ 抓取失敗，請檢查 log",
        "color": topic["color"],
        "footer": {"text": f"更新時間：{now_hkt} HKT"},
    }


def _embed_char_len(embed: dict[str, Any]) -> int:
    return (
        len(embed.get("title", ""))
        + len(embed.get("description", ""))
        + len(embed.get("footer", {}).get("text", ""))
    )


def build_all_embeds(
    results: list[tuple[dict[str, Any], Optional[str]]],
) -> list[dict[str, Any]]:
    """Build 7 embeds and trim descriptions if total exceeds Discord's 6000-char limit."""
    embeds = [
        _error_embed(topic) if summary is None else _embed_for(topic, summary)
        for topic, summary in results
    ]

    # Safety margin: keep total below 5800 (Discord hard limit is 6000)
    total = sum(_embed_char_len(e) for e in embeds)
    while total > 5800:
        longest_idx = max(
            range(len(embeds)), key=lambda i: len(embeds[i].get("description", ""))
        )
        desc = embeds[longest_idx].get("description", "")
        if len(desc) <= 50:
            break  # Nothing left to trim
        embeds[longest_idx]["description"] = desc[: len(desc) - 50] + "…"
        total = sum(_embed_char_len(e) for e in embeds)

    if total > 5800:
        log.warning("Total embed chars %d still above 5800 after trimming", total)

    return embeds


# ─── T6: Discord Webhook Sender ───────────────────────────────────────────────

async def send_to_discord(
    client: httpx.AsyncClient,
    embeds: list[dict[str, Any]],
    cfg: dict[str, str],
) -> bool:
    """POST all embeds to Discord webhook; handles 429 with a single retry."""

    async def _post() -> httpx.Response:
        return await client.post(
            cfg["DISCORD_WEBHOOK_URL"],
            json={"embeds": embeds},
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

    try:
        resp = await _post()
        if resp.status_code == 429:
            retry_after = float(resp.json().get("retry_after", 5))
            log.warning("Discord 429 — retrying after %.1fs", retry_after)
            await asyncio.sleep(retry_after)
            resp = await _post()

        if resp.status_code in (200, 204):
            log.info(
                "✅ Discord webhook delivered (%d embeds, HTTP %d)",
                len(embeds),
                resp.status_code,
            )
            return True

        log.error(
            "Discord webhook failed: HTTP %d — %s",
            resp.status_code,
            resp.text[:300],
        )
        return False

    except Exception as exc:
        log.error("Discord webhook exception: %s", exc)
        return False


# ─── T7: Orchestrator ─────────────────────────────────────────────────────────

async def run_daily_job(cfg: dict[str, str], tw_api: twscrape.API) -> None:
    """
    Full daily pipeline:
      1. Fetch all RSS feeds concurrently (single batch).
      2. For each of 7 topics: fetch X tweets + merge RSS + AI filter.
      3. Build all 7 embeds and POST to Discord.

    Each topic is error-isolated — individual failures produce an error embed,
    not a crash of the whole job.
    """
    start = time.monotonic()
    log.info(
        "═══ Daily job started at %s HKT ═══",
        datetime.now(tz=HKT).strftime("%Y-%m-%d %H:%M:%S"),
    )

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Phase 1 — RSS (concurrent, single batch)
        log.info("Fetching %d RSS feeds concurrently…", len(RSS_FEEDS))
        all_rss = await fetch_all_rss(client)

        # Phase 2 — per-topic pipeline
        results: list[tuple[dict[str, Any], Optional[str]]] = []

        for topic in TOPICS:
            try:
                rss_posts = get_rss_for_topic(all_rss, topic)
                tweets = await fetch_tweets(tw_api, topic, client)

                # Merge: RSS first (higher quality), X after; deduplicate by URL
                seen_urls: set[str] = set()
                merged: list[dict[str, Any]] = []

                for post in rss_posts:
                    url = post.get("link", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged.append(post)

                for post in tweets:
                    url = post.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged.append(post)

                log.info(
                    "%s: %d RSS + %d X → %d merged",
                    topic["name"],
                    len(rss_posts),
                    len(tweets),
                    len(merged),
                )
                if len(merged) < 3:
                    log.warning(
                        "%s: fewer than 3 posts available", topic["name"]
                    )

                summary = await ai_filter(client, merged, topic, cfg)
                results.append((topic, summary))

            except Exception as exc:
                log.error(
                    "Topic %s pipeline error: %s",
                    topic["name"],
                    exc,
                    exc_info=True,
                )
                results.append((topic, None))  # None → error embed

            # Brief pause between topics (reduces X rate-limit risk)
            await asyncio.sleep(2)

        # Phase 3 — deliver
        embeds = build_all_embeds(results)
        await send_to_discord(client, embeds, cfg)

    elapsed = time.monotonic() - start
    log.info("═══ Daily job complete in %.1fs ═══", elapsed)


# ─── T8: Scheduler & Main Loop ────────────────────────────────────────────────

async def main() -> None:
    """Entry point: validate env → run once → schedule daily at 13:30 HKT."""
    log.info("Discord Daily Tech Bot — starting up")

    # T10: startup validation (fail fast if env vars missing)
    cfg = validate_env()

    # T2: twscrape account setup
    tw_api = await setup_twscrape(cfg)

    async def _job() -> None:
        await run_daily_job(cfg, tw_api)

    run_on_startup = _env_bool("RUN_ON_STARTUP", default=False)
    if run_on_startup:
        log.info("RUN_ON_STARTUP=true -> executing immediate startup run")
        await _job()
    else:
        log.info("RUN_ON_STARTUP=false -> skip immediate run; waiting for schedule")

    # Schedule daily at 13:30 HKT
    scheduler = AsyncIOScheduler(timezone=HKT)
    scheduler.add_job(_job, CronTrigger(hour=13, minute=30, timezone=HKT))
    scheduler.start()

    jobs = scheduler.get_jobs()
    if jobs:
        log.info("⏰ Next scheduled run: %s", jobs[0].next_run_time)

    try:
        # Keep event loop alive
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutdown signal — stopping scheduler")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
