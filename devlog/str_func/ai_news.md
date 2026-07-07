---
created: 2026-07-07
tags: [trend-viewer, AI-news, Hugging-Face, RSS, feed-registry]
aliases: [ai_news 모듈, AI 영상 뉴스, Hugging Face 모델, AI 뉴스 분류]
---

# ai_news 모듈 문서

이 문서는 `src/ai_news/` 모듈을 다음 작업자가 바로 이어받을 수 있게 설명한다.
소스 코드를 먼저 읽고, 파일 경계와 함수 경계를 기준으로 책임을 적는다.
여기서 말하는 동기화는 코드 변경 뒤 이 문서와 테스트 관점도 함께 맞추는 일을 뜻한다.
외부 웹 검색 없이 로컬 소스와 포팅 계획 문서만 근거로 삼는다.

---

## File Tree

이 섹션은 실제 파일 수와 라인 수를 기준으로 모듈의 표면적을 보여준다.
라인 수가 달라지면 이 표도 같이 갱신한다.

| 파일 | 라인 수 | 역할 |
|---|---:|---|
| `src/ai_news/__init__.py` | 3 | fetch_oembed와 get_ai_data 배럴 export |
| `src/ai_news/ai_news_tool.py` | 301 | AI 뉴스 feed registry, 카테고리 분류, Hugging Face 모델 수집 |
| `src/ai_news/test_ai_news_tool.py` | 320 | AI news/model/oEmbed 계약 테스트 |

### 파일별 읽기 순서

1. `src/ai_news/__init__.py`를 읽는다. 배럴 export 라인 수는 3줄이다.
2. `src/ai_news/ai_news_tool.py`를 읽는다. 뉴스 feed와 모델 수집 라인 수는 301줄이다.
3. `src/ai_news/test_ai_news_tool.py`를 읽는다. AI news/model/oEmbed 테스트 라인 수는 320줄이다.

### 파일 경계 메모

- `src/ai_news/__init__.py`는 public export 표면만 맡는다.
- `src/ai_news/ai_news_tool.py`는 feed registry, RSS/HN 파싱, AI anchor 필터, 카테고리 분류, 모델 수집, oEmbed를 맡는다.
- `src/ai_news/test_ai_news_tool.py`는 feed 수, 분류 규칙, dedupe, fetch-time fallback, HN branch, cache contract를 검증한다.
- 라인 수가 바뀌면 File Tree와 문서 동기화 체크를 함께 갱신한다.

## Module Responsibility

`src/ai_news/`는 AI 뉴스와 Hugging Face 영상 생성 모델 목록을 모은다.
뉴스는 여러 공식·기술 매체 RSS, Google News RSS, HN Algolia JSON API를 병렬로 읽고 하나의 list로 합친다.
각 뉴스 item은 region과 category를 가진 앱 내부 shape로 정규화되고, Hugging Face 모델은 latest/trending 두 묶음으로 정리된다.
추가로 TikTok과 YouTube URL의 oEmbed metadata를 가져오는 작은 helper를 제공한다.

### 책임 경계

- `FEED_REGISTRY`는 17개 feed의 이름, URL, region, 기본 category, `needs_ai_anchor` 여부를 소유한다.
- feed region은 `global` 또는 `KR`로 들어오며 프론트는 `KR`을 국내, 그 외를 해외로 표시한다.
- feed 기본 category는 `모델·제품`, `연구`, `산업·투자`, `정책·규제`, `mixed` 중 하나다.
- `needs_ai_anchor=True` feed는 title에서 AI anchor가 발견된 item만 통과시킨다.
- `CATEGORY_KEYWORDS`는 카테고리별 가중치 dict다. named entity와 명확한 도메인 키워드는 2점, generic 키워드는 1점이다.
- `classify_news`는 leader 점수가 runner-up보다 2점 이상 앞설 때만 해당 category로 확정하고, 아니면 feed 기본 category로 폴백한다.
- `fetch_news`는 feed별 최대 20개, 병합 후 최신순 최대 80개를 반환한다.

### 운영 관점

