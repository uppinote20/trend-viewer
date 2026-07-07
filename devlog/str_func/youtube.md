---
created: 2026-07-07
tags: [trend-viewer, YouTube, InnerTube, video-search, country-filter]
aliases: [youtube 모듈, 유튜브 검색, 쇼츠 검색, 국가별 유튜브]
---

# youtube 모듈 문서

이 문서는 `src/youtube/` 모듈을 다음 작업자가 바로 이어받을 수 있게 설명한다.
소스 코드를 먼저 읽고, 파일 경계와 함수 경계를 기준으로 책임을 적는다.
여기서 말하는 동기화는 코드 변경 뒤 이 문서와 테스트 관점도 함께 맞추는 일을 뜻한다.
외부 웹 검색 없이 로컬 소스와 포팅 계획 문서만 근거로 삼는다.

---

## File Tree

이 섹션은 실제 파일 수와 라인 수를 기준으로 모듈의 표면적을 보여준다.
라인 수가 달라지면 이 표도 같이 갱신한다.

| 파일 | 라인 수 | 역할 |
|---|---:|---|
| `src/youtube/__init__.py` | 3 | CATEGORIES와 get_videos 배럴 export |
| `src/youtube/youtube_tool.py` | 259 | 국가별 YouTube InnerTube 검색, 기간 필터, 좋아요 보강 |
| `src/youtube/test_youtube_tool.py` | 222 | YouTube 검색·국가·캐시 계약 단위 테스트 |

### 파일별 읽기 순서

1. `src/youtube/__init__.py`를 읽는다. 배럴 export 라인 수는 3줄이다.
2. `src/youtube/youtube_tool.py`를 읽는다. 국가별 InnerTube 검색과 좋아요 보강 라인 수는 259줄이다.
3. `src/youtube/test_youtube_tool.py`를 읽는다. 검색 계약 테스트 라인 수는 222줄이다.

### 파일 경계 메모

- `src/youtube/__init__.py`는 public export 표면만 맡는다.
- `src/youtube/youtube_tool.py`는 카테고리 query, 국가 locale, InnerTube payload, 결과 파싱, 좋아요 보강, 캐시 key를 모두 소유한다.
- `src/youtube/test_youtube_tool.py`는 base64 params, 기간 제외어, country fallback, cache key 분리까지 계약으로 묶는다.
- 라인 수가 바뀌면 File Tree와 문서 동기화 체크를 함께 갱신한다.

## Module Responsibility

`src/youtube/`는 유튜브 일반 영상과 쇼츠 검색을 담당한다.
카테고리와 기간 필터를 InnerTube search payload로 바꾸고, 결과 트리를 순회해 `videoRenderer` 목록을 평탄화한다.
좋아요순 정렬이 필요할 때는 next endpoint를 추가 호출해 일부 영상에 `likes` 값을 보강한다.
현재 구현은 한국·미국·일본 국가 선택을 지원하며, 국가값은 검색 locale과 카테고리 query, 기간 문자열 필터, 캐시 key까지 관통한다.

### 책임 경계

- `CATEGORIES`는 기본 한국어 카테고리 이름과 fallback query를 소유한다.
- `COUNTRY_LOCALE`은 `KR -> (ko, KR)`, `US -> (en, US)`, `JP -> (ja, JP)` InnerTube client locale을 소유한다.
- `COUNTRY_CATEGORIES`는 미국·일본에서 카테고리별 다중 검색어를 소유한다.
- `PERIOD_CODE`는 InnerTube 기간 filter base64 생성을 소유한다.
- `PERIOD_EXCLUDE_BY_LOCALE`은 `ko/en/ja` 발행일 문자열 후처리를 소유한다.
- `extract_videos`는 videoRenderer shape를 앱 내부 item shape로 바꾼다.
- 좋아요 보강은 `enrich=True`일 때만 실행되는 선택 경로다.

### 운영 관점

- `country`는 `/api/videos` query param으로 들어오며 유효하지 않으면 `KR`로 정규화된다.
- `yt_search`, `yt_like_count`, `enrich_likes`, `merge_yt_searches`, `get_videos` 모두 country 인자를 받는다.
- 캐시 key는 `("yt", country, query or category, period, shorts, enrich)`라서 국가별 결과가 섞이지 않는다.
- `get_videos` 결과는 main.py에서 `videos[:60]`으로 잘린다.
- 영상 item은 `id`, `title`, `channel`, `views`, `viewsText`, `length`, `published`, `thumbnail`, 선택적 `likes`를 가진다.

## Key Function Signatures

아래 함수명은 실제 소스의 공개 함수와 내부 헬퍼를 기준으로 한다.
테스트 헬퍼는 동작 계약을 보여주는 경우에만 포함한다.

### `_country_key(country: str) -> str`

- 입력을 대문자로 바꾸고 `COUNTRY_LOCALE`에 없으면 `KR`을 반환한다.
- 모든 country-aware 함수의 방어선이다.

### `_locale_for_country(country: str)`

- `_country_key`로 정규화한 뒤 InnerTube `hl`, `gl` 튜플을 반환한다.

### `_category_queries(category: str, country: str)`

- `전체`는 `ALL_MERGE` 카테고리를 펼쳐 query 목록으로 만든다.
- `AI`는 `AI_YT_QUERIES`를 반환한다.
- `US`와 `JP`는 `COUNTRY_CATEGORIES`의 다중 query를 우선 사용한다.
- fallback은 `CATEGORIES.get(category, category)`이다.

### `within_period(published: str, period: str, country: str = "KR") -> bool`

