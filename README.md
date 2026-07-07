# trend-viewer

`trend-viewer`는 유튜브 인기 영상과 쇼츠, 인스타 릴스, X, 스레드, 틱톡,
AI 영상 모델/뉴스를 한 화면에서 훑어보는 로컬 트렌드 관제판이다.

원본은 `_upstream/`의 단일 파일 프로토타입이다. 이 저장소는 그 기능을
Python 표준 라이브러리만 쓰는 feature-based 구조로 포팅한 버전이다.
별도 패키지 설치 없이 실행하는 약속을 유지하면서, 수집 모듈과 프론트엔드,
캐시, 계정 설정, 저장 기능을 분리했다.

![trend-viewer desktop screenshot](docs/screenshot-dashboard-desktop.jpg)

모바일 폭에서도 주요 탐색/필터/카드 흐름을 유지한다.

![trend-viewer mobile screenshot](docs/screenshot-dashboard-mobile.jpg)

## 왜 쓰나

트렌드는 플랫폼마다 흩어져 있다. 유튜브는 조회수와 기간 필터가 중요하고,
릴스와 틱톡은 계정 기반 흐름을 봐야 하며, X와 스레드는 링크 미리보기와
텍스트 맥락이 중요하다. `trend-viewer`는 이 흐름을 매번 여러 탭으로 열지
않고, 로컬 브라우저 한 장에서 비교할 수 있게 만든다.

이 앱은 서버에 로그인 정보를 올리지 않는다. 계정 목록과 캐시는 로컬 파일로
관리한다. 인스타그램과 스레드처럼 비로그인 접근이 불안정한 플랫폼은 가능한
공개 엔드포인트를 먼저 시도하고, 데이터가 막히면 바로가기 폴백을 보여준다.

## 바로 실행

```bash
python3 src/main.py
```

브라우저에서 아래 주소를 연다.

```text
http://localhost:8779
```

포트를 바꾸려면 환경 변수를 지정한다.

```bash
TREND_VIEWER_PORT=8780 python3 src/main.py
```

## 주요 기능

- 영상/쇼츠: 유튜브 InnerTube 기반 검색, 카테고리, 기간, 정렬, 검색어 필터
- 릴스: 인스타그램 공개 프로필 수집 시도, 차단 시 계정 바로가기 폴백
- X: syndication API 기반 계정 타임라인 수집
- 스레드: GraphQL 수집 시도와 계정 바로가기 폴백
- 틱톡: 공개 API 기반 트렌딩/계정 피드 수집
- AI: AI 영상 모델과 관련 뉴스 피드
- 공통: 1시간 캐시, 이미지 프록시, 저장 항목 API, 반응형 단일 HTML UI

## 계정 설정

런타임 계정 파일은 `config/*_accounts.json` 형식이다. 이 파일들은 개인 설정이라
git에 올리지 않는다.

예시는 아래처럼 구성한다.

```json
[
  "xazinga",
  "openai"
]
```

대상 파일은 플랫폼별로 나뉜다.

| 플랫폼 | 파일 |
| --- | --- |
| 릴스 | `config/reels_accounts.json` |
| X | `config/x_accounts.json` |
| 스레드 | `config/threads_accounts.json` |
| 틱톡 | `config/tiktok_accounts.json` |

## 구조

```text
src/
├── main.py          # HTTP 서버, 라우팅, 정적 HTML 제공
├── settings.py      # 포트, 경로, 캐시, 이미지 프록시 허용 도메인
├── frontend/        # 단일 HTML/CSS/JS 프론트엔드
├── shared/          # HTTP, 캐시, 계정, 이미지 프록시, 저장 항목
├── youtube/         # 유튜브 영상/쇼츠 수집
├── reels/           # 인스타 릴스 수집
├── x_twitter/       # X 타임라인 수집
├── threads/         # 스레드 수집과 폴백
├── tiktok/          # 틱톡 수집
└── ai_news/         # AI 모델/뉴스 수집
```

폴더명은 Python import 제약 때문에 `snake_case`를 쓴다. 각 기능은
`*_tool.py`와 colocated `test_*.py`로 묶는다.

## 개발 확인

테스트는 Python 표준 라이브러리의 `unittest`로 실행한다.

```bash
python3 -m unittest discover -s src -p 'test_*.py'
```

README 스크린샷은 로컬 서버를 띄운 뒤 브라우저에서 캡처한 실제 화면이다.

## 문서

- 포팅 계획: `devlog/_plan/010_porting-plan.md`
- 프론트엔드 정책: `devlog/_plan/020_frontend-policy.md`
- jaw-marketing 비교 분석: `devlog/_plan/090_jaw-marketing-analysis.md`
- 기능별 구조 문서: `devlog/str_func/`
- 완료된 작업 로그: `devlog/_fin/`

## 변경 기록

- 2026-07-07: `xazingatrend/trend-viewer` 초기 공개용 README와 실제 앱 스크린샷 추가
- 2026-07-07: 단일 파일 프로토타입을 stdlib 기반 feature 구조로 포팅
