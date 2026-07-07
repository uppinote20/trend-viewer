---
created: 2026-07-07
tags: [CI, GitHub-Actions, unittest, lint]
aliases: [CI 파이프라인, CI 계획]
---

# CI 파이프라인 계획

trend-viewer의 지속적 통합(CI) 전략을 정리한다.

## 무엇을 자동화하나

이 프로젝트는 Python 표준 라이브러리만 쓰므로 의존성 설치 단계가 없다.
CI에서 확인할 것은 두 가지다.

1. **단위 테스트**: `python3 -m unittest discover -s src -p 'test_*.py'`
2. **정적 분석/린트**: 향후 `ruff` 또는 `flake8` 추가 시 여기에 단계 추가

## 1단계: GitHub Actions unittest (구현 완료)

`.github/workflows/test.yml`에 기본 워크플로를 배치했다.

- 트리거: `push`(main), `pull_request`(main)
- 매트릭스: Python 3.11, 3.12, 3.13
- 단계: checkout -> python setup -> unittest discover
- 외부 API 호출은 전부 mock 처리이므로 네트워크 없이 통과한다

## 2단계: 린트 (향후)

`ruff`를 도입하면 `ruff check src/`를 CI에 추가한다. stdlib only 프로젝트라
`pip install ruff`만 추가하면 된다.

## 3단계: 릴리스 (향후)

버전 태깅이 필요해지면 `git tag v0.x.x` + GitHub Release를 자동화한다.

---

## 변경 기록

- 2026-07-07: 초기 CI 계획 문서 작성, test.yml 구현
