import os
import unittest
from unittest.mock import AsyncMock, Mock, patch

import main


class LegacyCodeRemovalTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "DISCORD_WEBHOOK_URL": "https://discord.example/main",
            "DISCORD_INIT_WEBHOOK_URL": "https://discord.example/init",
            "OPENROUTER_API_KEY": "sk-test",
            "DIGEST_MODE": "legacy",
        },
        clear=True,
    )
    def test_validate_env_rejects_legacy_mode(self):
        with self.assertRaises(SystemExit):
            main.validate_env()

    def test_legacy_x_helpers_removed(self):
        self.assertFalse(hasattr(main, "fetch_tweets"))
        self.assertFalse(hasattr(main, "discover_x_urls"))
        self.assertFalse(hasattr(main, "fetch_fxtwitter_tweet"))


class TopicDistributionTests(unittest.TestCase):
    def test_maker_category_removed_and_feeds_distributed(self):
        topic_names = {topic["name"] for topic in main.TOPICS}
        self.assertNotIn("Maker", topic_names)

        distributed_targets = [
            topic for topic in main.TOPICS if topic["name"] in {"ESP32", "RP2040", "Arduino", "3D列印"}
        ]
        distributed_feed_keys = {
            feed
            for topic in distributed_targets
            for feed in topic["rss_feeds"]
        }

        for maker_feed in {
            "hackaday",
            "adafruit",
            "adafruit_learning",
            "makezine",
            "reddit_maker",
            "reddit_diy",
            "reddit_electronics",
        }:
            self.assertIn(maker_feed, distributed_feed_keys)

    def test_each_category_has_at_least_10_xers(self):
        for topic in main.TOPICS:
            self.assertGreaterEqual(
                len(topic.get("x_handles", [])),
                10,
                f"{topic['name']} should define >=10 x_handles",
            )

    def test_ai_category_contains_required_requested_xers(self):
        ai_topic = next(topic for topic in main.TOPICS if topic["name"] == "AI")
        for handle in {"Khazix0918", "dotey", "vista8"}:
            self.assertIn(handle, ai_topic.get("x_handles", []))


class InitWebhookTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_init_message_uses_init_webhook_env(self):
        client = AsyncMock()
        client.post.return_value.status_code = 204

        cfg = {
            "DISCORD_WEBHOOK_URL": "https://discord.example/main",
            "DISCORD_INIT_WEBHOOK_URL": "https://discord.example/init",
        }

        await main.send_init_message(
            client,
            cfg,
            branch="main",
            remote="origin",
            rss_feed_count=12,
        )

        client.post.assert_awaited_once()
        self.assertEqual(client.post.await_args.args[0], cfg["DISCORD_INIT_WEBHOOK_URL"])
        payload = client.post.await_args.kwargs["json"]
        self.assertIn("Bot init", payload["content"])
        self.assertIn("rss_feeds=12", payload["content"])

    async def test_send_init_message_falls_back_to_main_webhook_when_init_missing(self):
        client = AsyncMock()
        client.post.return_value.status_code = 204

        cfg = {
            "DISCORD_WEBHOOK_URL": "https://discord.example/main",
            "DISCORD_INIT_WEBHOOK_URL": "",
        }

        await main.send_init_message(
            client,
            cfg,
            branch="main",
            remote="origin",
            rss_feed_count=12,
        )

        client.post.assert_awaited_once()
        self.assertEqual(client.post.await_args.args[0], cfg["DISCORD_WEBHOOK_URL"])


