import unittest
from unittest import mock

from ai_news import ai_news_tool
from shared import cache_tool


def _rss(items):
    body = ["<rss><channel>"]
    for title, source, link, pub in items:
        body.append(
            "<item>"
            f"<title>{title}</title>"
            f"<source>{source}</source>"
            f"<link>{link}</link>"
            f"<pubDate>{pub}</pubDate>"
            "</item>"
        )
    body.append("</channel></rss>")
    return "".join(body).encode()


def _model(model_id, created_at, likes=1, downloads=2):
    return {
        "id": model_id,
        "createdAt": created_at,
        "likes": likes,
        "downloads": downloads,
    }


class AiNewsToolTest(unittest.TestCase):
    def setUp(self):
        cache_tool._cache.clear()

    def tearDown(self):
        cache_tool._cache.clear()

    def test_news_feeds_are_computed_with_quote(self):
        self.assertIn("AI%20%EC%98%81%EC%83%81%20%EC%83%9D%EC%84%B1", ai_news_tool.NEWS_FEEDS[0][1])
        self.assertIn("%22AI%20video%22%20model", ai_news_tool.NEWS_FEEDS[1][1])
        self.assertEqual(ai_news_tool.HF_PIPELINES, ["text-to-video", "image-to-video"])

    def test_fetch_news_parses_limits_and_sorts_rss_items(self):
        feeds = [("국내", "https://feed.test/kr"), ("해외", "https://feed.test/us")]
        kr_items = [
            (
                f"kr-{i}",
                "KR Source",
                f"https://news.test/kr/{i}",
                f"Tue, 07 Jul 2026 00:{i:02d}:00 +0000",
            )
            for i in range(30)
        ]
        us_items = [
            (
                "us-new",
                "US Source",
                "https://news.test/us/new",
                "Tue, 07 Jul 2026 02:00:00 +0000",
            )
        ]

        def fake_http_get(url, timeout=15):
            self.assertEqual(timeout, 12)
            return "application/rss+xml", _rss(kr_items if url.endswith("/kr") else us_items)

        with (
            mock.patch.object(ai_news_tool, "NEWS_FEEDS", feeds),
            mock.patch("ai_news.ai_news_tool.http_tool.http_get", side_effect=fake_http_get),
        ):
            news = ai_news_tool.fetch_news()

        self.assertEqual(len(news), 26)
        self.assertEqual(news[0]["title"], "us-new")
        self.assertEqual(news[0]["region"], "해외")
        self.assertEqual(news[0]["source"], "US Source")
        self.assertEqual(news[0]["link"], "https://news.test/us/new")
        self.assertEqual(sum(1 for item in news if item["region"] == "국내"), 25)
        self.assertGreaterEqual(news[0]["ts"], news[-1]["ts"])

    def test_fetch_news_returns_empty_chunk_on_fetch_or_parse_failure(self):
        with mock.patch("ai_news.ai_news_tool.http_tool.http_get", side_effect=TimeoutError):
            self.assertEqual(ai_news_tool.fetch_news(), [])

    def test_fetch_hf_models_dedupes_splits_and_limits_results(self):
        calls = []

        def fake_http_json(url, timeout=15):
            calls.append((url, timeout))
            self.assertEqual(timeout, 12)
            if "sort=createdAt" in url and "text-to-video" in url:
                return [_model("shared", "2026-07-07T00:00:00Z")] + [
                    _model(f"latest-{i}", f"2026-07-{i + 1:02d}T00:00:00Z")
                    for i in range(14)
                ]
            if "sort=createdAt" in url:
                return [_model("shared", "2026-07-08T00:00:00Z"), _model("image-latest", "2026-08-01T00:00:00Z")]
            if "text-to-video" in url:
                return [_model("trend-shared", "2026-01-01T00:00:00Z")] + [
                    _model(f"trend-{i}", f"2026-01-{i + 1:02d}T00:00:00Z")
                    for i in range(14)
                ]
            return [_model("trend-shared", "2026-02-01T00:00:00Z"), _model("image-trend", "2026-02-02T00:00:00Z")]

        with mock.patch("ai_news.ai_news_tool.http_tool.http_json", side_effect=fake_http_json):
            models = ai_news_tool.fetch_hf_models()

        self.assertEqual(len(calls), 4)
        self.assertEqual([timeout for _, timeout in calls], [12, 12, 12, 12])
        self.assertEqual(len(models["latest"]), 12)
        self.assertEqual(len(models["trending"]), 12)
        self.assertEqual(models["latest"][0]["id"], "image-latest")
        self.assertEqual(len({m["id"] for m in models["latest"]}), 12)
        self.assertEqual(len({m["id"] for m in models["trending"]}), 12)
        self.assertEqual(models["latest"][0]["pipeline"], "image-to-video")
        self.assertIn("trend-shared", [m["id"] for m in models["trending"]])

    def test_fetch_hf_models_returns_empty_lists_on_fetch_failure(self):
        with mock.patch("ai_news.ai_news_tool.http_tool.http_json", side_effect=TimeoutError):
            self.assertEqual(ai_news_tool.fetch_hf_models(), {"latest": [], "trending": []})

    def test_get_ai_data_cache_contract_and_force_refresh(self):
        calls = []

        def fake_news():
            calls.append("news")
            return [{"title": str(len(calls))}]

        def fake_models():
            calls.append("models")
            return {"latest": [{"id": str(len(calls))}], "trending": []}

        with (
            mock.patch("ai_news.ai_news_tool.fetch_news", side_effect=fake_news),
            mock.patch("ai_news.ai_news_tool.fetch_hf_models", side_effect=fake_models),
        ):
            data, fetched_at = ai_news_tool.get_ai_data(False)
            data2, fetched_at2 = ai_news_tool.get_ai_data(False)
            data3, fetched_at3 = ai_news_tool.get_ai_data(True)

        self.assertEqual(data, data2)
        self.assertEqual(fetched_at, fetched_at2)
        self.assertNotEqual(data2, data3)
        self.assertNotEqual(fetched_at2, fetched_at3)
        self.assertEqual(calls.count("news"), 2)
        self.assertEqual(calls.count("models"), 2)
        self.assertIn(("ai",), cache_tool._cache)

    def test_fetch_oembed_routes_supported_hosts(self):
        captured = []

        def fake_http_json(url, timeout=15):
            captured.append((url, timeout))
            return {"title": "Title", "author_name": "Author", "thumbnail_url": "https://img.test/t.jpg"}

        with mock.patch("ai_news.ai_news_tool.http_tool.http_json", side_effect=fake_http_json):
            tiktok = ai_news_tool.fetch_oembed("https://www.tiktok.com/@x/video/1")
            youtube = ai_news_tool.fetch_oembed("https://youtu.be/abc")

        self.assertEqual(tiktok, {"ok": True, "title": "Title", "author": "Author", "thumbnail": "https://img.test/t.jpg"})
        self.assertEqual(youtube["ok"], True)
        self.assertEqual(captured[0], ("https://www.tiktok.com/oembed?url=https%3A%2F%2Fwww.tiktok.com%2F%40x%2Fvideo%2F1", 10))
        self.assertEqual(captured[1], ("https://www.youtube.com/oembed?format=json&url=https%3A%2F%2Fyoutu.be%2Fabc", 10))

    def test_fetch_oembed_unsupported_and_fetch_failed(self):
        self.assertEqual(
            ai_news_tool.fetch_oembed("https://example.com/x"),
            {"ok": False, "reason": "unsupported"},
        )
        with mock.patch("ai_news.ai_news_tool.http_tool.http_json", side_effect=TimeoutError):
            self.assertEqual(
                ai_news_tool.fetch_oembed("https://www.youtube.com/watch?v=abc"),
                {"ok": False, "reason": "fetch_failed"},
            )


if __name__ == "__main__":
    unittest.main()
