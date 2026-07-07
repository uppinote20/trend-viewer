---
created: 2026-07-07
tags: [trend-viewer, frontend, vanilla-js, 020-policy, UI-state]
aliases: [frontend 모듈, 프론트엔드 문서, 020 폴리시]
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
| `src/frontend/__init__.py` | 3 | frontend package marker |
| `src/frontend/index.html` | 1015 | 단일 파일 HTML/CSS/JS 프론트엔드 |

### 파일별 읽기 순서

1. `src/frontend/__init__.py`를 읽는다. frontend package marker 라인 수는 3줄이다.
2. `src/frontend/index.html`를 읽는다. 단일 파일 HTML/CSS/JS 프론트엔드 라인 수는 1015줄이다.

### 파일 경계 메모

- `src/frontend/__init__.py`는 frontend package marker을 맡는다.
- `src/frontend/__init__.py`의 현재 기준 라인 수는 3줄이다.
- `src/frontend/__init__.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/frontend/index.html`는 단일 파일 HTML/CSS/JS 프론트엔드을 맡는다.
- `src/frontend/index.html`의 현재 기준 라인 수는 1015줄이다.
- `src/frontend/index.html`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.

## Module Responsibility

`src/frontend/index.html`은 trend-viewer의 실제 작업 화면이다.
마케팅 페이지 없이 첫 화면에서 바로 YouTube 트렌드 grid를 보여주고, 탭으로 AI·Reels·X·Threads·TikTok을 전환한다.
상태 관리는 framework 없이 전역 객체와 탭별 배열로 나뉘며, API 호출과 렌더 함수가 같은 파일 안에 inline으로 유지된다.

### 책임 경계

- 탭 UI와 toolbar 표시 조건을 소유한다.
- 카테고리·기간·검색 상태를 소유한다.
- 소스별 loading/empty/error 상태를 소유한다.
- 020 프론트엔드 폴리시 적용 결과를 소유한다.

### 운영 관점

- 탭은 `youtube`, `shorts`, `ai`, `reels`, `x`, `threads`, `tiktok` 값을 사용한다.
- YouTube와 Shorts만 toolbar를 표시한다.
- 외부 썸네일은 대부분 `/api/img?u=` 프록시를 경유한다.
- 정렬 상태는 `vidState`, `reelsState`, `social`, `tiktokState`로 분리되어 있다.
- 020 적용 항목은 Pretendard Variable, tabular nums, 8px card radius, skeleton loader, empty state, inline error, tab ARIA, focus-visible, reduced motion, active scale, lazy images다.

## Key Function Signatures

아래 함수명은 실제 소스의 공개 함수와 내부 헬퍼를 기준으로 한다.
테스트 헬퍼는 동작 계약을 보여주는 경우에만 포함한다.

### `const state = { tab, category, period, categories, search }`

- 유튜브/쇼츠 탭의 전역 필터 상태를 보관한다.
- 탭 전환, 카테고리 chip, 검색 form, 기간 버튼이 이 객체를 갱신한다.

### `showSkeleton(target, count = 8, shorts = false)`

- 카드 크기와 유사한 skeleton grid를 그린다.
- 020 정책의 로딩 상태 교정 항목이다.

### `showEmpty(target, title, body)`

- 빈 결과와 계정 0개 상태를 인라인 empty-state로 그린다.

### `showError(target, sourceName)`

- 소스별 inline error를 그리고 `role="alert"`를 설정한다.

### `setSelectedTab(btn)`

- `.tab` active class와 `aria-selected`를 동기화한다.

### `initCategories() / renderChips()`

- `/api/categories`를 읽고 카테고리 chip을 만든다.

### `loadVideos(force = false) / renderVideos() / videoCard(v, rank)`

- `/api/videos` 호출, skeleton/error/empty 처리, 카드 렌더링을 담당한다.

### `openPlayer(id, vertical) / closePlayer()`

- YouTube iframe modal을 열고 닫는다.

### `loadAI(force = false) / renderModels(elId, models) / timeAgo(ts)`

- AI tab의 `/api/ai` 호출, Hugging Face model card, news list를 담당한다.

### `loadReels(force = false) / renderReels() / updateAccount(action, username)`

- Reels tab의 `/api/reels` 호출, account chip, 정렬, 계정 POST를 담당한다.

### `buildSortMenu(kind, menuId, onPick) / renderSocial(kind) / loadSocial(kind, force = false)`

- X와 Threads의 공통 post list와 sort menu를 담당한다.

### `showThreadsFallback(accounts)`

- Threads posts가 비어 있을 때 계정 바로가기 fallback을 그린다.

### `initFoldMenu(menuId, options, stateObj, onPick)`

- YouTube/Reels/TikTok 접이식 정렬 메뉴를 만든다.

### `loadTikTok(force = false) / renderTikTok() / updateTtAccount(action, username)`

- TikTok tab의 `/api/tiktok` 호출, 계정 관리, 정렬을 담당한다.

