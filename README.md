# CatchTable CLI (ct)

**캐치테이블(CatchTable) 맛집 예약 플랫폼의 검색 및 매장 조회를 위한 에이전트 친화적(Agent DX) 비공식 CLI 도구**

[![PyPI version](https://img.shields.io/pypi/v/catchtable-cli?color=blue)](https://pypi.org/project/catchtable-cli/)
[![Python Version](https://img.shields.io/pypi/pyversions/catchtable-cli)](https://pypi.org/project/catchtable-cli/)
[![Agent DX 70/70](https://img.shields.io/badge/Agent%20DX-70%2F70-brightgreen)](https://github.com/tellang/catchtable-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`catchtable-cli`는 캐치테이블의 매장 검색, 지역 탐색, 상세 정보를 터미널 환경에서 빠르게 조회할 수 있도록 설계되었습니다. 특히 LLM 에이전트가 도구로 사용하기에 최적화된 **Agent DX(Developer Experience for Agents)** 7대 원칙을 준수합니다.

---

## 설치 방법

Python 3.11 이상의 환경이 필요합니다.

```bash
# PyPI에서 설치
pip install catchtable-cli

# 개발 버전 설치 (소스 코드)
git clone https://github.com/tellang/catchtable-cli.git
cd catchtable-cli
pip install -e .
```

---

## 빠른 시작

### 매장 검색 (Search)

위치, 날짜, 인원수 등 다양한 조건을 조합하여 매장을 검색합니다.

```bash
# 기본 검색 (강남 지역 스시)
ct search "스시" --location "강남" --date 2026-03-20 --party-size 2

# 필드 선택 및 JSON 출력 (에이전트용)
ct search "한우" --fields shopName,rating,reviewCount --format json
```

### 매장 상세 정보 (Shop Info)

특정 매장의 예약 가능 상태와 상세 정보를 조회합니다.

```bash
# 특정 매장 alias로 조회
ct shop info "S12345"
```

---

## Agent DX 기능 (에이전트 최적화)

본 도구는 에이전트가 파이프라인에서 오류 없이 데이터를 처리할 수 있도록 다음 기능을 제공합니다.

| 기능 | 플래그 / 명령 | 설명 |
| :--- | :--- | :--- |
| **JSON-First** | `--format json` | 기본 출력을 구조화된 JSON으로 제공 (파싱 용이성) |
| **Field Selection** | `--fields a,b` | 필요한 필드만 추출하여 토큰 소모 및 컨텍스트 오버헤드 최소화 |
| **Dry Run** | `--dry-run` | 실제 API 요청을 보내지 않고 실행 계획(URL, Headers 등)만 확인 |
| **Self-Schema** | `ct schema` | 입출력 데이터의 규격(JSON Schema)을 즉시 확인하여 유효성 검증 |
| **Raw Passthrough** | `--json-body`, `--params` | API 요청에 원본 페이로드를 직접 전달 |
| **Safety Rails** | `--dry-run`, 민감정보 마스킹 | 사고 방지를 위한 안전장치 |

---

## 에이전트 사용 패턴

에이전트는 `jq`와 같은 도구와 조합하여 복잡한 검색 및 필터링 작업을 수행할 수 있습니다.

```bash
# 평점이 4.5 이상인 식당의 이름만 추출
ct search "오마카세" --format json | jq '.[] | select(.rating >= 4.5) | .shopName'

# 검색 결과의 개수만 확인
ct search "피자" --format json | jq '. | length'

# 특정 필드만 선택하여 토큰 절약
ct search "스테이크" --fields shopId,shopName --format json

# dry-run으로 요청 미리보기
ct search "한식" --dry-run
```

---

## 환경 변수

보안 및 실행 옵션을 위해 다음 환경 변수를 지원합니다. `.env` 파일 또는 쉘 환경에 설정하세요.

| 변수명 | 설명 | 기본값 |
| :--- | :--- | :--- |
| `CT_SESSION_COOKIE` | 캐치테이블 세션 쿠키 (인증이 필요한 요청 시 사용) | `None` |
| `CT_USE_CURL_CFFI` | `True` 설정 시 curl_cffi로 Cloudflare 우회 (httpx 폴백) | `False` |
| `CT_API_BASE_URL` | API 엔드포인트 기본 주소 | `https://api.catchtable.co.kr` |
| `CT_LOG_LEVEL` | 로그 레벨 설정 (DEBUG, INFO, ERROR) | `INFO` |

---

## Exit Codes (종료 코드)

자동화 스크립트에서 실행 결과를 판단할 수 있는 표준 종료 코드를 사용합니다.

| 코드 | 의미 | 설명 |
| :---: | :--- | :--- |
| **0** | SUCCESS | 작업이 성공적으로 완료됨 |
| **1** | RUNTIME_ERROR | API 응답 오류 또는 네트워크 문제 발생 |
| **2** | VALIDATION_ERROR | 입력 인자값이 스키마에 어긋나거나 유효하지 않음 |

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

**Disclaimer**: 본 도구는 캐치테이블(CatchTable)의 공식 라이브러리가 아닙니다. 개인적인 연구 및 개발 생산성 향상을 목적으로 제작되었으며, 과도한 요청으로 인한 서비스 차단 책임은 사용자에게 있습니다.
