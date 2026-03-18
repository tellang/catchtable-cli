# CatchTable CLI (ct)

캐치테이블(CatchTable) 서비스를 터미널에서 이용할 수 있는 비공식 CLI 도구입니다.
AI 에이전트 친화적 설계(Agent DX)를 적용하여 자동화 파이프라인에서도 안정적으로 동작합니다.

## 주요 기능

- **매장 검색 (`search`)**: 위치, 음식 종류, 날짜, 인원수 기반 검색
- **지역 검색 (`search region`)**: 지역 기반 매장 탐색
- **매장 정보 (`shop info`)**: 특정 매장의 상세 정보 조회
- **JSON-First 출력**: `--json` 플래그로 구조화된 JSON 출력
- **스키마 자체검사**: `ct schema` 명령으로 입출력 스키마 확인
- **입력 검증**: 잘못된 인자에 대해 명확한 오류 메시지 제공
- **dry-run 모드**: 실제 API 호출 없이 요청 미리보기

## 설치

Python 3.11 이상이 필요합니다.

```bash
pip install catchtable-cli
```

또는 소스에서 설치:

```bash
git clone https://github.com/tellang/catchtable-cli.git
cd catchtable-cli
pip install -e .
```

## 사용법

```bash
# 매장 검색
ct search "스시" --location "강남" --date 2026-03-20 --party-size 2

# JSON 형식 출력
ct search "한우" --json

# 매장 상세 정보
ct shop info SHOP_ID

# 스키마 확인
ct schema

# 버전 / 개요
ct version
ct overview
```

## 환경 변수

`.env` 파일을 프로젝트 루트에 생성하세요.

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `CT_API_BASE_URL` | API 엔드포인트 | `https://api.catchtable.co.kr` |
| `CT_AUTH_TOKEN` | 인증 토큰 | (필수) |

## 프로젝트 구조

```
catchtable-cli/
├── catchtable_cli/
│   ├── __init__.py
│   ├── cli.py           # Typer 앱 진입점
│   ├── client.py        # HTTP API 클라이언트
│   ├── config.py        # 환경 변수 설정
│   ├── models.py        # 데이터 모델
│   ├── schema.py        # 입출력 스키마 정의
│   ├── validate.py      # 입력 검증 로직
│   └── commands/
│       ├── __init__.py
│       ├── search.py    # 검색 커맨드
│       └── shop.py      # 매장 정보 커맨드
├── pyproject.toml
└── README.md
```

## 라이선스

MIT