- 발행 문자열이 비어 있으면 통과시킨다.
- 국가 locale에 맞는 제외어 목록을 보고 day/week/month 결과를 후처리한다.
- 영어 week 필터는 `"week ago"`, `"weeks ago"`, month/year 계열을 제외하지만 `"days ago"`는 제외하지 않는다.
- 한국어는 `일 전/주 전/개월 전/년 전`, 일본어는 `日前/週間前/か月前/年前` 계열을 사용한다.

### `build_search_params(period: str, shorts: bool = False) -> str`

- 기간 코드와 shorts flag를 bytes로 조립한 뒤 URL-safe base64로 인코딩한다.

### `extract_videos(node, out)`

- 중첩 dict/list를 재귀 순회하며 `videoRenderer`를 찾는다.
- id, title, channel, views, length, published, thumbnail을 out에 append한다.

### `yt_search(query: str, period: str, shorts: bool, country: str = "KR")`

- `/youtubei/v1/search` payload에 `hl/gl`, query, params를 넣어 호출한다.
- 네트워크와 JSON 오류는 빈 리스트로 폴백한다.
- id dedupe 뒤 `within_period(..., country)`로 locale별 기간 필터를 적용한다.

### `yt_like_count(video_id: str, country: str = "KR")`

- `/youtubei/v1/next` payload에도 국가별 `hl/gl`을 넣는다.
- 한국어 `다른 사용자 ...명` 또는 영어 `along with ... other` 패턴을 찾아 likes를 계산한다.
- 실패하면 0을 반환한다.

### `enrich_likes(videos, limit=45, country: str = "KR")`

- 상위 limit개 중 likes가 없는 영상만 ThreadPoolExecutor로 보강한다.
- 각 작업은 `yt_like_count(video_id, country)`를 호출한다.

### `merge_yt_searches(queries, period, shorts, country: str = "KR")`

- 여러 query를 병렬 검색하고 id 기준으로 dedupe한 뒤 views 내림차순 정렬한다.

### `get_videos(category: str, period: str, shorts: bool, force: bool, enrich: bool = False, query: str = "", country: str = "KR")`

- country를 먼저 정규화한다.
- 직접 검색어가 있으면 단일 query, 없으면 `_category_queries(category, country)`를 사용한다.
- enrich가 참이면 `enrich_likes(..., country=country)`를 수행한다.
- 캐시는 country를 포함한 key로 저장한다.

### 테스트 함수 지도

- `YoutubeToolTest.test_extract_videos_nested_tree`
- `YoutubeToolTest.test_within_period_filters_excluded_phrases`
- `YoutubeToolTest.test_within_period_english_week_allows_days_ago`
- `YoutubeToolTest.test_build_search_params_exact_base64`
- `YoutubeToolTest.test_yt_search_payload_dedupes_and_filters_period`
- `YoutubeToolTest.test_yt_search_uses_country_locale`
- `YoutubeToolTest.test_yt_like_count_regex_korean_english_and_failure`
- `YoutubeToolTest.test_get_videos_query_selection_and_force_cache_contract`
- `YoutubeToolTest.test_get_videos_cache_key_includes_country`

## Dependencies

이 모듈이 직접 가져오는 대상과 런타임으로 기대하는 설정을 적는다.

- `base64`, `json`, `re`, `urllib.error`
- `concurrent.futures.ThreadPoolExecutor`
- `shared.cache_tool`
- `shared.http_tool`

## Dependents

이 모듈을 import하거나 HTTP 라우트로 소비하는 쪽이다.

- `src/youtube/__init__.py` re-exports `CATEGORIES`, `get_videos`
- `src/main.py` reads `youtube_tool.CATEGORIES` in `/api/categories`
- `src/main.py` validates `youtube_tool.COUNTRY_LOCALE` in `/api/videos`
- `src/main.py` calls `youtube_tool.get_videos` in `/api/videos`
- `src/frontend/index.html` calls `/api/categories` and `/api/videos`

## Sync Checklist

코드를 바꾼 뒤에는 아래 항목을 순서대로 확인한다.
체크박스는 실제 변경에서 완료 여부를 남기는 용도다.

- [ ] `CATEGORIES`, `COUNTRY_CATEGORIES` 변경 시 `/api/categories`와 프론트 chip 표시를 확인한다.
- [ ] `COUNTRY_LOCALE` 변경 시 main.py country validation과 frontend country segmented control을 함께 갱신한다.
- [ ] `PERIOD_CODE` 변경 시 exact base64 테스트를 갱신한다.
- [ ] `PERIOD_EXCLUDE_BY_LOCALE` 변경 시 ko/en/ja 기간 필터 테스트를 갱신한다.
- [ ] video item 키 변경 시 `videoCard`와 `/api/videos` 응답을 갱신한다.
- [ ] 좋아요 보강 범위나 country 전달이 바뀌면 enrich cache key를 검토한다.
- [ ] 캐시 key shape가 바뀌면 국가별 cache 격리 테스트를 갱신한다.

### 실패 동작 체크

- [ ] InnerTube search 오류는 빈 리스트로 폴백한다.
- [ ] like count 오류는 0으로 폴백한다.
- [ ] 중복 video id는 한 번만 남아야 한다.
- [ ] unknown country는 `KR`로 폴백해야 한다.

### 문서 동기화 체크

- [ ] `src/youtube/__init__.py` 라인 수가 3줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/youtube/youtube_tool.py` 라인 수가 259줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/youtube/test_youtube_tool.py` 라인 수가 222줄에서 바뀌면 File Tree를 갱신한다.

## 변경 기록

- 2026-07-07: 국가별 YouTube 검색, locale별 기간 필터, country 포함 캐시 key를 문서에 동기화했다.

## 문서 연결

- 이전: [[shared.md]]
- 다음: [[reels.md]]
