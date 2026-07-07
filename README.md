# trend-viewer

유튜브, 쇼츠, 릴스, X, 스레드, 틱톡, AI 모델/뉴스를 한 화면에서 보는
로컬 트렌드 뷰어입니다.

브라우저 탭을 여러 개 열지 않아도 됩니다. `python3 src/main.py`로 켜고,
`http://localhost:8779`에서 오늘 볼 만한 흐름을 바로 훑어보세요.

![trend-viewer desktop screenshot](docs/screenshot-dashboard-desktop.jpg)

모바일 폭에서도 같은 화면을 좁게 정리해서 보여줍니다.

![trend-viewer mobile screenshot](docs/screenshot-dashboard-mobile.jpg)

## 무엇을 해결하나요

트렌드는 플랫폼마다 다르게 보입니다.

유튜브는 조회수, 기간, 카테고리가 중요합니다. 릴스와 틱톡은 계정 흐름을
같이 봐야 합니다. X와 스레드는 텍스트 맥락과 링크가 중요합니다.
`trend-viewer`는 이 흐름을 로컬 브라우저 한 장에 모읍니다.

로그인 정보는 서버로 보내지 않습니다. 계정 목록과 캐시는 이 기기 안의
파일로 관리합니다. 인스타그램과 스레드처럼 비로그인 접근이 자주 막히는
플랫폼은 공개 수집을 먼저 시도하고, 막히면 바로가기 폴백을 보여줍니다.

## 바로 실행하세요

추가 패키지 설치는 필요하지 않습니다. Python 표준 라이브러리만 사용합니다.

```bash
python3 src/main.py
```

실행 후 브라우저에서 엽니다.

```text
http://localhost:8779
```

포트를 바꾸고 싶으면 이렇게 실행합니다.

```bash
TREND_VIEWER_PORT=8780 python3 src/main.py
```

## 볼 수 있는 것

- 영상: 유튜브 인기 영상, 카테고리, 기간, 검색어, 정렬
- 쇼츠: 유튜브 쇼츠 중심 보기
- AI: AI 영상 모델과 관련 뉴스
- 릴스: 인스타그램 공개 프로필 수집, 막히면 계정 바로가기
- X: syndication API 기반 계정 타임라인
- 스레드: GraphQL 수집 시도, 막히면 계정 바로가기
- 틱톡: 공개 API 기반 트렌딩/계정 피드
- 공통: 1시간 캐시, 이미지 프록시, 저장 항목 API, 반응형 UI

## 계정 목록을 넣으세요

계정 기반 피드를 보려면 `config/*_accounts.json` 파일을 만듭니다.
이 파일들은 개인 설정이라 git에 올리지 않습니다.

예시는 아래와 같습니다.

```json
[
  "xazinga",
  "openai"
]
```

| 플랫폼 | 파일 |
| --- | --- |
| 릴스 | `config/reels_accounts.json` |
| X | `config/x_accounts.json` |
| 스레드 | `config/threads_accounts.json` |
| 틱톡 | `config/tiktok_accounts.json` |

## 프로젝트 구조

원본은 `_upstream/`의 단일 파일 프로토타입입니다. 현재 버전은 같은 기능을
기능별 모듈로 나눠 포팅한 구조입니다.

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

Python import 규칙 때문에 폴더명은 `snake_case`를 씁니다. 각 기능은
`*_tool.py`와 `test_*.py`를 같은 폴더에 둡니다.

## 확인 방법

테스트는 `unittest`로 실행합니다.

```bash
python3 -m unittest discover -s src -p 'test_*.py'
```

README의 스크린샷은 로컬 서버를 띄운 뒤 실제 앱 화면을 캡처한 이미지입니다.

## 더 읽을 문서

- 포팅 계획: `devlog/_plan/010_porting-plan.md`
- 프론트엔드 정책: `devlog/_plan/020_frontend-policy.md`
- jaw-marketing 비교 분석: `devlog/_plan/090_jaw-marketing-analysis.md`
- 기능별 구조 문서: `devlog/str_func/`
- 완료된 작업 로그: `devlog/_fin/`

## 변경 기록

- 2026-07-07: README 문체를 한국어 UX writing 기준으로 조정
- 2026-07-07: `xazingatrend/trend-viewer` 초기 공개용 README와 실제 앱 스크린샷 추가
- 2026-07-07: 단일 파일 프로토타입을 stdlib 기반 feature 구조로 포팅
