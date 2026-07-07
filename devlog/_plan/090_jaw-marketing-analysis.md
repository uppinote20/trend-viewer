# 090 — jaw-marketing 기반 개선 분석

jaw-marketing(React+Vite+TS 멀티플랫폼 발행 대시보드)의 devlog, 디자인 시스템,
컴포넌트 아키텍처, API 레이어를 분석해 trend-viewer에 적용 가능한 개선점을 정리한다.
4개 gpt-5.5 서브에이전트 병렬 탐색 결과를 종합.

---

## 핵심 판단

trend-viewer는 "설치 없이 더블클릭으로 켜는 로컬 트렌드 관제판"이다. React/Vite
전면 전환은 이 약속과 충돌하므로 비추천(35/100). 대신 jaw-marketing의 설계 패턴을
**stdlib 방식으로 흡수**하는 게 훨씬 낫다.

## 가져올 패턴 (우선순위순)

### 1. View Registry (탭 전환 데이터 기반화) — 추천 90

jaw-marketing의 `SidebarRail` items 배열 + `App.tsx` view switch 패턴을 vanilla JS로.
현재 trend-viewer는 탭 버튼/view div/load 함수/refresh 분기가 7곳에 하드코딩되어 있다.

```js
const VIEWS = [
  { id: 'youtube', label: '영상', icon: '📺', color: '--c-youtube',
    elementId: 'videoView', load: loadVideos, toolbar: 'categories' },
  { id: 'shorts', label: '쇼츠', ... },
  // ...
];
```

탭 생성, display 토글, refresh dispatcher, skeleton/empty/error 렌더링을
`VIEWS` 배열 기반으로 공통화하면 새 소스 추가 시 수정 지점이 1곳으로 줄어든다.

### 2. CSS 토큰 확장 — 추천 85

jaw-marketing의 토큰 계층(`--surface-1~4`, `--border-hover`, `--text-secondary`,
`--transition-fast/slow`, `--shadow-*`)을 trend-viewer에 도입.

특히 **플랫폼 색상 토큰**이 강력하다:
- `--c-youtube: #ff0000`, `--c-shorts: #ff0000`
- `--c-reels: #e1306c`, `--c-tiktok: #00f2ea`
- `--c-x: #000000`, `--c-threads: #000000`
- `--c-ai: var(--accent)`

active 탭 indicator, rank highlight, 필터 chip에 연결하면 "데이터 모음"이 아니라
"플랫폼 워크스페이스"처럼 느껴진다.

모션 토큰도 통일: 현재 `.12s`, `.18s` 흩어진 값을
`--transition-fast: 120ms`, `--transition: 200ms`, `--transition-slow: 350ms`로.

### 3. createTrendCard 카드 쉘 — 추천 80

jaw-marketing의 `PostCard`는 공통 도메인 카드. trend-viewer도 YouTube/Shorts,
Reels/TikTok, X/Threads 카드 렌더 함수에 중복이 많다.

```js
function createTrendCard({ thumbnail, rank, title, metaNodes, onClick, variant }) { ... }
```

variant로 `video`(16:9 썸네일) / `shorts`(9:13) / `text`(X/Threads 텍스트 프리뷰) /
`article`(AI 뉴스 다이제스트) 분기. 썸네일, 랭크 뱃지, 메타 라인, 클릭 동작이 공통 쉘.

### 4. 상태 렌더링 공통화 — 추천 80

jaw-marketing의 `.queue-empty`, `.post-status-*`, `.toast-*` 패턴을 차용.
`renderState(container, { loading, empty, error, data })` 함수로
skeleton/empty CTA/error-inline/data 렌더를 한 곳에서 처리.

### 5. 계정 관리 + 정렬 메뉴 공통화 — 추천 75

Reels/X/Threads/TikTok 4개 탭의 계정 칩 + 정렬 메뉴가 거의 동일한데 각각 구현.
jaw-marketing의 `PlatformView` 공통 레이아웃처럼 `accountManager(source)` +
`sortMenu(options)` 팩토리로 묶으면 코드 반 이상 줄어든다.

### 6. 저장/북마크 모델 — 추천 75

jaw-marketing의 `Post` queue를 "트렌드 아이템 저장 큐"로 변환:
- `saved_items_tool.py`: `config/saved_items.json` (id, source, title, url, savedAt, note, tags)
- `/api/saved` GET/POST/DELETE — 기존 계정 라우팅 패턴 재사용
- 프론트에 "저장됨" 탭 추가

### 7. 선택적 AI 분석 패널 — 추천 65

jaw-marketing의 `AgentView` health-check + iframe 패턴 차용:
- `/api/agent/health` — jaw/cli-jaw가 로컬에 있으면 200, 없으면 503
- 카드에 "왜 떴을까?" 버튼 → 있을 때만 활성화 → agent에 분석 프롬프트 전송
- 없어도 기본 기능은 0% 영향 (graceful degradation)

### 8. CSS 파일 분리 — 추천 60

jaw-marketing의 `tokens.css / layout.css / components.css / animations.css` 4분할.
trend-viewer도 index.html의 `<style>` 170줄이 더 커지기 전에 분리할 타이밍이긴 하나,
단일 HTML 서빙의 단순함과 트레이드오프. 다음 기능 추가 시 자연스럽게.

### 9. 사이드 Rail 전환 — 추천 50

jaw-marketing의 좌측 `SidebarRail`은 7개 탭에 좋은 대안이지만,
trend-viewer의 현재 상단 탭이 모바일에서도 작동하고 사용자 기대와 맞아서
기존 사용자 입장에서는 변화 비용이 큰 편. 탭이 10개 이상 되면 재고.

### 10. React/Vite 전면 전환 — 비추천 35

double-click run 약속 위반, npm 의존성 추가, 빌드 스텝 필요.
실험용 `frontend-react/`로만 검토, 메인 경로 유지.

## jaw-marketing 참조 파일

| 영역 | 파일 | 핵심 패턴 |
|---|---|---|
| 디자인 토큰 | `src/styles/tokens.css` | surface 계층, 플랫폼 색상, 모션 토큰 |
| 레이아웃 | `src/styles/layout.css` | app-shell 2열 grid, 100dvh, workspace split |
| 모션 | `src/styles/animations.css` | fadeIn/slideUp/shimmer + utility class |
| 뷰 전환 | `src/components/SidebarRail.tsx` | items 배열, group 분리, active indicator |
| 공통 뷰 | `src/platforms/PlatformView.tsx` | 골격 소유 + 플랫폼은 config/slot 주입 |
| 카드 | `src/components/PostCard.tsx` | 공통 도메인 카드 + status 액션 |
| 큐 | `src/components/QueueList.tsx` | empty state, status 정렬 |
| API 클라이언트 | `src/api/jaw-client.ts` | 얇은 래퍼, `{ok, error}` 결과 객체 |
| 저장 | `src/api/storage.ts` | localStorage, QueueState 모델 |
| AI 연동 | `src/views/AgentView.tsx` | health poll + iframe embed |
| 캘린더 | `src/views/CalendarView.tsx` | 날짜별 필터링, 플랫폼 색상 dot |
