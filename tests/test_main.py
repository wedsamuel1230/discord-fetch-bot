import unittest
from unittest.mock import AsyncMock, Mock, patch

import main


class FetchXPostsTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_tweets_uses_discovery_and_hydration(self):
        topic = {
            "name": "AI",
            "fetch_limit": 5,
            "discover_queries": ["AI LLM open source model"],
        }

        discovered = [
            {
                "url": "https://x.com/example/status/123",
                "title": "Example title",
                "snippet": "Example snippet",
            }
        ]
        hydrated = {
            "source": "x",
            "author": "example",
            "content": "Hydrated tweet text",
            "url": "https://x.com/example/status/123",
            "like_count": 91,
        }

        with patch("main.discover_x_urls", return_value=discovered) as discover_mock, patch(
            "main.fetch_fxtwitter_tweet", new=AsyncMock(return_value=hydrated)
        ) as hydrate_mock:
            posts = await main.fetch_tweets(None, topic, AsyncMock())

        discover_mock.assert_called_once_with(topic, limit=topic["fetch_limit"])
        hydrate_mock.assert_awaited_once()
        self.assertEqual(posts, [hydrated])


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
            "arduino_blog",
            "raspberry_pi_news",
            "prusa_blog",
            "voxelmatters",
        ]:
            self.assertIn(key, main.RSS_FEEDS)


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


if __name__ == "__main__":
    unittest.main()