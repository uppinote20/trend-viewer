"""AI news and model helpers ported from the upstream stdlib server."""

import email.utils
import json
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlparse

from shared import cache_tool, http_tool


NEWS_FEEDS = [
    (
        "국내",
        "https://news.google.com/rss/search?q="
        + quote('AI 영상 생성 OR "AI 비디오" OR 영상생성모델')
        + "&hl=ko&gl=KR&ceid=KR:ko",
    ),
    (
        "해외",
        "https://news.google.com/rss/search?q="
        + quote('"AI video" model OR Sora OR Runway OR Kling OR Veo')
        + "&hl=en-US&gl=US&ceid=US:en",
    ),
]

HF_PIPELINES = ["text-to-video", "image-to-video"]


def fetch_news():
    def one(feed):
        label, url = feed
        try:
            _, body = http_tool.http_get(url, timeout=12)
            root = ET.fromstring(body)
        except Exception:
            return []
        items = []
        for item in root.iter("item"):
            title = item.findtext("title") or ""
            source = item.findtext("source") or ""
            pub = item.findtext("pubDate") or ""
            try:
                ts = email.utils.parsedate_to_datetime(pub).timestamp()
            except (TypeError, ValueError):
                ts = 0
            items.append(
                {
                    "region": label,
                    "title": title,
                    "source": source,
                    "link": item.findtext("link") or "",
                    "ts": ts,
                }
            )
        return items[:25]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = pool.map(one, NEWS_FEEDS)
    merged = [n for chunk in results for n in chunk]
    merged.sort(key=lambda n: n["ts"], reverse=True)
    return merged[:40]


def fetch_hf_models():
    def one(args):
        pipeline, sort = args
        url = (
            "https://huggingface.co/api/models?pipeline_tag=%s&sort=%s"
            "&direction=-1&limit=12" % (pipeline, sort)
        )
        try:
            data = http_tool.http_json(url, timeout=12)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return []
        return [
            {
                "id": m.get("id", ""),
                "likes": m.get("likes", 0),
                "downloads": m.get("downloads", 0),
                "pipeline": pipeline,
                "createdAt": m.get("createdAt", ""),
            }
            for m in data
        ]

    jobs = [(p, s) for p in HF_PIPELINES for s in ("createdAt", "trendingScore")]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(one, jobs))

    def dedupe(lists):
        seen, out = set(), []
        for chunk in lists:
            for m in chunk:
                if m["id"] not in seen:
                    seen.add(m["id"])
                    out.append(m)
        return out

    latest = dedupe(results[0::2])
    latest.sort(key=lambda m: m["createdAt"], reverse=True)
    trending = dedupe(results[1::2])
    return {"latest": latest[:12], "trending": trending[:12]}


def get_ai_data(force: bool):
    def fetch():
        with ThreadPoolExecutor(max_workers=2) as pool:
            news_f = pool.submit(fetch_news)
            models_f = pool.submit(fetch_hf_models)
            return {"news": news_f.result(), "models": models_f.result()}

    return cache_tool.cached(("ai",), force, fetch)


def fetch_oembed(url: str):
    host = urlparse(url).netloc.lower()
    if "tiktok.com" in host:
        endpoint = "https://www.tiktok.com/oembed?url=" + quote(url, safe="")
    elif "youtube.com" in host or "youtu.be" in host:
        endpoint = "https://www.youtube.com/oembed?format=json&url=" + quote(url, safe="")
    else:
        return {"ok": False, "reason": "unsupported"}
    try:
        data = http_tool.http_json(endpoint, timeout=10)
        return {
            "ok": True,
            "title": data.get("title", ""),
            "author": data.get("author_name", ""),
            "thumbnail": data.get("thumbnail_url", ""),
        }
    except Exception:
        return {"ok": False, "reason": "fetch_failed"}
