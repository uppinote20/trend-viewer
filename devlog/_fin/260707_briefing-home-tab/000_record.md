# 홈 브리핑 탭 구현 기록

오늘 작업은 `trend-viewer`의 첫 화면을 개별 플랫폼 탭이 아니라 하루 단위 브리핑 보드로 바꾸는 것이었다. 기존에는 사용자가 유튜브, 쇼츠, AI, 릴스, X, 스레드, 틱톡 탭을 하나씩 눌러야 전체 흐름을 확인할 수 있었다. 그래서 `src/frontend/index.html:394`의 `VIEWS` 레지스트리 첫 항목에 `home` 탭을 추가하고, `src/frontend/index.html:404`의 초기 `state.tab`과 `src/frontend/index.html:1569`의 초기 `switchTab` 호출을 모두 `home`으로 맞췄다.

홈 화면의 목적은 각 API가 서로 영향을 주지 않는 일일 요약판이다. 이를 위해 `src/frontend/index.html:300`에 `homeView` 섹션을 추가했고, `src/frontend/index.html:1183`의 `HOME_SECTIONS`에서 유튜브 영상, 쇼츠, AI, 릴스, X, 스레드, 틱톡을 고정된 브리핑 소스로 선언했다. 특히 쇼츠는 서버 기본값에 기대지 않도록 `/api/videos?shorts=true&period=week` 형태로 명시했다.

구현 방식은 기존 단일 HTML 구조를 유지하는 쪽으로 잡았다. `src/frontend/index.html:1326`의 `loadHome(force)`는 `Promise.allSettled`로 7개 API를 병렬 호출하고, 실패한 소스만 해당 섹션 안에서 `showError`로 표시한다. 성공했지만 데이터가 비어 있는 소스는 같은 섹션 안에서 `showEmpty`를 표시하므로, 한 플랫폼의 실패나 빈 응답이 다른 플랫폼 목록을 막지 않는다.

화면 구성은 기존 다크 컨트롤 보드 톤을 그대로 따랐다. `src/frontend/index.html:202`부터 홈 전용 CSS를 추가해 반경 8px 이하, `var(--surface-*)` 기반 배경, 88px 썸네일 행, 2줄 제목 클램프를 사용했다. 각 섹션 헤더는 플랫폼 아이콘과 색상 토큰을 사용하고, `src/frontend/index.html:1303`의 chevron 버튼은 `switchTab(section.tab)`으로 전체 탭에 바로 이동한다.

접근성은 기존 탭 생성 흐름을 그대로 재사용했다. `home` 항목이 `VIEWS`에 들어가므로 `renderTabs()`가 자동으로 `role="tab"`, `aria-selected`, `aria-controls="homeView"`를 연결한다. 홈 안의 각 플랫폼 헤더는 `src/frontend/index.html:1297`에서 실제 `h2`로 생성하고, 이동 버튼에는 플랫폼별 `aria-label`을 부여했다.

검증은 다음 명령으로 수행했다.

```bash
python3 -c "import pathlib;h=pathlib.Path('src/frontend/index.html').read_text();assert 'homeView' in h"
TREND_VIEWER_PORT=8791 python3 src/main.py &
curl -s localhost:8791/ | grep -c homeView
```

서버 실행 검증은 로컬 Python stdlib 서버가 HTML을 정상 제공하는지 확인하기 위한 것이다. 실제 외부 API 호출은 네트워크나 플랫폼 제한으로 실패할 수 있지만, 홈 UI는 섹션 단위 오류 표시로 부분 실패를 처리하도록 구성했다.
