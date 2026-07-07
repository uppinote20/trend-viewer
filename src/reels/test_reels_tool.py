import json
import os
import tempfile
import unittest
from unittest import mock

from reels import reels_tool
from shared import accounts_tool, cache_tool


def _edge(shortcode, is_video=True, caption="caption", views=1):
    return {
        "node": {
            "is_video": is_video,
            "edge_media_to_caption": {"edges": [{"node": {"text": caption}}]},
            "video_view_count": views,
            "edge_liked_by": {"count": 7},
            "edge_media_to_comment": {"count": 3},
            "thumbnail_src": "https://img.test/thumb.jpg",
            "shortcode": shortcode,
            "taken_at_timestamp": 123,
        }
    }


class ReelsToolTest(unittest.TestCase):
    def setUp(self):
        accounts_tool._sources.clear()
        cache_tool._cache.clear()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.config_patch = mock.patch("shared.accounts_tool.settings.CONFIG_DIR", self.tmpdir.name)
        self.config_patch.start()
        reels_tool.register()

    def tearDown(self):
        self.config_patch.stop()
        self.tmpdir.cleanup()
        accounts_tool._sources.clear()
        cache_tool._cache.clear()

    def test_fetch_ig_reels_parses_web_profile_info_videos_only(self):
        long_first_line = "a" * 130
        fixture = {
            "data": {
                "user": {
                    "edge_owner_to_timeline_media": {
                        "edges": [
                            _edge("abc123", True, long_first_line + "\nsecond line", 42),
                            _edge("photo", False, "not a video", 999),
                        ]
                    }
                }
            }
        }
        captured = {}

        def fake_http_json(url, headers=None, timeout=15):
            captured["url"] = url
            captured["headers"] = headers
            captured["timeout"] = timeout
            return fixture

        with mock.patch("reels.reels_tool.http_tool.http_json", side_effect=fake_http_json):
            reels, error = reels_tool.fetch_ig_reels("open ai")

        self.assertEqual(captured["url"], "https://www.instagram.com/api/v1/users/web_profile_info/?username=open%20ai")
        self.assertEqual(captured["headers"], {"x-ig-app-id": reels_tool.IG_APP_ID})
        self.assertEqual(captured["timeout"], 12)
        self.assertIsNone(error)
        self.assertEqual(len(reels), 1)
        self.assertEqual(reels[0]["account"], "open ai")
        self.assertEqual(reels[0]["title"], "a" * 120)
        self.assertEqual(reels[0]["views"], 42)
        self.assertEqual(reels[0]["likes"], 7)
        self.assertEqual(reels[0]["comments"], 3)
        self.assertEqual(reels[0]["url"], "https://www.instagram.com/reel/abc123/")

    def test_fetch_ig_reels_exception_fallback(self):
        with mock.patch("reels.reels_tool.http_tool.http_json", side_effect=TimeoutError):
            reels, error = reels_tool.fetch_ig_reels("openai")

        self.assertEqual(reels, [])
        self.assertEqual(error, {"account": "openai", "kind": "timeout", "code": None})

    def test_get_reels_sorts_and_cache_key_includes_accounts_tuple(self):
        path = accounts_tool.get_source("reels")["path"]
        with open(path, "w") as f:
            json.dump(["b", "a"], f)

        calls = []

        def fake_fetch(account):
            calls.append(account)
            return [{"id": account, "views": 10 if account == "a" else 3}], None

        with mock.patch("reels.reels_tool.fetch_ig_reels", side_effect=fake_fetch):
            reels, accounts, fetched_at, errors, cache_ttl = reels_tool.get_reels(False)
            reels2, accounts2, fetched_at2, errors2, cache_ttl2 = reels_tool.get_reels(False)

        self.assertEqual(accounts, ["b", "a"])
        self.assertEqual(accounts2, ["b", "a"])
        self.assertEqual([r["id"] for r in reels], ["a", "b"])
        self.assertEqual(reels2, reels)
        self.assertEqual(errors, [])
        self.assertEqual(errors2, [])
        self.assertEqual(cache_ttl, 3600)
        self.assertEqual(cache_ttl2, 3600)
        self.assertEqual(fetched_at2, fetched_at)
        self.assertEqual(calls, ["b", "a"])
        self.assertIn(("reels", ("b", "a")), cache_tool._cache)

    def test_get_reels_negative_error_uses_short_cache_ttl(self):
        path = accounts_tool.get_source("reels")["path"]
        with open(path, "w") as f:
            json.dump(["openai"], f)

        def fake_fetch(account):
            return [], {"account": account, "kind": "http", "code": 401}

        with mock.patch("reels.reels_tool.fetch_ig_reels", side_effect=fake_fetch):
            reels, accounts, fetched_at, errors, cache_ttl = reels_tool.get_reels(False)

        self.assertEqual(reels, [])
        self.assertEqual(accounts, ["openai"])
        self.assertGreater(fetched_at, 0)
        self.assertEqual(errors, [{"account": "openai", "kind": "http", "code": 401}])
        self.assertEqual(cache_ttl, 120)


if __name__ == "__main__":
    unittest.main()
