---
created: 2026-07-07
tags: [trend-viewer, frontend, vanilla-js, analysis-tab, date-tab, home-briefing]
aliases: [frontend 모듈, 프론트엔드 문서, 분석 탭, 데이트 탭]
---

# frontend 모듈 문서

이 문서는 `src/frontend/` 모듈을 다음 작업자가 바로 이어받을 수 있게 설명한다.
소스 코드를 먼저 읽고, 파일 경계와 함수 경계를 기준으로 책임을 적는다.
여기서 말하는 동기화는 코드 변경 뒤 이 문서와 테스트 관점도 함께 맞추는 일을 뜻한다.
외부 웹 검색 없이 로컬 소스와 포팅 계획 문서만 근거로 삼는다.

---

## File Tree

이 섹션은 실제 파일 수와 라인 수를 기준으로 모듈의 표면적을 보여준다.
라인 수가 달라지면 이 표도 같이 갱신한다.

| 파일 | 라인 수 | 역할 |
|---|---:|---|
| `src/frontend/__init__.py` | 0 | 빈 frontend package marker |
| `src/frontend/index.html` | 2652 | 단일 파일 HTML/CSS/JS 프론트엔드 |

### 파일별 읽기 순서

1. `src/frontend/__init__.py`를 확인한다. 현재는 내용이 없는 0줄 package marker다.
2. `src/frontend/index.html`를 읽는다. 단일 파일 HTML/CSS/JS 프론트엔드 라인 수는 2652줄이다.

### 파일 경계 메모

- `src/frontend/__init__.py`는 빈 package marker다.
- `src/frontend/index.html`은 화면 구조, CSS, inline JavaScript 상태와 API 호출을 모두 맡는다.
- 파일이 크므로 탭 정의, 상태 객체, 공통 렌더 helper, 각 load/render 함수, 이벤트 wiring 순서로 읽는다.
- 라인 수가 바뀌면 File Tree와 문서 동기화 체크를 함께 갱신한다.

## Module Responsibility

`src/frontend/index.html`은 trend-viewer의 실제 작업 화면이다.
마케팅 페이지 없이 첫 화면에서 바로 홈 브리핑을 보여주고, 탭으로 급상승·분석·YouTube·Shorts·AI·데이트·Reels·X·Threads·TikTok·저장을 전환한다.
상태 관리는 framework 없이 전역 객체와 탭별 배열로 나뉘며, API 호출과 렌더 함수가 같은 파일 안에 inline으로 유지된다.

### 책임 경계

- 탭 UI와 toolbar 표시 조건을 소유한다.
- 국가 segmented control과 URL hash 동기화를 소유한다.
- 카테고리·기간·검색 상태를 소유한다.
- 급상승, 분석, YouTube, Shorts, AI news, 데이트, 계정 기반 소스의 loading/empty/error 상태를 소유한다.
- 저장 카드, 홈 브리핑, keyboard shortcut, modal player를 소유한다.

### 운영 관점

- `VIEWS`는 `home`, `trends`, `analysis`, `youtube`, `shorts`, `ai`, `date`, `reels`, `x`, `threads`, `tiktok`, `saved` 순서의 12개 탭을 사용한다.
- `state.country`는 `KR`, `US`, `JP` 중 하나이며 기본값은 `KR`이다.
- 국가 UI는 `.country` button 세 개로 구성된 segmented control이다.
- hash에는 기본값과 다른 경우 `country` param이 저장되고, 복원 시 invalid country는 `KR`로 되돌린다.
- 국가 변경은 YouTube/Shorts, Trends, Analysis, Date, Home 데이터를 invalidation한다.
- `.tab`은 `white-space: nowrap`과 `flex-shrink: 0`으로 긴 탭 label이 줄바꿈되지 않게 한다.
- YouTube/Shorts/Trends/Analysis/Date/Home briefing API URL에는 country param이 붙는다.
- 외부 썸네일은 대부분 `/api/img?u=` 프록시를 경유한다.

## Key Function Signatures

아래 함수명은 실제 소스의 공개 함수와 내부 헬퍼를 기준으로 한다.
테스트 헬퍼는 동작 계약을 보여주는 경우에만 포함한다.