- AI data는 `{news, models, fetchedAt, cacheTtl}` 형태로 main.py에서 응답된다.
- news item shape는 `{region, category, title, source, link, ts}`이다.
- model item은 `id`, `likes`, `downloads`, `pipeline`, `createdAt`를 가진다.
- `_dedupe_key`는 정규화된 title에서 공백과 문장부호를 제거해 중복 뉴스를 합친다.
- `_news_ts`는 pubDate 파싱 실패 시 feed fetch 시각을 fallback timestamp로 쓴다.
- HN Algolia feed는 XML이 아니라 JSON branch인 `_parse_hn_news`로 처리한다.

## Key Function Signatures

아래 함수명은 실제 소스의 공개 함수와 내부 헬퍼를 기준으로 한다.
테스트 헬퍼는 동작 계약을 보여주는 경우에만 포함한다.

### `_google_news_url(query, hl, gl, ceid)`

- Google News RSS search URL을 quote된 query와 locale 값으로 만든다.

### `_feed(name, url, region, category, needs_ai_anchor=False)`

- `FEED_REGISTRY` item dict를 만든다.
- dict key는 `name`, `url`, `region`, `category`, `needs_ai_anchor`다.

### `FEED_REGISTRY`

- 총 17개 feed를 가진다.
- 글로벌 기술 매체, 한국 매체, Google News query, HN Algolia JSON feed를 함께 포함한다.
- feed마다 region, 기본 category, AI anchor 필터 필요 여부가 명시된다.

### `classify_news(title, source_default_category)`

- title을 NFKC lower-case로 정규화한다.
- `CATEGORY_KEYWORDS`의 keyword hit를 가중치로 합산한다.
- leader가 runner-up보다 2점 이상 앞서면 leader category를 반환한다.
- 확실한 leader가 없으면 source 기본 category를 쓰고, 기본 category도 고정 카테고리가 아니면 `mixed`를 반환한다.

### `has_ai_anchor(title)`

- ASCII token anchor는 `ai`, `llm`, `gpt`, `chatgpt`, `openai`, `anthropic`, `gemini`를 단어 경계로 본다.
- phrase anchor는 `machine learning`을 공백 유연 regex로 본다.
- 한국어 anchor는 `인공지능`, `생성형`, `머신러닝`, `딥러닝` substring으로 본다.

### `_news_ts(pub, fallback)`

- `email.utils.parsedate_to_datetime(pub).timestamp()`를 반환한다.
- pubDate가 없거나 파싱 실패하면 `fallback`을 반환한다.

### `_news_item(feed, title, source, link, ts)`

- feed metadata와 title classifier를 결합해 `{region, category, title, source, link, ts}` shape를 만든다.
- source가 비어 있으면 feed 이름을 사용한다.

### `_parse_rss_news(feed, body, fetch_ts)`

- RSS XML에서 item을 순회한다.
- `needs_ai_anchor` feed는 `has_ai_anchor(title)`가 거짓이면 제외한다.
- feed별 최대 20개를 반환한다.

### `_parse_hn_news(feed, fetch_ts)`

- HN Algolia JSON endpoint를 `http_json`으로 호출한다.
- `hits`에서 title/story_title, url/story_url, created_at_i를 읽는다.
- created_at_i가 없으면 fetch timestamp를 사용한다.

### `_dedupe_key(title)`

- title을 정규화한 뒤 공백과 punctuation category 문자를 제거한다.
- 빈 key나 이미 본 key는 병합 단계에서 제외된다.

### `fetch_news()`

- `FEED_REGISTRY`를 최대 8 worker로 fetch한다.
- HN URL은 JSON branch, 나머지는 RSS branch로 처리한다.
- feed 실패는 해당 feed 빈 리스트로 삼킨다.
- dedupe 후 timestamp 최신순으로 정렬하고 최대 80개를 반환한다.

### `fetch_hf_models()`

- `text-to-video`, `image-to-video` pipeline을 createdAt/trendingScore 정렬로 호출한다.
- 중복 model id를 제거하고 `latest`, `trending`을 각각 최대 12개 반환한다.

### `get_ai_data(force: bool)`

- news와 models fetch를 병렬 실행한다.
- 캐시 key는 `("ai",)`이다.

### `fetch_oembed(url: str)`

- tiktok.com은 TikTok oEmbed endpoint로 라우팅한다.
- youtube.com 또는 youtu.be는 YouTube oEmbed endpoint로 라우팅한다.
- 미지원 host는 `{ok: False, reason: "unsupported"}`를 반환한다.

