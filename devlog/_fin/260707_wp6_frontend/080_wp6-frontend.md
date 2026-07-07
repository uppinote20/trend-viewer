# 080 — WP6: frontend 분리 + 020 폴리시 적용 (diff-level plan)

## Loop-spec

- **Loop archetype**: spec-satisfaction repair
- **Trigger**: HOTL 루프 WP6 — 010 계획의 P7
- **Goal**: `_upstream/index.html` 893줄을 `src/frontend/`로 분리하고 020 폴리시
  (Pretendard, tabular-nums, 스켈레톤 로더, 빈/에러 상태, 접근성, 카드 8px)를 적용.
  서버가 `src/frontend/index.html`을 서빙하고 7개 탭이 동작.
- **Non-goals**: 서버 백엔드 변경(WP1-5 완료), str_func 문서(WP7)
- **Verifier**: 서버 기동 → 7탭 브라우저 렌더 (C-RENDER-GROUNDING-01: 헤드리스
  스크린샷 + 실제 관찰), 020 폴리시 체크리스트 코드 검사
- **Stop condition**: verifier 통과
- **Expected terminal outcomes**: DONE
- **HOTL resource bounds**: worker 1(gpt-5.5), 쓰기범위 `src/frontend/`, `src/main.py`
  (index 서빙 경로만)

## 파일 변경 맵

| 파일 | 작업 |
|---|---|
| `src/frontend/index.html` | `_upstream/index.html` 기반 + 020 폴리시 교정 적용. 단일 파일 유지 (vanilla 스택 — CSS/JS inline). 변경점: (1) Pretendard Variable CDN link 추가, font-family 교체, (2) `.views`등 숫자에 `font-variant-numeric:tabular-nums`, (3) 카드 `border-radius:12px` → `8px`, (4) 로딩 상태: `.status` 텍스트 → 카드 크기 스켈레톤 `.skeleton-card` 애니메이션 (shimmer gradient, transform/opacity만), (5) 빈 상태: 검색 0건/계정 0개 시 안내 메시지, (6) 에러 상태: 소스별 인라인 에러 `.error-inline`, (7) 탭 `role="tablist"` + `aria-selected`, 버튼 `<button>`, (8) `:focus-visible` 링 `outline:2px solid var(--accent2)`, (9) `@media (prefers-reduced-motion:reduce)` 모든 애니메이션 비활성, (10) 카드 `:active` `scale(0.98)`, (11) 이미지 `loading="lazy"` |
| `src/main.py` | 수정 — index 서빙 경로를 `_upstream/index.html` → `src/frontend/index.html`로 변경 (os.path.join(BASE_DIR, "frontend", "index.html")) |

**IN**: 위 2파일. **OUT**: 그 외. `_upstream/` 절대 수정 안 함.

## 020 폴리시 체크리스트 (수용 기준과 동일)

1. Pretendard Variable 로드 (`<link>` CDN) + body `font-family` 교체.
2. 숫자 요소에 `font-variant-numeric: tabular-nums` 적용.
3. 카드 `border-radius` ≤ 8px.
4. 스켈레톤 로더 (카드 크기, shimmer, 원형 스피너 없음).
5. 빈 상태 UI (검색 0건, 계정 0개).
6. 에러 상태 UI (소스별 인라인, alert() 없음).
7. 탭 `role="tablist"` + `aria-selected`, 버튼 시맨틱.
8. `:focus-visible` 링.
9. `prefers-reduced-motion` 지원.
10. 카드 `:active` tactile (`scale(0.98)`).
11. 이미지 `loading="lazy"`.
12. compileall + unittest 기존 45개 통과 (프론트 변경이 백엔드 깨지 않음).
13. 서버 기동 후 index 서빙 확인 (`curl -sI :8779/` → 200 text/html).