### `const VIEWS = [...]`

- 12개 탭의 ID, label, SVG icon, color token, view element, loader, toolbar, force 지원 여부를 선언한다.
- 분석은 급상승 바로 뒤에 있으며 `i-sparkles`, `--c-analysis`, country toolbar를 사용한다.
- 데이트는 AI 바로 뒤에 있으며 `i-heart`, `--c-date`, country toolbar를 사용한다.
- 숫자 단축키는 이 배열의 인덱스를 직접 사용한다.

### `const state = { tab, category, period, categories, search, country }`

- 전역 필터 상태를 보관한다.
- `country`는 급상승, 분석, YouTube, Shorts, 데이트, 홈 브리핑 URL을 바꾼다.
- 탭 전환, 카테고리 chip, 검색 form, 기간 버튼, 국가 버튼이 이 객체를 갱신한다.

### `const DEFAULT_HASH_STATE = { tab, category, period, search, country }`

- hash 생략 기준값을 정의한다.
- country 기본값은 `KR`이다.

### `updateHashState() / restoreHashState()`

- hash에 `tab`, `cat`, `period`, `q`, `country`를 저장하거나 복원한다.
- country는 대문자로 읽고 `COUNTRIES`에 없으면 기본값으로 돌린다.
- 복원 시 `.country` active class와 `aria-pressed`를 함께 맞춘다.

### `invalidateVideoViews()`

- 국가·카테고리·기간·검색 변경으로 YouTube와 Shorts 캐시 화면을 다시 불러야 할 때 `loadedViews`에서 제거한다.

### `document.getElementById('countries').onclick`

- `.country` button을 찾아 `state.country`를 바꾼다.
- button active class와 `aria-pressed`를 갱신한다.
- YouTube/Shorts, Trends, Analysis, Date, Home loaded state를 삭제한다.
- 현재 tab에 따라 `loadTrends`, `loadAnalysis`, `loadDate`, `loadHome`, `loadVideos` 중 하나를 호출한다.

### `loadVideos(force = false) / renderVideos() / videoCard(v, rank)`

- `/api/videos` 호출, skeleton/error/empty 처리, 카드 렌더링을 담당한다.
- query에는 category, period, shorts, force, enrich, q, country가 포함된다.

### `let trendsSeq = 0`

- 급상승 탭의 비동기 응답 순서를 보호한다.
- 새 요청마다 증가하고, 오래된 응답은 렌더하지 않는다.

### `safeUrl(u)`

- `http://` 또는 `https://` URL만 외부 링크로 허용한다.
- 급상승 news link와 AI news link, 홈 브리핑 링크에 사용된다.

### `loadTrends(force = false)`

- 현재 tab이 `trends`가 아니면 즉시 반환한다.
- `/api/trends?country=${state.country}`를 호출하고 force가 참이면 `force=1`을 붙인다.
- skeleton, cache age, empty, error 상태를 처리한다.
- 결과는 `trendsData`에 저장한 뒤 `renderTrends()`로 그린다.

### `renderTrends()`

- `trendsData`를 `.trendcard` list로 그린다.
- keyword는 Google search 링크로 연결한다.
- `traffic`, `timeAgo(ts)`, news 최대 3개, `picture` 프록시 이미지를 표시한다.
- news URL은 `safeUrl`을 통과한 것만 링크로 만든다.

### `loadAnalysis(force = false)`

- `/api/analysis?country=${state.country}`를 호출하고 force가 참이면 `force=1`을 붙인다.
- `analysisSeq`로 stale response를 막고, 새 요청 전에 기존 `AbortController`를 취소한다.
- 전체 요청 90초 timer를 두며 abort와 일반 fetch 오류를 나눠 표시한다.
- 응답의 `fetchedAt`, `cacheTtl`, `llm`, `velocityBaseline`, `errors`를 상태 영역에 반영한다.

### `renderAnalysis(data) / analysisCard(cluster)`

- `clusters`를 momentum, platform badge, why, keyword, evidence link가 있는 카드로 그린다.
- LLM이 비활성화되거나 실패하면 `휴리스틱 분석` 상태 chip을 표시한다.
- cluster가 있으면서 channel error가 있으면 결과를 유지하고 일부 수집 실패를 알린다.
- evidence URL은 `safeUrl`을 통과해야 하며 evidence link가 있어 카드 전체 action을 붙이지 않는다.
- briefing이 없으면 briefing band를 숨긴다.

