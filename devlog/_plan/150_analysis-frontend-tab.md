---
created: 2026-07-10
tags: [trend-viewer, analysis-tab, frontend, responsive-UI, browser-QA]
aliases: [분석 프론트엔드 계획, WP4 분석 탭, analysis frontend tab]
---

# 150 — 분석 프론트엔드 탭 (WP4)

이 계획은 `/api/analysis` 결과를 기존 단일 파일 프론트엔드에 연결한 WP4의 실제
구현 계약을 기록한다. 분석은 급상승 다음의 핵심 탭으로 배치한다. cluster 카드에는
제목, momentum, 플랫폼, 설명, keyword, 검증된 근거 링크를 보여준다.

분석 요청은 다른 홈 소스보다 오래 걸릴 수 있다. 홈 전체 렌더를 기다리게 하지 않고
별도 비동기 요청으로 분석 섹션을 채운다. 프록시가 없을 때는 오류 화면 대신 조용한
휴리스틱 상태를 표시한다. WP4는 2026-07-10에 감사된 REV 2 계획을 실행했고,
데스크톱·모바일·홈 화면과 콘솔 오류를 확인한 상태로 마쳤다.

---

## 실행 상태

- 상태: 완료
- 실행일: 2026-07-10
- 감사: REV 2, GO-WITH-FIXES 6건 반영
- 선행 조건: [[140_analysis-synthesis-api.md]]의 응답 계약
- 구현 표면: `src/frontend/index.html`

## 범위

### 포함

- `analysis` view와 탭 navigation을 추가한다.
- LLM·휴리스틱 상태, briefing, cluster, 근거 링크를 렌더한다.
- 국가 변경, URL hash, 강제 새로고침, 숫자 단축키 흐름에 분석 탭을 연결한다.
- 홈 브리핑에 blocking 없는 별도 분석 섹션을 추가한다.
- 데스크톱 1440px와 모바일 390px에서 화면과 콘솔을 확인한다.

### 제외

- 서버 분석 알고리즘과 응답 스키마는 바꾸지 않는다.
- React, 번들러, 외부 icon package를 추가하지 않는다.
- 분석 cluster 카드 전체를 클릭 대상으로 만들지 않는다.
- 분석 요청을 `HOME_SECTIONS`의 blocking `Promise.all`에 넣지 않는다.

## Diff-level 파일 지도

| 경로 | 작업 | 구현 계약 |
|---|---|---|
| `src/frontend/index.html` | MODIFY | 분석 색상 token, SVG symbol, view, nav, loader, renderer, 홈 비동기 섹션, 국가 invalidation을 추가한다. |
| `devlog/str_func/analysis.md` | NEW | 분석 모듈과 프론트 소비 계약을 필수 섹션을 갖춘 전체 문서로 고정한다. |
| `devlog/str_func/AGENTS.md` | MODIFY | `src/analysis/` 문서를 완료 상태로 인덱싱한다. |
| `docs/screenshot-analysis-desktop.png` | NEW | 1440px 분석 탭의 검증된 데스크톱 화면을 README에 제공한다. |

## View 등록 계약

`VIEWS`에서 분석은 `trends` 바로 뒤에 둔다.

```javascript
{
  id: 'analysis',
  label: '분석',
  svgIcon: 'i-sparkles',
  color: '--c-analysis',
  elementId: 'analysisView',
  load: (force) => loadAnalysis(force),
  toolbar: 'countries',
  hasForce: true,
}
```

- `--c-analysis`는 카드 전체를 덮지 않고 강조선·chip·상태에만 사용한다.
- `analysisView`는 `analysisStatus`, `analysisBrief`, `analysisGrid`를 소유한다.
- 숫자 단축키는 `VIEWS` 순서를 그대로 사용하므로 분석 삽입 뒤 3번이 분석이 된다.
- evidence link를 가진 cluster 카드는 `wireCardAction`으로 감싸지 않는다.

## 로딩과 경쟁 요청 계약

- `analysisSeq`가 오래된 응답의 렌더를 막는다.
- `analysisController`는 새 요청 전에 이전 요청을 abort한다.
- 요청 상한은 90초이며 첫 분석이 길 수 있다는 상태 문구를 표시한다.
- 요청 시작 시 이전 briefing, 상태 chip, grid를 지운다.
- HTTP non-OK는 오류 경로로 보낸다.
- `AbortError`는 시간 초과 안내를 표시한다.
- 현재 sequence가 아닌 응답과 오류는 화면을 바꾸지 않는다.
- 완료되면 응답의 `fetchedAt`과 `cacheTtl`을 공통 cache age helper로 표시한다.

