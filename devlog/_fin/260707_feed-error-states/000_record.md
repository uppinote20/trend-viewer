# Feed Error States Record

## 이야기

이번 작업은 백엔드가 `/api/x`, `/api/reels`, `/api/threads`에 추가하는 `status`, `errors`, `cacheTtl` 계약을 프론트엔드가 방어적으로 받아들이도록 맞춘 것이다. 기존 payload처럼 `status`가 없으면 지금의 빈 상태와 계정 바로가기 fallback을 그대로 유지하고, 새 계약에서 `error` 또는 `blocked`가 오면서 항목이 0개인 경우에만 수집 실패 UI로 분기했다.

공통 표시 로직은 `src/frontend/index.html:486`부터 `src/frontend/index.html:529`에 모았다. 오류 종류와 HTTP code를 묶어 `429 요청 제한 · 5개 계정 실패` 같은 문장으로 보여주고, 강한 문구는 `일시적으로 가져오지 못했습니다`로 통일했다. 부분 실패는 `src/frontend/index.html:572`의 `renderFeedStatus()`와 `src/frontend/index.html:1764`의 홈 전용 안내를 통해 `N개 계정은 이번 수집에서 실패했습니다.` 한 줄만 muted 톤으로 붙인다.

릴스 탭은 `src/frontend/index.html:1216`에서 `res.ok`를 먼저 확인하도록 바꿨고, 오류 상태에서 항목이 없으면 `src/frontend/index.html:1228`의 error-inline 경로를 사용한다. 계정이 있고 `status`가 비어 있거나 `empty`인 응답은 기존처럼 `src/frontend/index.html:1230`의 계정 바로가기 fallback으로 남는다.

X/스레드 탭도 같은 방식으로 `src/frontend/index.html:1835`에서 HTTP 실패를 먼저 걸러낸다. 항목이 없을 때 `src/frontend/index.html:1847`에서 계약 오류를 먼저 보고, 그 외에는 스레드 fallback과 기존 empty copy를 유지한다.

홈 브리핑은 섹션 단위로 같은 기준을 적용했다. 각 섹션 payload에서 항목이 있으면 정상 렌더 후 `partial` 안내만 붙이고, 항목이 없으면서 `error` 또는 `blocked`이면 `src/frontend/index.html:1799`에서 empty copy 대신 error-inline을 보여준다.

캐시 문구는 기존 `cacheAgeText()`가 이미 payload의 `cacheTtl`을 사용하고 있었다. 이번 변경에서는 `src/frontend/index.html:555`의 그 흐름을 유지했고, `src/frontend/index.html:97`의 cache-age 컨테이너만 여러 줄 안내를 자연스럽게 담도록 flex column으로 바꿨다.

---

## 변경 기록

### `src/frontend/index.html` — 피드 계약 상태별 UI 분기
- **Changes**: X/릴스/스레드용 계약 오류 요약, partial 안내, `res.ok` 체크, 홈 섹션별 error/partial 분기를 추가했다.
- **Impact**: 백엔드가 새 additive contract를 내려도 레거시 payload는 기존 동작을 유지하고, 전 계정 수집 실패와 빈 결과/fallback을 사용자가 구분할 수 있다.
- **Verification**: `node --check /tmp/trend_viewer_inline.js` 통과. `python3 -m unittest discover -s src -p 'test_*.py'` → 60 tests OK. `TREND_VIEWER_PORT=8797 python3 src/main.py` 후 `GET /` smoke → `smoke ok: 96978`.
