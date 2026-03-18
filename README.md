# CatchTable CLI (ct)

캐치테이블(CatchTable) 서비스를 터미널에서 이용할 수 있는 비공식 CLI 도구입니다.
매장 검색, 상세 정보 조회 및 예약 관리 기능을 제공합니다.

> **Note:** 현재 Placeholder API를 사용 중입니다. 실제 API 엔드포인트는 RE 후 교체 예정입니다.

## 주요 기능

- **매장 검색 (`search`)**: 위치, 음식 종류, 날짜, 인원수 기반 검색
- **매장 정보 (`shop info`)**: 특정 매장의 상세 정보 조회
- **예약 관리 (`reserve`)**: 예약 생성 (구현 중)
- **빈자리 알림 (`notify`)**: 취소 자리 실시간 알림 (구현 중)

## 설치

Python 3.11 이상이 필요합니다.

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
│   └── commands/
│       ├── __init__.py
│       ├── search.py    # 검색 커맨드
│       └── shop.py      # 매장 정보 커맨드
├── pyproject.toml
└── README.md
```

## 라이선스

MIT
