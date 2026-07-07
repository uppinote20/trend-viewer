import unittest
from unittest import mock

import main


class MainApiCacheMetadataTest(unittest.TestCase):
    def setUp(self):
        self.handler = main.Handler.__new__(main.Handler)
        self.sent = []

        def capture(handler_self, code, body, content_type="application/json; charset=utf-8"):
            del handler_self, content_type
            self.sent.append((code, body))

        self.send_patch = mock.patch.object(main.Handler, "_send", capture)
        self.send_patch.start()

    def tearDown(self):
        self.send_patch.stop()

    def assert_cache_metadata(self, body, fetched_at=123.5):
        self.assertEqual(body["fetchedAt"], fetched_at)
        self.assertEqual(body["cacheTtl"], main.CACHE_TTL)

    def test_videos_payload_includes_cache_metadata(self):
        with mock.patch.object(main.youtube_tool, "get_videos", return_value=([{"id": "v"}], 123.5)):
            self.handler._handle_videos({})

        code, body = self.sent[-1]
        self.assertEqual(code, 200)
        self.assertEqual(body["videos"], [{"id": "v"}])
        self.assert_cache_metadata(body)

    def test_reels_payload_includes_cache_metadata(self):
        with mock.patch.object(main.reels_tool, "get_reels", return_value=([{"id": "r"}], ["openai"], 123.5)):
            self.handler._handle_reels({})

        code, body = self.sent[-1]
        self.assertEqual(code, 200)
        self.assertEqual(body["reels"], [{"id": "r"}])
        self.assertEqual(body["accounts"], ["openai"])
        self.assert_cache_metadata(body)

    def test_x_payload_includes_cache_metadata(self):
        with mock.patch.object(main.x_twitter_tool, "get_x_posts", return_value=([{"id": "x"}], ["OpenAI"], 123.5)):
            self.handler._handle_x({})

        code, body = self.sent[-1]
        self.assertEqual(code, 200)
        self.assertEqual(body["posts"], [{"id": "x"}])
        self.assertEqual(body["accounts"], ["OpenAI"])
        self.assert_cache_metadata(body)

    def test_threads_payload_includes_cache_metadata(self):
        with mock.patch.object(main.threads_tool, "get_threads_posts", return_value=([{"id": "th"}], ["openai"], 123.5)):
            self.handler._handle_threads({})

        code, body = self.sent[-1]
        self.assertEqual(code, 200)
        self.assertEqual(body["posts"], [{"id": "th"}])
        self.assertEqual(body["accounts"], ["openai"])
        self.assert_cache_metadata(body)

    def test_tiktok_payload_includes_cache_metadata(self):
        with mock.patch.object(main.tiktok_tool, "get_tiktok", return_value=([{"id": "tt"}], ["openai"], 123.5)):
            self.handler._handle_tiktok({})

        code, body = self.sent[-1]
        self.assertEqual(code, 200)
        self.assertEqual(body["posts"], [{"id": "tt"}])
        self.assertEqual(body["accounts"], ["openai"])
        self.assert_cache_metadata(body)

    def test_ai_payload_includes_cache_metadata(self):
        data = {"news": [{"title": "n"}], "models": {"latest": []}}
        with mock.patch.object(main.ai_news_tool, "get_ai_data", return_value=(data, 123.5)):
            self.handler._handle_ai({})

        code, body = self.sent[-1]
        self.assertEqual(code, 200)
        self.assertEqual(body["news"], [{"title": "n"}])
        self.assertEqual(body["models"], {"latest": []})
        self.assert_cache_metadata(body)


if __name__ == "__main__":
    unittest.main()