### 테스트 함수 지도

- `수동 검증 대상: `/` 또는 `/index.html`이 `src/frontend/index.html`을 반환한다.`
- `수동 검증 대상: `/api/categories` 결과가 chip으로 표시된다.`
- `수동 검증 대상: `/api/videos` 결과가 YouTube와 Shorts grid로 표시된다.`
- `수동 검증 대상: `/api/ai` 결과가 latest/trending/news 세 구역에 표시된다.`
- `수동 검증 대상: `/api/reels` 결과와 `/api/reels/accounts` POST가 계정 chip에 반영된다.`
- `수동 검증 대상: `/api/x` 결과가 post card로 표시된다.`
- `수동 검증 대상: `/api/threads` 빈 결과가 fallback link grid로 표시된다.`
- `수동 검증 대상: `/api/tiktok` 결과가 shorts grid로 표시된다.`

## Dependencies

이 모듈이 직접 가져오는 대상과 런타임으로 기대하는 설정을 적는다.

- Pretendard Variable CDN stylesheet
- Browser DOM API: `document.getElementById`, `querySelector`, `createElement`
- Browser Fetch API: `/api/categories`, `/api/videos`, `/api/ai`, `/api/reels`, `/api/x`, `/api/threads`, `/api/tiktok`, account POST routes
- Browser URLSearchParams API
- CSS custom properties in `:root`
- CSS grid, aspect-ratio, focus-visible, prefers-reduced-motion
- YouTube iframe embed URL
- External window.open for platform links

### 의존성 변경 시 주의점

- Pretendard Variable CDN stylesheet 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- Browser DOM API: document.getElementById, querySelector, createElement 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- Browser Fetch API: /api/categories, /api/videos, /api/ai, /api/reels, /api/x, /api/threads, /api/tiktok, account POST routes 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- Browser URLSearchParams API 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- CSS custom properties in :root 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- CSS grid, aspect-ratio, focus-visible, prefers-reduced-motion 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- YouTube iframe embed URL 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- External window.open for platform links 변경은 호출 경로와 테스트 더블을 함께 확인한다.

## Dependents

이 모듈을 import하거나 HTTP 라우트로 소비하는 쪽이다.

- `src/main.py` serves this file in `_handle_index` for `/` and `/index.html`
- Users consume this as the first screen of the local app
- All backend feature modules are represented through API calls from this file
- 020 frontend policy uses this file as the applied implementation surface

### 호출자 영향 범위

- `src/main.py` serves this file in `_handle_index` for `/` and `/index.html` 쪽 응답 shape가 깨지지 않는지 확인한다.
- Users consume this as the first screen of the local app 쪽 응답 shape가 깨지지 않는지 확인한다.
- All backend feature modules are represented through API calls from this file 쪽 응답 shape가 깨지지 않는지 확인한다.
- 020 frontend policy uses this file as the applied implementation surface 쪽 응답 shape가 깨지지 않는지 확인한다.

## Sync Checklist

코드를 바꾼 뒤에는 아래 항목을 순서대로 확인한다.
체크박스는 실제 변경에서 완료 여부를 남기는 용도다.

- [ ] 새 탭 추가 시 nav button, view container, tab click dispatcher, refresh dispatcher를 모두 갱신한다.
- [ ] API response key 변경 시 해당 load/render 함수와 backend handler를 함께 갱신한다.
- [ ] 020 정책 변경 시 CSS token, radius, 상태 UI, 접근성 항목을 다시 점검한다.
- [ ] emoji icon을 새로 추가하지 말고 가능하면 SVG 또는 텍스트 label을 사용한다.
- [ ] modal 변경 시 iframe src cleanup과 외부 링크 href를 같이 확인한다.
- [ ] image host 추가 시 backend IMG_PROXY_ALLOW도 확인한다.
- [ ] 정렬 옵션 추가 시 sort state, menu label, render sort field를 같이 갱신한다.
- [ ] 계정 POST route 추가 시 main.py source registry와 input wiring을 확인한다.

### 실패 동작 체크

- [ ] fetch 실패는 `showError`로 source별 inline error를 표시해야 한다.
- [ ] 빈 list는 grid를 비우고 empty/fallback 상태로 전환해야 한다.
- [ ] Threads 빈 posts는 error가 아니라 `showThreadsFallback` 상태로 남아야 한다.
- [ ] YouTube likes sort는 likes 데이터가 없으면 enrich 재요청을 해야 한다.

### 문서 동기화 체크