### `loadDate(force = false) / renderDate() / dateCard(item, rank)`

- `/api/date?country=${state.country}`를 호출하고 force가 참이면 `force=1`을 붙인다.
- `dateSeq`로 오래된 응답을 무시한다.
- briefing 두 줄과 최대 30개 idea를 카드로 그린다.
- 카드에는 source, metric, account, published, tag를 표시하고 안전한 원문 URL을 연다.

### `loadAI(force = false) / renderModels(elId, models)`

- `/api/ai` 호출, Hugging Face model card, cache age를 담당한다.
- news data는 `aiNewsData`에 저장한 뒤 chip과 list를 다시 렌더한다.

### `const aiNewsState = { category: '전체' }`

- AI news category chip의 선택 상태를 가진다.
- category 값은 `전체`, `모델·제품`, `연구`, `산업·투자`, `정책·규제`, `기타` 중 하나다.

### `renderAINewsChips() / renderAINews()`

- news category chip을 만들고 선택 상태를 표시한다.
- `renderAINews`는 category에 맞춰 `aiNewsData`를 필터링한다.
- `mixed` 또는 category가 없는 뉴스는 `기타`에서 보인다.
- news link는 `safeUrl(n.link) || '#'`로 방어한다.

### `const HOME_SECTIONS`

- 분석을 제외한 9개 홈 소스의 URL과 렌더 metadata를 정의한다.
- 급상승 URL은 `/api/trends?country=${state.country}`이다.
- YouTube/Shorts URL은 `/api/videos?...&country=${state.country}`이다.
- 데이트 URL은 `/api/date?country=${state.country}`이다.
- force refresh 때 각 URL에 `force=1`을 붙인다.

### `const HOME_ANALYSIS_SECTION / loadHomeAnalysis(sectionsEl, force)`

- 분석은 최대 70초가 걸릴 수 있어 `HOME_SECTIONS`의 병렬 완료를 막지 않도록 별도 fetch한다.
- 대기 중에는 전용 skeleton 5개를 표시한다.
- 성공하면 briefing과 cluster 최대 5개를 홈 row로 바꾼다.
- 실패하면 분석 홈 section만 조용히 제거한다.

### `loadHome(force = false) / homeItems(section, data)`

- `HOME_SECTIONS`를 병렬로 fetch하고 홈 브리핑 섹션을 채운다.
- 급상승 section은 `data.trends`에서 keyword, picture, traffic, 첫 news link를 가져온다.
- 데이트 section은 `data.ideas`에서 source, metric, account, tag를 가져온다.
- 분석 mapper는 별도 `HOME_ANALYSIS_SECTION`과 `data.clusters`를 사용한다.

### 테스트 함수 지도

- `수동 검증 대상: / 또는 /index.html이 src/frontend/index.html을 반환한다.`
- `수동 검증 대상: country segmented control이 hash country param과 API URL에 반영된다.`
- `수동 검증 대상: /api/trends 결과가 급상승 tab과 home briefing에 표시된다.`
- `수동 검증 대상: /api/analysis 결과가 분석 tab과 non-blocking home section에 표시된다.`
- `수동 검증 대상: LLM 비활성 응답이 휴리스틱 chip과 cluster를 유지한다.`
- `수동 검증 대상: /api/date 결과가 데이트 tab과 home briefing에 표시된다.`
- `수동 검증 대상: /api/categories 결과가 chip으로 표시된다.`
- `수동 검증 대상: /api/videos 결과가 YouTube와 Shorts grid로 표시된다.`
- `수동 검증 대상: /api/ai 결과가 latest/trending/news category chip으로 표시된다.`
- `수동 검증 대상: /api/reels, /api/x, /api/threads, /api/tiktok 결과가 각 tab에 표시된다.`
- `수동 검증 대상: .tab label이 좁은 화면에서 줄바꿈되지 않는다.`

## Dependencies

이 모듈이 직접 가져오는 대상과 런타임으로 기대하는 설정을 적는다.

