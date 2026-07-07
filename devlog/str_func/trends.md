---
created: 2026-07-07
tags: [trend-viewer, trends, Google-Trends, RSS, country-filter]
aliases: [trends 모듈, 급상승 모듈, Google Trends RSS]
---

# trends 모듈 문서

이 문서는 `src/trends/` 모듈을 다음 작업자가 바로 이어받을 수 있게 설명한다.
소스 코드를 먼저 읽고, 파일 경계와 함수 경계를 기준으로 책임을 적는다.
여기서 말하는 동기화는 코드 변경 뒤 이 문서와 테스트 관점도 함께 맞추는 일을 뜻한다.
외부 웹 검색 없이 로컬 소스와 포팅 계획 문서만 근거로 삼는다.

---

## File Tree

이 섹션은 실제 파일 수와 라인 수를 기준으로 모듈의 표면적을 보여준다.
라인 수가 달라지면 이 표도 같이 갱신한다.

| 파일 | 라인 수 | 역할 |
|---|---:|---|
| `src/trends/__init__.py` | 3 | GEOS와 get_trends 배럴 export |
| `src/trends/trends_tool.py` | 97 | Google Trends RSS 수집, ht namespace 파싱, negative cache |
| `src/trends/test_trends_tool.py` | 161 | 급상승 RSS 파싱·국가·캐시 계약 테스트 |

### 파일별 읽기 순서

1. `src/trends/__init__.py`를 읽는다. 배럴 export 라인 수는 3줄이다.
2. `src/trends/trends_tool.py`를 읽는다. Google Trends RSS helper 라인 수는 97줄이다.
3. `src/trends/test_trends_tool.py`를 읽는다. 급상승 테스트 라인 수는 161줄이다.
4. `src/main.py`의 `/api/trends` handler를 읽어 route 응답 shape를 확인한다.
5. `src/frontend/index.html`의 `loadTrends`, `renderTrends`, `HOME_SECTIONS`를 읽어 소비 shape를 확인한다.

### 파일 경계 메모

- `src/trends/__init__.py`는 public export 표면만 맡는다.
- `src/trends/trends_tool.py`는 Google Trends RSS URL, country 정규화, RSS 파싱, 오류 shape, cache TTL을 맡는다.
- `src/trends/test_trends_tool.py`는 item shape, news cap, fallback country, cache key, negative cache TTL을 검증한다.
- main.py는 route envelope와 country validation을 맡는다.
- frontend는 route 결과를 화면 카드와 홈 브리핑으로 렌더링한다.

## Module Responsibility

`src/trends/`는 Google Trends RSS의 국가별 급상승 검색어를 앱 내부 shape로 변환한다.
지원 국가는 `KR`, `US`, `JP`이고 유효하지 않은 입력은 `KR`로 폴백한다.
RSS item 안의 Google Trends 전용 `ht:` namespace를 파싱해 traffic, 대표 이미지, 관련 뉴스 목록을 추출한다.
수집 실패는 오류 list로 반환하고, 실패 결과는 짧은 negative cache TTL로 저장한다.

### 책임 경계

- `GEOS`는 지원 국가 집합 `("KR", "US", "JP")`를 소유한다.
- `TRENDS_RSS_URL`은 `https://trends.google.com/trending/rss?geo=%s` URL template을 소유한다.
- `HT_NS`와 `NS`는 `https://trends.google.com/trending/rss` namespace 파싱을 소유한다.
- `NEGATIVE_CACHE_TTL = 120`은 실패 결과 캐시 시간을 소유한다.
- `_parse_items`는 RSS item을 trend item shape로 바꾼다.
- main.py는 `/api/trends` route envelope를 소유한다.

### 운영 관점

- item shape는 `{keyword, traffic, trafficValue, ts, picture, pictureSource, news}`이다.
- `news`는 관련 뉴스 item을 최대 3개만 담는다.
- news item shape는 `{title, url, source, picture}`이다.
- 정렬은 `(trafficValue, ts)` 내림차순이다.
- RSS fetch 또는 XML parse 실패는 empty items와 errors list를 반환한다.
- 실패 결과는 `NEGATIVE_CACHE_TTL=120`으로 캐시되고, 성공 결과는 shared 기본 TTL을 사용한다.

## Key Function Signatures

아래 함수명은 실제 소스의 공개 함수와 내부 헬퍼를 기준으로 한다.
테스트 헬퍼는 동작 계약을 보여주는 경우에만 포함한다.

### `_normalize_country(country: str) -> str`

- 입력을 대문자로 바꾼 뒤 `GEOS`에 없으면 `KR`을 반환한다.

### `_traffic_value(text: str) -> int`

- `20,000+` 같은 traffic 문자열에서 숫자만 남겨 int로 바꾼다.
- 숫자가 없으면 0을 반환한다.

### `_timestamp(pub_date: str, fallback: float) -> float`

- RSS pubDate를 epoch timestamp로 바꾼다.
- pubDate가 없거나 깨졌으면 fetch 시각 fallback을 반환한다.

### `_ht_text(node, tag: str) -> str`

- `node.findtext("ht:" + tag, namespaces=NS)`로 Google Trends `ht:` namespace 값을 읽는다.
- 값이 없으면 빈 문자열을 반환한다.

