"""Date-course radar built from the existing unauthenticated trend/video sources."""

from concurrent.futures import ThreadPoolExecutor

from shared import cache_tool
from trends import trends_tool
from youtube import youtube_tool

DATE_QUERIES_BY_COUNTRY = {
    "KR": (
        ("서울 데이트 코스", ("서울", "코스")),
        ("주말 데이트 추천", ("주말", "추천")),
        ("실내 데이트", ("실내", "비오는날")),
        ("전시 데이트", ("전시", "문화")),
        ("맛집 데이트", ("맛집", "식사")),
    ),
    "US": (
        ("date ideas", ("date ideas", "romantic")),
        ("weekend date ideas", ("weekend", "date ideas")),
        ("indoor date ideas", ("indoor", "date ideas")),
        ("romantic restaurants", ("restaurant", "romantic")),
        ("museum date", ("museum", "culture")),
    ),
    "JP": (
        ("デート スポット", ("デート", "スポット")),
        ("週末 デート", ("週末", "デート")),
        ("室内デート", ("室内", "デート")),
        ("美術館 デート", ("美術館", "文化")),
        ("ディナー デート", ("ディナー", "食事")),
    ),
}
TREND_ACTIVITY_KEYWORDS = (
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
TREND_DATE_CONTEXT_KEYWORDS = ("커플", "연인", "로맨틱", "기념일", "소개팅", "둘이")
MAX_IDEAS = 30
NEGATIVE_CACHE_TTL = 120


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


def _trend_idea(trend: dict) -> dict:
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
        "score": int(trend.get("trafficValue") or 0),
        "tags": ["급상승", "관심사"],
        "query": keyword,
    }


def _is_date_related(keyword: str) -> bool:
    compact = (keyword or "").replace(" ", "").casefold()
    if "데이트" in compact.replace("업데이트", ""):
        return True
    has_activity = any(word.casefold() in compact for word in TREND_ACTIVITY_KEYWORDS)
    has_date_context = any(
        word.casefold() in compact for word in TREND_DATE_CONTEXT_KEYWORDS
    )
    return has_activity and has_date_context


def _interleave_ideas(video_ideas: list, trend_ideas: list) -> list:
    ranked_videos = sorted(
        video_ideas, key=lambda item: item.get("score") or 0, reverse=True
    )
    ranked_trends = sorted(
        trend_ideas, key=lambda item: item.get("score") or 0, reverse=True
    )
    ideas = []
    for rank in range(max(len(ranked_videos), len(ranked_trends))):
        if rank < len(ranked_videos):
            ideas.append(ranked_videos[rank])
        if rank < len(ranked_trends):
            ideas.append(ranked_trends[rank])
    return ideas


def _fetch_date_radar(country: str):
    video_ideas = []
    trend_ideas = []
    errors = []
    seen = set()
    queries = DATE_QUERIES_BY_COUNTRY[country]

    worker_count = len(queries) + (1 if country == "KR" else 0)
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        video_futures = []
        for query, tags in queries:
            future = pool.submit(
                youtube_tool.merge_yt_searches, [query], "week", False, country
            )
            video_futures.append((query, tags, future))
        trend_future = (
            pool.submit(trends_tool.fetch_trends, country) if country == "KR" else None
        )

        for query, tags, future in video_futures:
            try:
                videos = future.result()[:6]
            except Exception as exc:
                errors.append(
                    {"kind": "youtube", "query": query, "error": exc.__class__.__name__}
                )
                continue
            for rank, video in enumerate(videos, 1):
                idea = _video_idea(video, query, tags, rank)
                if idea["url"] in seen or not video.get("id"):
                    continue
                seen.add(idea["url"])
                video_ideas.append(idea)

        if not video_ideas and not any(error["kind"] == "youtube" for error in errors):
            errors.append({"kind": "youtube", "error": "EmptyResult"})

        if trend_future is not None:
            try:
                trends, trend_errors = trend_future.result()
            except Exception as exc:
                trends = []
                trend_errors = [{"country": country, "kind": exc.__class__.__name__}]
            for error in trend_errors or []:
                detail = dict(error)
                error_name = detail.pop("kind", "UnknownError")
                errors.append({"kind": "trends", "error": error_name, **detail})
        else:
            trends = []

        for trend in trends:
            if not _is_date_related(trend.get("keyword", "")):
                continue
            idea = _trend_idea(trend)
            if idea["id"] in seen:
                continue
            seen.add(idea["id"])
            trend_ideas.append(idea)

    ideas = _interleave_ideas(video_ideas, trend_ideas)
    briefing = [
        "오늘/이번 주 데이트 코스 후보를 영상 조회수와 검색 급상승 신호로 자동 정렬했습니다.",
        "실내·전시·맛집·주말 코스를 섞어 날씨나 상황에 맞게 바로 고를 수 있습니다.",
    ]
    return {"ideas": ideas[:MAX_IDEAS], "briefing": briefing, "errors": errors}


def get_date_radar(country: str = "KR", force: bool = False):
    country = _normalize_country(country)

    def fetch():
        return _fetch_date_radar(country)

    def ttl_for_outcome(data):
        return NEGATIVE_CACHE_TTL if not data.get("ideas") and data.get("errors") else None

    cache_key = ("date_radar", country)
    data, fetched_at = cache_tool.cached(cache_key, force, fetch, ttl=ttl_for_outcome)
    return data, fetched_at, cache_tool.ttl_for(cache_key)