- Pretendard Variable CDN stylesheet
- Browser DOM API: `document.getElementById`, `querySelector`, `createElement`
- Browser Fetch API: `/api/categories`, `/api/trends`, `/api/analysis`, `/api/videos`, `/api/ai`, `/api/date`, `/api/reels`, `/api/x`, `/api/threads`, `/api/tiktok`, saved/account POST routes
- Browser URLSearchParams API
- Browser localStorage API for seen/saved UI state
- CSS custom properties in `:root`
- CSS grid, aspect-ratio, focus-visible, prefers-reduced-motion
- YouTube iframe embed URL
- External window.open for platform links

## Dependents

이 모듈을 import하거나 HTTP 라우트로 소비하는 쪽이다.

- `src/main.py` serves this file in `_handle_index` for `/` and `/index.html`
- Users consume this as the first screen of the local app
- All backend feature modules are represented through API calls from this file
- Module docs use this file as the frontend contract source

## Sync Checklist

코드를 바꾼 뒤에는 아래 항목을 순서대로 확인한다.
체크박스는 실제 변경에서 완료 여부를 남기는 용도다.

- [ ] 새 탭 추가 시 `VIEWS`, nav button, view container, tab dispatcher, refresh dispatcher를 모두 갱신한다.
- [ ] country 목록 변경 시 `COUNTRIES`, segmented button, hash 복원, main.py validation, YouTube/Trends docs를 같이 갱신한다.
- [ ] country가 영향을 주는 API가 추가되면 `HOME_SECTIONS` URL과 invalidation 대상도 갱신한다.
- [ ] 분석 응답 shape 변경 시 `renderAnalysis`, `analysisCard`, `homeItems`를 함께 갱신한다.
- [ ] 분석 home fetch를 변경할 때 기본 `HOME_SECTIONS`의 완료를 막지 않는지 확인한다.
- [ ] 데이트 응답 shape 변경 시 `loadDate`, `renderDate`, `dateCard`, `homeItems`를 함께 갱신한다.
- [ ] `/api/trends` response key 변경 시 `loadTrends`, `renderTrends`, `homeItems`를 함께 갱신한다.
- [ ] AI news category 변경 시 `AI_NEWS_CATEGORIES`, `renderAINews`, `ai_news.md`를 함께 갱신한다.
- [ ] API response key 변경 시 해당 load/render 함수와 backend handler를 함께 갱신한다.
- [ ] image host 추가 시 backend `IMG_PROXY_ALLOW`도 확인한다.
- [ ] `.tab` 레이아웃 변경 시 nowrap, horizontal scroll, keyboard focus 이동을 확인한다.
- [ ] modal 변경 시 iframe src cleanup과 외부 링크 href를 같이 확인한다.

### 실패 동작 체크

- [ ] fetch 실패는 `showError`로 source별 inline error를 표시해야 한다.
- [ ] 빈 list는 grid를 비우고 empty/fallback 상태로 전환해야 한다.
- [ ] stale trends 응답은 `trendsSeq`로 무시되어야 한다.
- [ ] stale analysis 응답은 `analysisSeq`로 무시되고 이전 요청은 abort되어야 한다.
- [ ] stale date 응답은 `dateSeq`로 무시되어야 한다.
- [ ] `safeUrl`을 통과하지 못한 외부 URL은 링크로 쓰지 않아야 한다.
- [ ] YouTube likes sort는 likes 데이터가 없으면 enrich 재요청을 해야 한다.

### 문서 동기화 체크

- [ ] `src/frontend/__init__.py` 라인 수가 0줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/frontend/index.html` 라인 수가 2652줄에서 바뀌면 File Tree를 갱신한다.

## 변경 기록

- 2026-07-10: 실제 2652줄 소스, 12개 `VIEWS`, 분석·데이트 탭, 별도 홈 분석 흐름을 문서에 동기화했다.
- 2026-07-07: 국가 segmented control, 급상승 탭, 홈 브리핑 country URL, AI news chip 필터, `.tab` nowrap을 문서에 동기화했다.

## 문서 연결

- 이전: [[ai_news.md]]
- 다음: [[shared.md]]
