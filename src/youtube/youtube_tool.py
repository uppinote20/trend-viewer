"""YouTube search helpers ported from the upstream stdlib server."""

import base64
import json
import re
import urllib.error
from concurrent.futures import ThreadPoolExecutor

from shared import cache_tool, http_tool


CATEGORIES = {
    "먹방": "먹방",
    "뷰티/패션": "뷰티 메이크업 패션",
    "브이로그": "브이로그",
    "예능/코미디": "예능 웃긴 영상",
    "영화/드라마": "영화 드라마 리뷰",
    "테크/IT": "테크 리뷰",
    "지식/교육": "지식 교양",
    "여행": "여행",
    "동물": "강아지 고양이",
}

ALL_MERGE = ["먹방", "브이로그", "예능/코미디", "뷰티/패션", "영화/드라마", "여행"]

PERIOD_CODE = {"day": 2, "week": 3, "month": 4}

PERIOD_EXCLUDE = {
    "day": ("일 전", "주 전", "개월 전", "년 전"),
    "week": ("주 전", "개월 전", "년 전"),
    "month": ("개월 전", "년 전"),
}

AI_YT_QUERIES = ["AI 영상 제작", "AI 영상 생성", "sora ai video", "runway kling veo"]


def within_period(published: str, period: str) -> bool:
    if not published:
        return True
    return not any(word in published for word in PERIOD_EXCLUDE.get(period, ()))


def build_search_params(period: str, shorts: bool = False) -> str:
    filters = bytes([0x08, PERIOD_CODE.get(period, 3), 0x10, 0x01])
    if shorts:
        filters += bytes([0x18, 0x01])
    raw = bytes([0x08, 0x03, 0x12, len(filters)]) + filters
    return base64.urlsafe_b64encode(raw).decode()


def extract_videos(node, out):
    if isinstance(node, dict):
        if "videoRenderer" in node:
            v = node["videoRenderer"]
            title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))
            views_text = v.get("viewCountText", {}).get("simpleText", "")
            thumbs = v.get("thumbnail", {}).get("thumbnails", [])
            out.append(
                {
                    "id": v.get("videoId", ""),
                    "title": title,
                    "channel": "".join(
                        r.get("text", "") for r in v.get("ownerText", {}).get("runs", [])
                    ),
                    "views": http_tool.parse_view_count(views_text),
                    "viewsText": views_text,
                    "length": v.get("lengthText", {}).get("simpleText", ""),
                    "published": v.get("publishedTimeText", {}).get("simpleText", ""),
                    "thumbnail": thumbs[-1]["url"] if thumbs else "",
                }
            )
        for value in node.values():
            extract_videos(value, out)
    elif isinstance(node, list):
        for item in node:
            extract_videos(item, out)


def yt_search(query: str, period: str, shorts: bool):
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20250624.01.00",
                "hl": "ko",
                "gl": "KR",
            }
        },
        "query": query,
        "params": build_search_params(period, shorts),
    }
    try:
        data = http_tool.http_json("https://www.youtube.com/youtubei/v1/search", payload)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    videos = []
    extract_videos(data, videos)
    seen, unique = set(), []
    for v in videos:
        if v["id"] and v["id"] not in seen and within_period(v["published"], period):
            seen.add(v["id"])
            unique.append(v)
    return unique


def yt_like_count(video_id: str):
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20250624.01.00",
                "hl": "ko",
                "gl": "KR",
            }
        },
        "videoId": video_id,
    }
    try:
        _, body = http_tool.http_get(
            "https://www.youtube.com/youtubei/v1/next", payload=payload, timeout=10
        )
        s = body.decode("utf-8", "ignore")
        m = re.search(r"다른 사용자 ([0-9,]+)명", s) or re.search(
            r"along with ([0-9,]+) other", s
        )
        return int(m.group(1).replace(",", "")) + 1 if m else 0
    except Exception:
        return 0


def enrich_likes(videos, limit=45):
    todo = [v for v in videos[:limit] if not v.get("likes")]
    if not todo:
        return videos
    with ThreadPoolExecutor(max_workers=12) as pool:
        counts = pool.map(lambda v: yt_like_count(v["id"]), todo)
    for v, c in zip(todo, counts):
        v["likes"] = c
    return videos


def merge_yt_searches(queries, period, shorts):
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = pool.map(lambda q: yt_search(q, period, shorts), queries)
    merged, seen = [], set()
    for chunk in results:
        for v in chunk:
            if v["id"] not in seen:
                seen.add(v["id"])
                merged.append(v)
    merged.sort(key=lambda v: v["views"], reverse=True)
    return merged


def get_videos(category: str, period: str, shorts: bool, force: bool, enrich: bool = False, query: str = ""):
    def fetch():
        if query:
            queries = [query]
        elif category == "전체":
            queries = [CATEGORIES[c] for c in ALL_MERGE]
        elif category == "AI":
            queries = AI_YT_QUERIES
        else:
            queries = [CATEGORIES.get(category, category)]
        vids = merge_yt_searches(queries, period, shorts)
        if enrich:
            enrich_likes(vids)
        return vids

    return cache_tool.cached(("yt", query or category, period, shorts, enrich), force, fetch)
