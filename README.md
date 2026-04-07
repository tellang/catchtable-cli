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

## 조각 사유 (Purpose & Motivation)

본 프로젝트는 캐치테이블(CatchTable)의 공식 API 또는 SDK가 부재한 환경에서, **AI 에이전트 친화적 CLI 설계(Agent DX) 연구** 및 개인 생산성 향상을 목적으로 개발되었습니다.

- 공식 API/SDK 부재로 인한 CLI 기반 자동화 수요 충족
- Agent DX(Developer Experience for Agents) 7대 원칙 검증을 위한 실험적 구현체
- 개인 학습 및 연구 목적의 비상업적 프로젝트

## 면책사항 (Disclaimer & Legal Notice)

> **이 프로젝트를 사용하기 전에 반드시 아래 내용을 숙지하십시오.**

### 비공식 도구

본 프로젝트는 **캐치테이블(CatchTable) 및 주식회사 와드컴퍼니와 어떠한 제휴, 후원, 보증, 공식적 관계도 없는 독립적인 비공식 도구**입니다. "캐치테이블", "CatchTable" 및 관련 상표는 주식회사 와드컴퍼니의 자산이며, 본 프로젝트에서의 사용은 식별 목적에 한합니다.

### 이용약관 준수 책임

본 도구의 사용은 **전적으로 사용자의 책임**입니다. 사용자는 캐치테이블 서비스 이용약관(Terms of Service)을 반드시 확인하고 준수해야 합니다. 본 도구의 사용이 서비스 이용약관에 위반될 수 있으며, 이로 인한 **계정 정지, IP 차단, 법적 조치 등 모든 결과에 대한 책임은 전적으로 사용자에게 있습니다.**

### 무보증 (AS-IS)

본 소프트웨어는 **"있는 그대로(AS-IS)" 제공**되며, 명시적이든 묵시적이든 어떠한 종류의 보증도 하지 않습니다. 여기에는 상품성, 특정 목적에의 적합성, 비침해에 대한 묵시적 보증이 포함되나 이에 한정되지 않습니다.

### 서비스 변경 및 중단

본 도구는 비공식 API 엔드포인트에 의존하므로, **캐치테이블의 API 변경, 보안 정책 강화, 서비스 구조 변경 등에 의해 언제든지 작동이 중단될 수 있습니다.** 이에 대한 지속적인 유지보수나 호환성을 보장하지 않습니다.

### 과도한 사용 금지

과도한 요청(rate limit 초과, 대량 크롤링, 자동화된 반복 요청 등)은 서비스 장애를 유발할 수 있습니다. **이로 인한 서비스 차단, 법적 책임, 제3자 피해에 대한 모든 책임은 사용자에게 있습니다.** 합리적인 사용 범위 내에서만 사용하십시오.

### 데이터 및 개인정보

본 도구를 통해 수집되는 데이터의 저장, 처리, 공유에 대한 책임은 전적으로 사용자에게 있습니다. 개인정보보호법 등 관련 법규를 준수해야 하며, 수집 데이터의 상업적 이용은 관련 법률 및 서비스 이용약관에 따라 제한될 수 있습니다.

### 손해배상 면책

본 프로젝트의 개발자는 본 도구의 사용 또는 사용 불가능으로 인해 발생하는 **직접적, 간접적, 부수적, 특별, 결과적 또는 징벌적 손해**에 대해 어떠한 경우에도 책임지지 않습니다. 이는 데이터 손실, 이익 손실, 사업 중단, 계정 정지, 서비스 차단 등을 포함하나 이에 한정되지 않습니다.

### 용도 제한

본 도구는 **개인적인 연구, 학습, 생산성 향상 목적**으로만 제작되었습니다. 상업적 목적의 대량 데이터 수집, 서비스 방해, 경쟁 서비스 구축, 또는 캐치테이블의 비즈니스에 손해를 끼치는 용도로 사용하는 것을 금합니다.
