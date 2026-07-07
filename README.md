# trend-viewer

유튜브 인기 영상·쇼츠, 인스타 릴스, X, 스레드, 틱톡, AI 영상 모델/뉴스를 하루 한 곳에서 보는 로컬 웹앱.
`데일리-트렌드-뷰어` 단일 파일 프로토타입(`_upstream/`)을 기능 단위 모듈 구조로 포팅하는 프로젝트다.

## Quick start (현재: 업스트림 그대로 실행)

```bash
python3 _upstream/server.py
# http://localhost:8778
```

포팅 완료 후에는 `python3 src/main.py`로 실행한다.

## Architecture (target)

```
src/
├── main.py            # 엔트리포인트: HTTP 서버 기동 + 라우팅 등록
├── shared/            # http 클라이언트, 캐시, 계정 저장, 이미지 프록시
├── youtube/           # InnerTube 검색 기반 영상/쇼츠 (+좋아요 보강)
├── reels/             # 인스타그램 web_profile_info 무인증 수집
├── x_twitter/         # syndication API 타임라인 수집
├── threads/           # GraphQL 시도 + 바로가기 폴백
├── tiktok/            # tikwm 공개 API (트렌딩 + 계정)
├── ai_news/           # 구글 뉴스 RSS + Hugging Face 모델
└── frontend/          # index.html → 분리된 정적 자산
```

폴더명은 파이썬 패키지 임포트 제약 때문에 kebab-case 대신 snake_case를 쓴다.

원칙: **Python 표준 라이브러리만 사용** (업스트림의 "설치 없이 실행" 약속 유지).

## Docs

- 업스트림 분석: `devlog/_plan/000_upstream-analysis.md`
- 포팅 계획: `devlog/_plan/010_porting-plan.md`
- 모듈 문서: `devlog/str_func/`