### 테스트 함수 지도

- `AiNewsToolTest.test_feed_registry_has_expected_shape`
- `AiNewsToolTest.test_classify_news_weighted_keywords_and_lead_rule`
- `AiNewsToolTest.test_has_ai_anchor_word_boundaries_and_korean`
- `AiNewsToolTest.test_fetch_news_parses_limits_sorts_dedupes_and_categorizes`
- `AiNewsToolTest.test_fetch_news_uses_fetch_time_when_pubdate_missing`
- `AiNewsToolTest.test_fetch_news_hn_algolia_json_branch`
- `AiNewsToolTest.test_fetch_news_returns_empty_chunk_on_fetch_or_parse_failure`
- `AiNewsToolTest.test_fetch_hf_models_dedupes_splits_and_limits_results`
- `AiNewsToolTest.test_fetch_hf_models_returns_empty_lists_on_fetch_failure`
- `AiNewsToolTest.test_get_ai_data_cache_contract_and_force_refresh`
- `AiNewsToolTest.test_fetch_oembed_routes_supported_hosts`
- `AiNewsToolTest.test_fetch_oembed_unsupported_and_fetch_failed`

## Dependencies

이 모듈이 직접 가져오는 대상과 런타임으로 기대하는 설정을 적는다.

- `email.utils`
- `json`, `re`, `time`, `unicodedata`, `urllib.error`
- `xml.etree.ElementTree as ET`
- `concurrent.futures.ThreadPoolExecutor`
- `urllib.parse.quote`, `urllib.parse.urlparse`
- `shared.cache_tool`
- `shared.http_tool`

## Dependents

이 모듈을 import하거나 HTTP 라우트로 소비하는 쪽이다.

- `src/ai_news/__init__.py` re-exports `fetch_oembed`, `get_ai_data`
- `src/main.py` calls `ai_news_tool.get_ai_data` in `/api/ai`
- `src/main.py` calls `ai_news_tool.fetch_oembed` in `/api/oembed`
- `src/frontend/index.html` calls `/api/ai` for the AI tab and home briefing

## Sync Checklist

코드를 바꾼 뒤에는 아래 항목을 순서대로 확인한다.
체크박스는 실제 변경에서 완료 여부를 남기는 용도다.

- [ ] `FEED_REGISTRY` 변경 시 feed count, region, category, `needs_ai_anchor` 테스트를 갱신한다.
- [ ] `CATEGORY_KEYWORDS` 변경 시 가중치와 2점 lead rule 테스트를 갱신한다.
- [ ] AI anchor 변경 시 한국어와 ASCII 단어 경계 테스트를 갱신한다.
- [ ] news item key 변경 시 `renderAINews`, `aiHomeItems`를 갱신한다.
- [ ] merged cap 80 변경 시 fetch_news limit 테스트와 프론트 표시 개수를 함께 검토한다.
- [ ] HN Algolia URL이나 response key가 바뀌면 JSON branch 테스트를 갱신한다.
- [ ] HF pipeline 변경 시 모델 카드 pill label을 확인한다.
- [ ] oEmbed 지원 host 추가 시 endpoint routing 테스트를 추가한다.

### 실패 동작 체크

- [ ] RSS fetch 또는 XML parse 실패는 해당 feed 빈 리스트로 처리한다.
- [ ] HN Algolia JSON fetch 실패도 해당 feed 빈 리스트로 처리한다.
- [ ] Hugging Face fetch 실패는 해당 job 빈 리스트로 처리한다.
- [ ] oEmbed fetch 실패는 `{ok: False, reason: "fetch_failed"}`여야 한다.

### 문서 동기화 체크

- [ ] `src/ai_news/__init__.py` 라인 수가 3줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/ai_news/ai_news_tool.py` 라인 수가 301줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/ai_news/test_ai_news_tool.py` 라인 수가 320줄에서 바뀌면 File Tree를 갱신한다.

## 변경 기록

- 2026-07-07: feed registry, weighted news classifier, HN JSON branch, news item shape, merged cap 80을 문서에 동기화했다.

## 문서 연결

- 이전: [[tiktok.md]]
- 다음: [[frontend.md]]