### `_news_items(item) -> list`

- `ht:news_item` node를 순회해 related news를 만든다.
- 최대 3개까지만 포함한다.

### `_parse_items(body, fallback_ts: float) -> list`

- RSS XML을 파싱하고 `item` node마다 keyword, traffic, timestamp, image, news를 추출한다.
- 결과는 trafficValue와 timestamp 기준 내림차순으로 정렬한다.

### `fetch_trends(country: str) -> list`

- `TRENDS_RSS_URL % country`로 Google Trends RSS를 호출한다.
- 성공 시 `(items, [])`를 반환한다.
- 실패 시 `([], [{"country": country, "kind": exc.__class__.__name__}])`를 반환한다.

### `get_trends(country: str = "KR", force: bool = False)`

- country를 정규화하고 cache key `("trends", country)`를 사용한다.
- `cache_tool.cached(..., ttl=ttl_for_outcome)`을 호출한다.
- 실패 outcome은 `NEGATIVE_CACHE_TTL`, 성공 outcome은 기본 TTL을 사용한다.
- 반환값은 4-tuple `(items, fetched_at, errors, cache_ttl)`이다.

### `main.py /api/trends route contract`

- query param은 `country`, `force`를 받는다.
- country가 `trends_tool.GEOS`에 없으면 `KR`로 폴백한다.
- response shape는 `{trends, country, fetchedAt, cacheTtl, status, errors}`이다.
- `status`는 `_feed_status(trends, errors)` 결과이며 `ok`, `partial`, `error`, `empty` 중 하나다.

### 테스트 함수 지도

- `TrendsToolTest.test_get_trends_parses_items_sorts_and_caps_news`
- `TrendsToolTest.test_malformed_pub_date_falls_back_to_fetch_time`
- `TrendsToolTest.test_unknown_country_falls_back_to_kr`
- `TrendsToolTest.test_cache_key_is_separate_per_country`
- `TrendsToolTest.test_xml_error_returns_empty_list`
- `TrendsToolTest.test_fetch_failure_uses_negative_cache_ttl_then_recovers`

## Dependencies

이 모듈이 직접 가져오는 대상과 런타임으로 기대하는 설정을 적는다.

- `email.utils`
- `re`
- `time`
- `xml.etree.ElementTree as ET`
- `shared.cache_tool`
- `shared.http_tool`

## Dependents

이 모듈을 import하거나 HTTP 라우트로 소비하는 쪽이다.

- `src/trends/__init__.py` re-exports `GEOS`, `get_trends`
- `src/main.py` imports `trends_tool` and serves `/api/trends`
- `src/frontend/index.html` calls `/api/trends` in `loadTrends`
- `src/frontend/index.html` calls `/api/trends` in `HOME_SECTIONS`
- `src/shared/cache_tool.py` supplies callback TTL and `ttl_for`
- `src/shared/img_proxy_tool.py` proxies trend pictures through `/api/img`

## Sync Checklist

코드를 바꾼 뒤에는 아래 항목을 순서대로 확인한다.
체크박스는 실제 변경에서 완료 여부를 남기는 용도다.

- [ ] `GEOS` 변경 시 main.py validation, frontend country segmented control, YouTube country docs를 함께 갱신한다.
- [ ] RSS item key 변경 시 `renderTrends`와 `homeItems`를 함께 갱신한다.
- [ ] `ht:` namespace tag 변경 시 `_ht_text`, `_news_items`, parser 테스트를 갱신한다.
- [ ] related news cap 3 변경 시 frontend card 밀도와 테스트를 확인한다.
- [ ] negative cache TTL 변경 시 shared cache TTL callback 테스트와 route `cacheTtl` 표시를 확인한다.
- [ ] `/api/trends` response envelope 변경 시 frontend `loadTrends`와 home briefing을 갱신한다.

### 실패 동작 체크

- [ ] XML parse 실패는 empty list와 `ParseError` kind를 반환해야 한다.
- [ ] HTTP 실패는 empty list와 exception class kind를 반환해야 한다.
- [ ] 실패 outcome은 `NEGATIVE_CACHE_TTL=120`으로 캐시되어야 한다.
- [ ] force refresh는 실패 캐시를 무시하고 다시 fetch해야 한다.
- [ ] unknown country는 `KR`로 폴백하고 cache key도 `("trends", "KR")`이어야 한다.

### 문서 동기화 체크

- [ ] `src/trends/__init__.py` 라인 수가 3줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/trends/trends_tool.py` 라인 수가 97줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/trends/test_trends_tool.py` 라인 수가 161줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/main.py`의 `/api/trends` route shape가 바뀌면 route contract를 갱신한다.
- [ ] `src/frontend/index.html`의 `loadTrends`나 `HOME_SECTIONS` URL이 바뀌면 frontend doc과 함께 갱신한다.

## 변경 기록

- 2026-07-07: Google Trends RSS 모듈 문서를 새로 작성하고 item shape, negative cache, `/api/trends` route contract를 기록했다.

## 문서 연결

- 이전: [[youtube.md]]
- 다음: [[ai_news.md]]