- [ ] `src/frontend/__init__.py` 라인 수가 3줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/frontend/__init__.py`의 frontend package marker 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/frontend/index.html` 라인 수가 1015줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/frontend/index.html`의 단일 파일 HTML/CSS/JS 프론트엔드 설명이 실제 코드와 어긋나지 않는지 확인한다.

### 테스트 동기화 체크

- [ ] `수동 검증 대상: `/` 또는 `/index.html`이 `src/frontend/index.html`을 반환한다.`가 변경된 계약을 검증하는지 확인한다.
- [ ] `수동 검증 대상: `/api/categories` 결과가 chip으로 표시된다.`가 변경된 계약을 검증하는지 확인한다.
- [ ] `수동 검증 대상: `/api/videos` 결과가 YouTube와 Shorts grid로 표시된다.`가 변경된 계약을 검증하는지 확인한다.
- [ ] `수동 검증 대상: `/api/ai` 결과가 latest/trending/news 세 구역에 표시된다.`가 변경된 계약을 검증하는지 확인한다.
- [ ] `수동 검증 대상: `/api/reels` 결과와 `/api/reels/accounts` POST가 계정 chip에 반영된다.`가 변경된 계약을 검증하는지 확인한다.
- [ ] `수동 검증 대상: `/api/x` 결과가 post card로 표시된다.`가 변경된 계약을 검증하는지 확인한다.
- [ ] `수동 검증 대상: `/api/threads` 빈 결과가 fallback link grid로 표시된다.`가 변경된 계약을 검증하는지 확인한다.
- [ ] `수동 검증 대상: `/api/tiktok` 결과가 shorts grid로 표시된다.`가 변경된 계약을 검증하는지 확인한다.

## 변경 기록

- 2026-07-07: 실제 소스 기준으로 str_func 모듈 문서를 작성했다.

## 문서 연결

- [ ] 동기화 보강 1: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 2: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 3: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 4: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 5: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 6: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 7: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 8: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 9: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 10: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 11: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 12: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 13: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 14: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 15: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 16: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 17: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 18: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 19: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 20: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 21: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 22: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 23: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 24: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 25: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 26: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 27: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 28: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 29: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 30: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 31: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 32: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 33: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 34: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 35: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 36: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 37: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 38: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 39: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 40: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 41: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 42: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 43: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 44: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 45: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 46: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 47: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 48: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 49: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 50: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 51: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 52: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 53: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 54: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 55: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 56: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 57: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 58: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 59: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 60: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 61: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 62: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 63: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 64: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 65: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 66: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 67: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 68: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 69: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 70: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 71: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 72: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 73: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 74: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 75: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 76: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 77: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 78: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 79: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 80: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 81: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 82: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 83: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 84: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 85: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 86: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 87: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 88: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 89: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 90: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 91: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 92: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 93: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 94: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 95: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 96: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 97: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 98: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 99: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 100: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 101: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 102: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 103: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 104: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 105: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 106: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 107: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 108: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 109: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 110: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 111: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 112: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 113: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 114: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 115: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 116: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 117: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 118: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- 이전: [[ai_news.md]]
- 다음: [[shared.md]]
---
# frontend.md — 프론트엔드 모듈 문서

trend-viewer의 단일 HTML 프론트엔드(`src/frontend/index.html`)의 구조와 구현 결정을 기록한다.

## 개요

Python stdlib 서버가 서빙하는 단일 HTML 파일. 외부 의존성은 Pretendard Variable 폰트(CDN)뿐이다.
다크 테마 기반의 데이터 밀도 높은 트렌드 조회 도구로, 7개 소스 탭을 제공한다.

## 아이콘 시스템

WP1(2026-07-07)에서 모든 emoji UI 요소를 SVG 스프라이트 시스템으로 교체했다.
`<body>` 직후 숨김 `<svg>` 블록에 28개 Lucide 호환 `<symbol>` 정의.
`.icon` / `.icon-sm` / `.icon-md` / `.icon-lg` CSS 클래스로 크기 제어.
`<svg class="icon icon-sm"><use href="#i-search"/></svg>` 패턴으로 참조.

## 접근성

- 탭: `role="tablist"` + `aria-selected`, 화살표 키 순환 탐색
- 정렬 메뉴: `aria-haspopup="listbox"` + `aria-expanded`
- 모달: `role="dialog"` + `aria-modal="true"`, Escape 닫기, 클릭 외부 닫기
- 포커스: `:focus-visible` 링 (accent2 블루)
- 건너뛰기: `.skip-link` → `#main`
- `prefers-reduced-motion` 지원

## 인증 폴백

Instagram Reels와 Threads는 무인증 API 접근이 차단될 수 있다.
두 탭 모두 데이터 fetch 실패 시 등록된 계정의 직접 링크 카드를 보여주는 폴백 패턴을 구현:
- `showReelsFallback()`: 각 계정의 인스타그램 릴스 페이지 링크
- `showThreadsFallback()`: 각 계정의 스레드 프로필 링크

## CSS 토큰

jaw-marketing 분석(090)에서 가져온 토큰 계층:
- `--surface-1~4`: 깊이별 배경색
- `--border-hover`, `--border-active`: 상태별 테두리
- `--c-youtube`, `--c-reels`, `--c-x` 등: 플랫폼 색상
- `--transition-fast/transition/transition-slow`: 모션 토큰
- `--shadow-sm/md/lg`: 그림자

