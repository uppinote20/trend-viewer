import unittest
from unittest import mock

from date import date_tool
from shared import cache_tool


class DateToolTest(unittest.TestCase):
    def setUp(self):
        cache_tool._cache.clear()

    def tearDown(self):
        cache_tool._cache.clear()

    def test_date_radar_merges_video_and_trend_ideas(self):
        def fake_merge(queries, period, shorts, country):
            query = queries[0]
            return [
                {
                    "id": "vid-" + query,
                    "title": query + " 영상",
                    "channel": "dateclub",
                    "views": 1000,
                    "viewsText": "1천회",
                    "published": "1일 전",
                    "thumbnail": "https://img.test/" + query + ".jpg",
                }
            ]

        trends = [
            {
                "keyword": "서울 전시 데이트",
                "traffic": "20,000+",
                "trafficValue": 20000,
                "picture": "https://img.test/trend.jpg",
                "news": [{"url": "https://news.test/date", "source": "News"}],
            },
            {"keyword": "정치 뉴스", "traffic": "50,000+", "trafficValue": 50000, "news": []},
        ]

        with (
            mock.patch("date.date_tool.youtube_tool.merge_yt_searches", side_effect=fake_merge),
            mock.patch("date.date_tool.trends_tool.fetch_trends", return_value=(trends, [])),
        ):
            data, fetched_at, cache_ttl = date_tool.get_date_radar("KR")

        self.assertGreater(fetched_at, 0)
        self.assertGreater(cache_ttl, 0)
        self.assertEqual(len(data["briefing"]), 2)
        self.assertEqual(len(data["ideas"]), 6)
        self.assertTrue(any(item["type"] == "trend" and item["title"] == "서울 전시 데이트" for item in data["ideas"]))
        self.assertFalse(any(item["title"] == "정치 뉴스" for item in data["ideas"]))
        self.assertTrue(all(item["url"].startswith("https://") for item in data["ideas"]))

    def test_unknown_country_falls_back_to_kr_and_uses_cache(self):
        calls = []

        def fake_fetch(country):
            calls.append(country)
            return {"ideas": [], "briefing": [country]}

        with mock.patch("date.date_tool._fetch_date_radar", side_effect=fake_fetch):
            first, first_ts, _ = date_tool.get_date_radar("ca")
            second, second_ts, _ = date_tool.get_date_radar("KR")

        self.assertEqual(first, {"ideas": [], "briefing": ["KR"]})
        self.assertEqual(second, first)
        self.assertEqual(second_ts, first_ts)
        self.assertEqual(calls, ["KR"])
        self.assertIn(("date_radar", "KR"), cache_tool._cache)


if __name__ == "__main__":
    unittest.main()