## 응답 상태 계약

| 조건 | 화면 동작 |
|---|---|
| cluster 있음, `llm.ok=true` | 모델 이름과 LLM briefing을 표시한다. |
| cluster 있음, `llm.ok=false` | `휴리스틱 분석` chip과 정상 cluster를 표시한다. |
| cluster 있음, errors 있음 | 결과를 유지하고 일부 채널 실패 문구를 덧붙인다. |
| cluster 없음, errors 없음 | 분석할 흐름이 없다는 빈 상태를 표시한다. |
| cluster 없음, errors 있음 | 수집 실패를 반영한 빈 상태를 표시한다. |
| briefing 없음 | briefing band를 숨긴다. |
| velocity baseline 없음 | momentum은 응답값대로 렌더하고 baseline 없음 상태를 허용한다. |

## Cluster 카드 계약

- title과 keyword는 긴 문자열도 카드 폭 안에서 줄바꿈한다.
- momentum은 `rising`, `steady`, `cooling`에 맞는 icon과 색을 사용한다.
- 플랫폼은 분석 전용 `.an-badge`로 표시한다.
- `why`는 세 줄로 제한해 카드 높이 변동을 줄인다.
- keyword는 최대 다섯 개를 chip으로 표시한다.
- evidence는 `safeUrl`을 통과한 `http`·`https` 링크만 만든다.
- evidence row는 카드 안에서 다시 테두리 카드처럼 보이지 않게 한다.
- evidence link가 있으므로 카드 자체 클릭과 키보드 action은 붙이지 않는다.

## 홈 통합 계약

- `HOME_SECTIONS`에는 분석을 넣지 않는다.
- `HOME_ANALYSIS_SECTION`은 분석 섹션 metadata만 따로 가진다.
- `loadHomeAnalysis`는 기본 홈 source fetch와 독립적으로 시작한다.
- 대기 중에는 분석 섹션 안에 5개 skeleton row를 표시한다.
- 성공하면 cluster 최대 5개와 briefing을 표시한다.
- cluster의 첫 evidence URL을 홈 row의 이동 링크로 사용한다.
- 실패하면 분석 홈 section만 조용히 제거한다.
- 별도 요청이므로 분석 지연이 급상승·영상·데이트 등 홈 섹션을 막지 않는다.

## 국가와 URL 상태 계약

- 분석 요청에는 `state.country`를 넣는다.
- 국가 변경 시 `loadedViews.delete('analysis')`를 실행한다.
- 현재 탭이 분석이면 `loadAnalysis()`를 즉시 호출한다.
- 홈도 국가별 분석을 포함하므로 국가 변경 시 `home` loaded state를 지운다.
- 분석 탭 ID는 공통 hash 복원 로직을 그대로 사용한다.
- refresh action은 `hasForce: true`를 따라 `force=1` 요청을 만든다.

## 완료 기준

- [x] 분석 탭이 급상승 바로 뒤에 표시되고 국가 toolbar를 사용한다.
- [x] LLM 성공과 휴리스틱 폴백이 같은 cluster 레이아웃으로 보인다.
- [x] 긴 제목·keyword·evidence가 카드 경계를 넘지 않는다.
- [x] evidence 링크만 클릭 가능하며 cluster 카드에 중첩 action이 없다.
- [x] 새 분석 요청이 이전 요청을 취소하고 stale 응답을 무시한다.
- [x] 홈 분석이 기본 `HOME_SECTIONS` 렌더를 지연시키지 않는다.
- [x] 국가 변경이 분석 탭과 홈 분석 cache state를 무효화한다.
- [x] 데스크톱 분석 탭 스크린샷을 1440px viewport에서 확인했다.
- [x] 모바일 분석 탭과 홈 화면을 확인했다.
- [x] 데스크톱·모바일·홈 검증에서 콘솔 오류가 0건이었다.

## 변경 기록

- 2026-07-10: 감사 반영 뒤 WP4를 실행하고 분석 탭·홈 비동기 통합을 완료했다.

## 문서 연결

- 이전: [[140_analysis-synthesis-api.md]]
- 다음: [[../str_func/frontend.md]]
