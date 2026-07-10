---
created: 2026-07-07
tags: [trend-viewer, implementation-plan, porting, analysis-engine]
aliases: [trend-viewer 계획 인덱스, devlog plan index]
---

# devlog/_plan

이 디렉터리는 구현 전 조사, 감사, 정책, 단계별 실행 계획을 번호순으로 보관한다.
완료된 계획도 후속 작업의 근거가 되면 이 인덱스에 남긴다. 상태는 현재 저장소의
실제 구현과 남은 범위를 기준으로 `완료` 또는 `진행`으로 표시한다.

---

| 문서 | 내용 | 상태 |
|---|---|---|
| `000_upstream-analysis.md` | 단일 파일 업스트림의 서버·프론트·외부 계약 분석 | 완료 |
| `010_porting-plan.md` | P1-P8 기능 모듈 포팅 계획; 단일 HTML 분리와 일부 문서화가 남음 | 진행 |
| `020_frontend-policy.md` | 현재 프론트엔드의 토큰·상태·접근성·금지 규칙 | 완료 |
| `090_jaw-marketing-analysis.md` | jaw-marketing 패턴의 선택적 도입 가능성 분석 | 완료 |
| `100_ci-pipeline.md` | unittest CI는 구현됨; 린트와 릴리스 자동화는 후속 범위 | 진행 |
| `110_logic-audit.md` | 트렌드 신호·국가·AI 뉴스 수집 로직 정합성 감사 | 완료 |
| `120_channel-research.md` | 무인증 수집 채널과 국가별 응답 형식 실측 | 완료 |
| `130_analysis-engine.md` | WP2 stdlib SSE 클라이언트와 7채널 휴리스틱 분석 | 완료 |
| `140_analysis-synthesis-api.md` | WP3 근거 기반 LLM 합성과 `/api/analysis` 계약 | 완료 |
| `150_analysis-frontend-tab.md` | WP4 분석 탭, 홈 비동기 섹션, 반응형 QA | 완료 |

## 상태 관리

- [x] 000-150 범위의 현재 계획 문서를 번호순으로 인덱싱했다.
- [x] 분석 엔진 WP2-WP4의 실행 완료 상태를 반영했다.
- [ ] 포팅 계획 P7의 프론트엔드 파일 분리 여부를 후속 작업에서 재검토한다.
- [ ] CI 계획의 린트·릴리스 범위를 실제 도입 시 별도 계획으로 구체화한다.

## 변경 기록

- 2026-07-10: 000-150 계획 문서와 현재 완료·진행 상태를 다시 맞췄다.
- 2026-07-07: 초기 계획 인덱스를 작성했다.

## 문서 연결

- 다음: [[000_upstream-analysis.md]]
