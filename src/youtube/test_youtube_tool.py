import json
import unittest
from unittest import mock

from shared import cache_tool
from youtube import youtube_tool


class _Response:
    def __init__(self, body=b"{}"):
        self.headers = {"Content-Type": "application/json"}
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body


def _video(video_id, title, views, published="1시간 전", thumb="https://img.test/2.jpg"):
    return {
        "videoRenderer": {
            "videoId": video_id,
            "title": {"runs": [{"text": title}]},
            "ownerText": {"runs": [{"text": "채널"}]},
            "viewCountText": {"simpleText": views},
            "lengthText": {"simpleText": "1:23"},
            "publishedTimeText": {"simpleText": published},
            "thumbnail": {"thumbnails": [{"url": "https://img.test/1.jpg"}, {"url": thumb}]},
        }
    }


class YoutubeToolTest(unittest.TestCase):
    def setUp(self):
        cache_tool._cache.clear()

    def tearDown(self):
        cache_tool._cache.clear()

    def test_extract_videos_nested_tree(self):
        data = {
            "contents": [
                {"section": {"items": [_video("a", "첫 영상", "조회수 12,345회")]}},
                _video("b", "Second Video", "1,000 views", "2시간 전"),
            ]
        }
        out = []

        youtube_tool.extract_videos(data, out)

        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["id"], "a")
        self.assertEqual(out[0]["title"], "첫 영상")
        self.assertEqual(out[0]["channel"], "채널")
        self.assertEqual(out[0]["views"], 12345)
        self.assertEqual(out[0]["viewsText"], "조회수 12,345회")
        self.assertEqual(out[0]["length"], "1:23")
        self.assertEqual(out[0]["published"], "1시간 전")
        self.assertEqual(out[0]["thumbnail"], "https://img.test/2.jpg")
        self.assertEqual(out[1]["views"], 1000)

    def test_within_period_filters_excluded_phrases(self):
        self.assertTrue(youtube_tool.within_period("", "day"))
        self.assertTrue(youtube_tool.within_period("3시간 전", "day"))
        self.assertFalse(youtube_tool.within_period("1일 전", "day"))
        self.assertTrue(youtube_tool.within_period("3일 전", "week"))
        self.assertFalse(youtube_tool.within_period("2주 전", "week"))
        self.assertTrue(youtube_tool.within_period("2주 전", "month"))
        self.assertFalse(youtube_tool.within_period("1개월 전", "month"))

    def test_build_search_params_exact_base64(self):
        expected = {
            ("day", False): "CAMSBAgCEAE=",
            ("day", True): "CAMSBggCEAEYAQ==",
            ("week", False): "CAMSBAgDEAE=",
            ("week", True): "CAMSBggDEAEYAQ==",
            ("month", False): "CAMSBAgEEAE=",
            ("month", True): "CAMSBggEEAEYAQ==",
        }
        for (period, shorts), value in expected.items():
            with self.subTest(period=period, shorts=shorts):
                self.assertEqual(youtube_tool.build_search_params(period, shorts), value)

    def test_yt_search_payload_dedupes_and_filters_period(self):
        captured = {}
        body = json.dumps(
            {
                "items": [
                    _video("new", "New", "조회수 2,000회", "1시간 전"),
                    _video("new", "Duplicate", "조회수 9,999회", "2시간 전"),
                    _video("old", "Old", "조회수 5,000회", "3일 전"),
                ]
            }
        ).encode()

        def fake_urlopen(req, timeout):
            captured["req"] = req
            captured["timeout"] = timeout
            return _Response(body)

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            videos = youtube_tool.yt_search("테스트", "day", True)

        payload = json.loads(captured["req"].data.decode())
        self.assertEqual(captured["req"].full_url, "https://www.youtube.com/youtubei/v1/search")
        self.assertEqual(captured["timeout"], 15)
        self.assertEqual(payload["context"]["client"]["clientName"], "WEB")
        self.assertEqual(payload["context"]["client"]["clientVersion"], "2.20250624.01.00")
        self.assertEqual(payload["context"]["client"]["hl"], "ko")
        self.assertEqual(payload["context"]["client"]["gl"], "KR")
        self.assertEqual(payload["query"], "테스트")
        self.assertEqual(payload["params"], "CAMSBggCEAEYAQ==")
        self.assertEqual([v["id"] for v in videos], ["new"])

    def test_yt_like_count_regex_korean_english_and_failure(self):
        bodies = [
            b'..."like this video along with 1,234 other"...',
            "다른 사용자 5,678명".encode(),
            b"no like count",
        ]

        def fake_urlopen(req, timeout):
            del req, timeout
            return _Response(bodies.pop(0))

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            self.assertEqual(youtube_tool.yt_like_count("a"), 1235)
            self.assertEqual(youtube_tool.yt_like_count("b"), 5679)
            self.assertEqual(youtube_tool.yt_like_count("c"), 0)

    def test_get_videos_query_selection_and_force_cache_contract(self):
        calls = []

        def fake_merge(queries, period, shorts):
            calls.append((list(queries), period, shorts))
            return [{"id": str(len(calls)), "views": len(calls)}]

        with mock.patch("youtube.youtube_tool.merge_yt_searches", side_effect=fake_merge):
            videos, fetched_at = youtube_tool.get_videos("전체", "week", False, False)
            videos2, fetched_at2 = youtube_tool.get_videos("전체", "week", False, False)
            videos3, fetched_at3 = youtube_tool.get_videos("전체", "week", False, True)
            ai_videos, _ = youtube_tool.get_videos("AI", "day", True, True)
            query_videos, _ = youtube_tool.get_videos("먹방", "month", False, True, query="custom")

        self.assertEqual(calls[0], ([youtube_tool.CATEGORIES[c] for c in youtube_tool.ALL_MERGE], "week", False))
        self.assertEqual(videos, videos2)
        self.assertEqual(fetched_at, fetched_at2)
        self.assertNotEqual(videos2, videos3)
        self.assertNotEqual(fetched_at2, fetched_at3)
        self.assertEqual(calls[2], (youtube_tool.AI_YT_QUERIES, "day", True))
        self.assertEqual(calls[3], (["custom"], "month", False))
        self.assertEqual(ai_videos[0]["id"], "3")
        self.assertEqual(query_videos[0]["id"], "4")
        self.assertEqual(len(calls), 4)


if __name__ == "__main__":
    unittest.main()