class SelfUpdateTests(unittest.TestCase):
    def test_check_and_apply_repo_update_skips_dirty_tree(self):
        responses = [
            Mock(returncode=0, stdout="main\n", stderr=""),
            Mock(returncode=0, stdout="M main.py\n", stderr=""),
        ]

        with patch("main.subprocess.run", side_effect=responses):
            result = main.check_and_apply_repo_update(repo_path=".")

        self.assertEqual(result["status"], "skipped")
        self.assertIn("dirty", result["reason"])

    def test_check_and_apply_repo_update_fast_forwards_when_remote_ahead(self):
        responses = [
            Mock(returncode=0, stdout="main\n", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout="abc123\n", stderr=""),
            Mock(returncode=0, stdout="def456\n", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout="Updating abc123..def456\n", stderr=""),
        ]

        with patch("main.subprocess.run", side_effect=responses):
            result = main.check_and_apply_repo_update(repo_path=".")

        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["branch"], "main")
        self.assertEqual(result["before"], "abc123")
        self.assertEqual(result["after"], "def456")


class RssCatalogTests(unittest.TestCase):
    def test_rss_feeds_include_new_high_signal_sources(self):
        for key in [
            "openai_news",
            "huggingface_blog",
            "google_ai_blog",
            "reddit_openai",
            "reddit_chatgpt",
            "arduino_blog",
            "raspberry_pi_news",
            "prusa_blog",
            "voxelmatters",
            "reddit_localllama",
            "reddit_singularity",
            "reddit_microcontrollers",
            "reddit_embedded",
            "all3dp",
        ]:
            self.assertIn(key, main.RSS_FEEDS)

    def test_ai_topic_includes_additional_reddit_ai_sources(self):
        ai_topic = next(topic for topic in main.TOPICS if topic["name"] == "AI")
        self.assertIn("reddit_openai", ai_topic["rss_feeds"])
        self.assertIn("reddit_chatgpt", ai_topic["rss_feeds"])


class DigestFormatTests(unittest.TestCase):
    def test_build_all_embeds_compacts_verbose_ai_bullets_to_one_line(self):
        topic = {
            "name": "AI",
            "emoji": "🤖",
            "color": 0x5865F2,
        }
        verbose_summary = (
            "• OpenAI 發布新模型，提升推理能力並改善工具呼叫穩定性，"
            "這對開發者在代理工作流與長任務處理上有直接幫助。\n"
            "  https://example.com/openai\n"
            "• GitHub 推出新功能，讓開源專案維護流程更順，"
            "對持續整合與版本管理有實際影響。 https://example.com/github"
        )

        embeds = main.build_all_embeds([(topic, verbose_summary)])

        description = embeds[0]["description"]
        lines = description.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(line.startswith("• ") for line in lines))
        self.assertIn("https://example.com/openai", lines[0])
        self.assertIn("https://example.com/github", lines[1])
        self.assertNotIn("\n  https://example.com/openai", description)

    def test_compact_summary_uses_visual_link_separator(self):
        summary = "• OpenAI 發布新模型並改善推理延遲 https://example.com/openai"
        compacted = main._compact_summary_for_discord(summary, max_body_len=120)
        self.assertIn(" ｜ https://example.com/openai", compacted)

    def test_build_all_embeds_orders_by_topic_config(self):
        ai_topic = next(topic for topic in main.TOPICS if topic["name"] == "AI")
        topic_3d = next(topic for topic in main.TOPICS if topic["name"] == "3D列印")

        embeds = main.build_all_embeds(
            [
                (topic_3d, "• 3D news https://example.com/3d"),
                (ai_topic, "• AI news https://example.com/ai"),
            ]
        )

        self.assertIn("AI", embeds[0]["title"])


class SourceRolloutTests(unittest.TestCase):
    def test_wave1_runtime_x_handles_include_overlay_and_exclude_wave2(self):
        ai_topic = next(topic for topic in main.TOPICS if topic["name"] == "AI")
        cfg = {"SOURCE_ROLLOUT_MODE": "wave1"}

        handles = main._topic_runtime_x_handles(ai_topic, cfg)

        self.assertIn("thdx", handles)
        self.assertNotIn("clairevo", handles)

    def test_wave2_runtime_x_handles_include_wave2_overlay(self):
        ai_topic = next(topic for topic in main.TOPICS if topic["name"] == "AI")
        cfg = {"SOURCE_ROLLOUT_MODE": "wave2"}

        handles = main._topic_runtime_x_handles(ai_topic, cfg)

        self.assertIn("thdx", handles)
        self.assertIn("clairevo", handles)

    def test_runtime_youtube_channels_include_curated_entries(self):
        topic_3d = next(topic for topic in main.TOPICS if topic["name"] == "3D列印")
        cfg = {
            "SOURCE_ROLLOUT_MODE": "wave1",
            "TOPIC_YOUTUBE_ENABLED": "true",
        }

        channels = main._topic_runtime_youtube_channels(topic_3d, cfg)

        self.assertIn("@makersmuse", channels)
        self.assertIn("@greatscottlab", channels)


class MigrationConfigTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "DISCORD_WEBHOOK_URL": "https://discord.example/main",
            "DISCORD_INIT_WEBHOOK_URL": "https://discord.example/init",
            "OPENROUTER_API_KEY": "sk-test",
            "DIGEST_MODE": "follow-builders-hybrid",
            "FOLLOW_BUILDERS_SOURCE_MODE": "pinned",
        },
        clear=True,
    )
    def test_validate_env_pinned_source_mode_requires_ref(self):
        with self.assertRaises(SystemExit):
            main.validate_env()

    @patch.dict(
        os.environ,
        {
            "DISCORD_WEBHOOK_URL": "https://discord.example/main",
            "OPENROUTER_API_KEY": "sk-test",
            "DIGEST_MODE": "follow-builders-hybrid",
            "FOLLOW_BUILDERS_SOURCE_MODE": "central",
        },
        clear=True,
    )
    def test_validate_env_allows_missing_init_webhook(self):
        cfg = main.validate_env()
        self.assertEqual(cfg["DISCORD_INIT_WEBHOOK_URL"], cfg["DISCORD_WEBHOOK_URL"])


class FollowBuildersFeedTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_follow_builders_feeds_normalizes_data(self):
        cfg = {
            "FOLLOW_BUILDERS_FEED_X_URL": "https://example.com/feed-x.json",
            "FOLLOW_BUILDERS_FEED_PODCASTS_URL": "https://example.com/feed-podcasts.json",
            "FOLLOW_BUILDERS_FEED_BLOGS_URL": "https://example.com/feed-blogs.json",
        }

        x_payload = {
            "generatedAt": "2026-03-29T00:00:00Z",
            "x": [
                {
                    "name": "Andrej Karpathy",
                    "handle": "karpathy",
                    "tweets": [
                        {
                            "id": "1",
                            "text": "New model training note",
                            "url": "https://x.com/karpathy/status/1",
                        }
                    ],
                }
            ],
        }
        podcasts_payload = {
            "podcasts": [
                {
                    "name": "Latent Space",
                    "title": "Agent systems",
                    "url": "https://youtube.com/watch?v=abc",
                    "transcript": "Long transcript text",
                }
            ]
        }
        blogs_payload = {
            "blogs": [
                {
                    "name": "Anthropic Engineering",
                    "title": "Model release",
                    "url": "https://www.anthropic.com/engineering/model-release",
                    "content": "Article body",
                }
            ]
        }

        responses: dict[str, Mock] = {}
        for url, payload in {
            cfg["FOLLOW_BUILDERS_FEED_X_URL"]: x_payload,
            cfg["FOLLOW_BUILDERS_FEED_PODCASTS_URL"]: podcasts_payload,
            cfg["FOLLOW_BUILDERS_FEED_BLOGS_URL"]: blogs_payload,
        }.items():
            resp = Mock()
            resp.raise_for_status.return_value = None
            resp.json.return_value = payload
            responses[url] = resp

        client = AsyncMock()
        client.get.side_effect = lambda url, **_: responses[url]

        normalized = await main.fetch_follow_builders_feeds(client, cfg)

        self.assertEqual(normalized["stats"]["x_builders"], 1)
        self.assertEqual(normalized["stats"]["total_tweets"], 1)
        self.assertEqual(normalized["stats"]["podcast_items"], 1)
        self.assertEqual(normalized["stats"]["blog_items"], 1)
        self.assertEqual(len(normalized["builders"]), 1)
        self.assertEqual(len(normalized["podcasts"]), 1)
        self.assertEqual(len(normalized["blogs"]), 1)
        self.assertEqual(normalized["errors"], [])

    async def test_fetch_follow_builders_feeds_surfaces_malformed_payload_error(self):
        cfg = {
            "FOLLOW_BUILDERS_FEED_X_URL": "https://example.com/feed-x.json",
            "FOLLOW_BUILDERS_FEED_PODCASTS_URL": "https://example.com/feed-podcasts.json",
            "FOLLOW_BUILDERS_FEED_BLOGS_URL": "https://example.com/feed-blogs.json",
        }

        bad = Mock()
        bad.raise_for_status.return_value = None
        bad.json.side_effect = ValueError("bad json")

        ok = Mock()
        ok.raise_for_status.return_value = None
        ok.json.return_value = {"podcasts": []}

        ok_blogs = Mock()
        ok_blogs.raise_for_status.return_value = None
        ok_blogs.json.return_value = {"blogs": []}

        responses = {
            cfg["FOLLOW_BUILDERS_FEED_X_URL"]: bad,
            cfg["FOLLOW_BUILDERS_FEED_PODCASTS_URL"]: ok,
            cfg["FOLLOW_BUILDERS_FEED_BLOGS_URL"]: ok_blogs,
        }

        client = AsyncMock()
        client.get.side_effect = lambda url, **_: responses[url]

        with patch("main._read_follow_builders_cache", return_value=None):
            normalized = await main.fetch_follow_builders_feeds(client, cfg)

        self.assertEqual(normalized["builders"], [])
        self.assertGreaterEqual(len(normalized["errors"]), 1)

    async def test_fetch_follow_builders_feeds_uses_mirror_candidates_when_primary_fails(self):
        cfg = {
            "FOLLOW_BUILDERS_BASE_URLS": "https://primary.example,https://mirror.example",
            "FOLLOW_BUILDERS_FEED_X_URL": "https://primary.example/feed-x.json",
            "FOLLOW_BUILDERS_FEED_PODCASTS_URL": "https://primary.example/feed-podcasts.json",
            "FOLLOW_BUILDERS_FEED_BLOGS_URL": "https://primary.example/feed-blogs.json",
            "FOLLOW_BUILDERS_CACHE_ENABLED": "false",
            "FOLLOW_BUILDERS_CACHE_TTL_HOURS": "48",
        }

        x_payload = {
            "x": [
                {
                    "name": "Andrej Karpathy",
                    "handle": "karpathy",
                    "tweets": [
                        {
                            "id": "1",
                            "text": "New model training note",
                            "url": "https://x.com/karpathy/status/1",
                        }
                    ],
                }
            ]
        }
        podcasts_payload = {
            "podcasts": [
                {
                    "name": "Latent Space",
                    "title": "Agent systems",
                    "url": "https://youtube.com/watch?v=abc",
                    "transcript": "Long transcript text",
                }
            ]
        }
        blogs_payload = {
            "blogs": [
                {
                    "name": "Anthropic Engineering",
                    "title": "Model release",
                    "url": "https://www.anthropic.com/engineering/model-release",
                    "content": "Article body",
                }
            ]
        }

        x_resp = Mock()
        x_resp.raise_for_status.return_value = None
        x_resp.json.return_value = x_payload

        p_resp = Mock()
        p_resp.raise_for_status.return_value = None
        p_resp.json.return_value = podcasts_payload

        b_resp = Mock()
        b_resp.raise_for_status.return_value = None
        b_resp.json.return_value = blogs_payload

        async def _get(url, **_):
            if url.startswith("https://primary.example"):
                raise RuntimeError("primary down")
            if url == "https://mirror.example/feed-x.json":
                return x_resp
            if url == "https://mirror.example/feed-podcasts.json":
                return p_resp
            if url == "https://mirror.example/feed-blogs.json":
                return b_resp
            raise AssertionError(f"Unexpected URL {url}")

        client = AsyncMock()
        client.get.side_effect = _get

        normalized = await main.fetch_follow_builders_feeds(client, cfg)

        self.assertEqual(normalized["stats"]["x_builders"], 1)
        self.assertEqual(normalized["stats"]["podcast_items"], 1)
        self.assertEqual(normalized["stats"]["blog_items"], 1)

    async def test_fetch_follow_builders_feeds_uses_cache_when_all_sources_fail(self):
        cfg = {
            "FOLLOW_BUILDERS_BASE_URLS": "https://primary.example",
            "FOLLOW_BUILDERS_FEED_X_URL": "https://primary.example/feed-x.json",
            "FOLLOW_BUILDERS_FEED_PODCASTS_URL": "https://primary.example/feed-podcasts.json",
            "FOLLOW_BUILDERS_FEED_BLOGS_URL": "https://primary.example/feed-blogs.json",
            "FOLLOW_BUILDERS_CACHE_ENABLED": "true",
            "FOLLOW_BUILDERS_CACHE_TTL_HOURS": "48",
        }

        cached = {
            "generated_at": "2026-03-31T00:00:00Z",
            "builders": [
                {
                    "name": "Andrej Karpathy",
                    "handle": "karpathy",
                    "tweets": [
                        {
                            "text": "Cached note",
                            "url": "https://x.com/karpathy/status/1",
                        }
                    ],
                }
            ],
            "podcasts": [],
            "blogs": [],
            "stats": {
                "x_builders": 1,
                "total_tweets": 1,
                "podcast_items": 0,
                "blog_items": 0,
            },
            "errors": [],
        }

        client = AsyncMock()
        client.get.side_effect = RuntimeError("network down")

        with patch("main._read_follow_builders_cache", return_value=cached):
            normalized = await main.fetch_follow_builders_feeds(client, cfg)

        self.assertEqual(normalized["stats"]["x_builders"], 1)
        self.assertIn("using cached follow-builders data", " ".join(normalized["errors"]))


