"""Instagram Reels helpers ported from the upstream stdlib server."""

import json
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

from shared import accounts_tool, cache_tool, http_tool


NEGATIVE_CACHE_TTL = 120
IG_APP_ID = "936619743392459"
DEFAULT_IG_ACCOUNTS = [
    "openai",
    "runwayapp",
    "pika_labs",
    "lumalabsai",
    "midjourney",
    "klingai_official",
    "heygen_official",
    "higgsfield.ai",
    "googledeepmind",
]


def register():
    accounts_tool.register_source("reels", "reels_accounts.json", DEFAULT_IG_ACCOUNTS)


def fetch_ig_reels(username: str):
    url = (
        "https://www.instagram.com/api/v1/users/web_profile_info/?username="
        + quote(username)
    )
    try:
        data = http_tool.http_json(url, headers={"x-ig-app-id": IG_APP_ID}, timeout=12)
    except urllib.error.HTTPError as exc:
        return [], {"account": username, "kind": "http", "code": exc.code}
    except TimeoutError:
        return [], {"account": username, "kind": "timeout", "code": None}
    except urllib.error.URLError as exc:
        kind = "timeout" if isinstance(exc.reason, TimeoutError) else "http"
        return [], {"account": username, "kind": kind, "code": None}
    except json.JSONDecodeError:
        return [], {"account": username, "kind": "parse", "code": None}
    except OSError:
        return [], {"account": username, "kind": "http", "code": None}
    user = (data.get("data") or {}).get("user") or {}
    reels = []
    for edge in (user.get("edge_owner_to_timeline_media") or {}).get("edges", []):
        n = edge.get("node", {})
        if not n.get("is_video"):
            continue
        caps = (n.get("edge_media_to_caption") or {}).get("edges") or []
        title = caps[0]["node"]["text"].split("\n")[0][:120] if caps else ""
        reels.append(
            {
                "account": username,
                "title": title or "(설명 없음)",
                "views": n.get("video_view_count") or 0,
                "likes": (n.get("edge_liked_by") or {}).get("count", 0),
                "comments": (n.get("edge_media_to_comment") or {}).get("count", 0),
                "thumbnail": n.get("thumbnail_src") or "",
                "url": "https://www.instagram.com/reel/%s/" % n.get("shortcode", ""),
                "takenAt": n.get("taken_at_timestamp") or 0,
            }
        )
    return reels, None


def get_reels(force: bool):
    source = accounts_tool.get_source("reels")
    accounts = accounts_tool.load_accounts(source["path"], source["defaults"])
    cache_key = ("reels", tuple(accounts))

    def fetch():
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = pool.map(fetch_ig_reels, accounts)
        merged = []
        errors = []
        for items, error in results:
            merged.extend(items)
            if error:
                errors.append(error)
        merged.sort(key=lambda r: r["views"], reverse=True)
        return merged, errors

    def ttl_for_outcome(outcome):
        reels, errors = outcome
        return NEGATIVE_CACHE_TTL if not reels and errors else None

    (reels, errors), fetched_at = cache_tool.cached(cache_key, force, fetch, ttl=ttl_for_outcome)
    return reels, accounts, fetched_at, errors, cache_tool.ttl_for(cache_key)
