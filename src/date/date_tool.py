"""Date-course radar built from the existing unauthenticated trend/video sources."""

from shared import cache_tool
from trends import trends_tool
from youtube import youtube_tool

DATE_QUERIES = (
    ("서울 데이트 코스", ("서울", "코스")),
    ("주말 데이트 추천", ("주말", "추천")),
    ("실내 데이트", ("실내", "비오는날")),
    ("전시 데이트", ("전시", "문화")),
    ("맛집 데이트", ("맛집", "식사")),
)
DATE_KEYWORDS = (
    "데이트",
    "전시",
    "팝업",
    "맛집",
    "카페",
    "축제",
    "공연",
    "여행",
    "핫플",
    "나들이",
)
MAX_IDEAS = 30


def _normalize_country(country: str) -> str:
    country = (country or "KR").upper()
    return country if country in youtube_tool.COUNTRY_LOCALE else "KR"


def _score_video(video: dict) -> int:
    return int(video.get("views") or 0)


def _video_idea(video: dict, query: str, tags: tuple, rank: int) -> dict:
    return {
        "id": "yt:" + (video.get("id") or query + str(rank)),
        "source": "YouTube",
        "type": "video",
        "title": video.get("title") or query,
        "url": "https://www.youtube.com/watch?v=" + (video.get("id") or ""),
        "thumbnail": video.get("thumbnail") or "",
        "account": video.get("channel") or "",
        "published": video.get("published") or "",
        "metric": video.get("viewsText") or "",
        "score": _score_video(video),
        "tags": list(tags),
        "query": query,
    }


def _trend_idea(trend: dict, rank: int) -> dict:
    keyword = trend.get("keyword") or "데이트 트렌드"
    news = trend.get("news") or []
    first_news = news[0] if news else {}
    return {
        "id": "trend:" + keyword,
        "source": "Google Trends",
        "type": "trend",
        "title": keyword,
        "url": first_news.get("url") or "https://www.google.com/search?q=" + keyword,
        "thumbnail": trend.get("picture") or first_news.get("picture") or "",
        "account": first_news.get("source") or "",
        "published": "",
        "metric": trend.get("traffic") or "",
        "score": int(trend.get("trafficValue") or 0) + max(0, 1000000 - rank),
        "tags": ["급상승", "관심사"],
        "query": keyword,
    }


def _is_date_related(keyword: str) -> bool:
    compact = (keyword or "").replace(" ", "").casefold()
    return any(word.casefold() in compact for word in DATE_KEYWORDS)


def _fetch_date_radar(country: str):
    ideas = []
    seen = set()

    for query, tags in DATE_QUERIES:
        videos = youtube_tool.merge_yt_searches([query], "week", False, country)[:6]
        for rank, video in enumerate(videos, 1):
            idea = _video_idea(video, query, tags, rank)
            if idea["url"] in seen or not video.get("id"):
                continue
            seen.add(idea["url"])
            ideas.append(idea)

    if country == "KR":
        trends, errors = trends_tool.fetch_trends(country)
        del errors
        for rank, trend in enumerate(trends, 1):
            if not _is_date_related(trend.get("keyword", "")):
                continue
            idea = _trend_idea(trend, rank)
            if idea["id"] in seen:
                continue
            seen.add(idea["id"])
            ideas.append(idea)

    ideas.sort(key=lambda item: item.get("score") or 0, reverse=True)
    briefing = [
        "오늘/이번 주 데이트 코스 후보를 영상 조회수와 검색 급상승 신호로 자동 정렬했습니다.",
        "실내·전시·맛집·주말 코스를 섞어 날씨나 상황에 맞게 바로 고를 수 있습니다.",
    ]
    return {"ideas": ideas[:MAX_IDEAS], "briefing": briefing}


def get_date_radar(country: str = "KR", force: bool = False):
    country = _normalize_country(country)

    def fetch():
        return _fetch_date_radar(country)

    data, fetched_at = cache_tool.cached(("date_radar", country), force, fetch)
    return data, fetched_at, cache_tool.ttl_for(("date_radar", country))