class AiBuilderSummaryTests(unittest.TestCase):
    def test_build_ai_builder_summary_includes_identity_and_url(self):
        fb_data = {
            "builders": [
                {
                    "name": "Andrej Karpathy",
                    "handle": "karpathy",
                    "tweets": [
                        {
                            "text": "Shared a practical note on eval loops",
                            "url": "https://x.com/karpathy/status/1",
                        }
                    ],
                }
            ],
            "podcasts": [],
            "blogs": [],
        }

        summary = main.build_ai_builder_summary(fb_data)

        self.assertIn("@karpathy", summary)
        self.assertIn("https://x.com/karpathy/status/1", summary)
        self.assertTrue(summary.startswith("• "))


class HybridOrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_daily_job_hybrid_uses_follow_builders_and_skips_x_fetch(self):
        client = AsyncMock()

        class _ClientCtx:
            async def __aenter__(self_inner):
                return client

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        cfg = {
            "DIGEST_MODE": "follow-builders-hybrid",
            "MAKER_RSS_ENABLED": "false",
            "MAKER_RSS_TOPIC_SET": "ESP32,RP2040,Arduino,3D列印",
            "DISCORD_WEBHOOK_URL": "https://discord.example/main",
            "DISCORD_INIT_WEBHOOK_URL": "https://discord.example/init",
            "OPENROUTER_API_KEY": "sk-test",
            "FOLLOW_BUILDERS_FEED_X_URL": "https://example.com/feed-x.json",
            "FOLLOW_BUILDERS_FEED_PODCASTS_URL": "https://example.com/feed-podcasts.json",
            "FOLLOW_BUILDERS_FEED_BLOGS_URL": "https://example.com/feed-blogs.json",
        }

        fb_data = {
            "builders": [
                {
                    "name": "Andrej Karpathy",
                    "handle": "karpathy",
                    "tweets": [
                        {
                            "text": "Shared a practical note",
                            "url": "https://x.com/karpathy/status/1",
                        }
                    ],
                }
            ],
            "podcasts": [],
            "blogs": [],
            "errors": [],
            "stats": {
                "x_builders": 1,
                "total_tweets": 1,
                "podcast_items": 0,
                "blog_items": 0,
            },
        }

        with patch("main.httpx.AsyncClient", return_value=_ClientCtx()), patch(
            "main.fetch_follow_builders_feeds", new=AsyncMock(return_value=fb_data)
        ) as feed_mock, patch(
            "main.ai_filter",
            new=AsyncMock(return_value="• 這是繁中摘要 https://x.com/karpathy/status/1"),
        ) as ai_filter_mock, patch(
            "main.send_to_discord", new=AsyncMock(return_value=True)
        ) as send_mock, patch(
            "main.maybe_apply_repo_update", new=AsyncMock(return_value={"status": "skipped"})
        ), patch("main.asyncio.sleep", new=AsyncMock(return_value=None)):
            await main.run_daily_job(cfg)

        feed_mock.assert_awaited_once()
        ai_filter_mock.assert_awaited_once()
        send_mock.assert_awaited_once()

        embeds = send_mock.await_args.args[1]
        self.assertEqual(len(embeds), 1)
        self.assertIn("AI", embeds[0]["title"])
        self.assertIn("繁中摘要", embeds[0]["description"])

    async def test_run_daily_job_hybrid_falls_back_to_ai_rss_when_follow_builders_empty(self):
        client = AsyncMock()

        class _ClientCtx:
            async def __aenter__(self_inner):
                return client

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        cfg = {
            "DIGEST_MODE": "follow-builders-hybrid",
            "MAKER_RSS_ENABLED": "false",
            "MAKER_RSS_TOPIC_SET": "ESP32,RP2040,Arduino,3D列印",
            "DISCORD_WEBHOOK_URL": "https://discord.example/main",
            "DISCORD_INIT_WEBHOOK_URL": "https://discord.example/init",
            "OPENROUTER_API_KEY": "sk-test",
            "FOLLOW_BUILDERS_FEED_X_URL": "https://example.com/feed-x.json",
            "FOLLOW_BUILDERS_FEED_PODCASTS_URL": "https://example.com/feed-podcasts.json",
            "FOLLOW_BUILDERS_FEED_BLOGS_URL": "https://example.com/feed-blogs.json",
        }

        fb_data = {
            "builders": [],
            "podcasts": [],
            "blogs": [],
            "errors": ["x feed error"],
            "stats": {
                "x_builders": 0,
                "total_tweets": 0,
                "podcast_items": 0,
                "blog_items": 0,
            },
        }

        ai_rss_payload = {
            "openai_news": [
                {
                    "source": "openai_news",
                    "title": "OpenAI release",
                    "link": "https://openai.com/news/example",
                    "summary": "new capability",
                    "published": "",
                }
            ]
        }

        with patch("main.httpx.AsyncClient", return_value=_ClientCtx()), patch(
            "main.fetch_follow_builders_feeds", new=AsyncMock(return_value=fb_data)
        ), patch(
            "main.fetch_all_rss", new=AsyncMock(return_value=ai_rss_payload)
        ) as fetch_all_rss_mock, patch(
            "main.ai_filter",
            new=AsyncMock(return_value="• 這是 AI RSS 備援摘要 https://openai.com/news/example"),
        ) as ai_filter_mock, patch(
            "main.send_to_discord", new=AsyncMock(return_value=True)
        ) as send_mock, patch(
            "main.maybe_apply_repo_update", new=AsyncMock(return_value={"status": "skipped"})
        ), patch("main.asyncio.sleep", new=AsyncMock(return_value=None)):
            await main.run_daily_job(cfg)

        fetch_all_rss_mock.assert_awaited_once()
        ai_filter_mock.assert_awaited_once()
        send_mock.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()