# catchtable-cli (ct) — Agent Skill File

> AI 에이전트가 이 CLI를 즉시 활용할 수 있도록 설계된 가이드입니다.

## Identity

- **Name**: `ct` (catchtable-cli)
- **Purpose**: 캐치테이블 레스토랑 예약 플랫폼 비공식 CLI
- **Version**: 0.1.0
- **Python**: >=3.11

## Quick Start

```bash
# 설치
pip install catchtable-cli

# 인증 (쿠키 기반)
export CT_SESSION_COOKIE="your-x-ct-a-cookie"

# Cloudflare 우회 활성화
export CT_USE_CURL_CFFI=true
```

## Commands

| Command | Description | Auth Required |
|---------|-------------|:---:|
| `ct search <keyword>` | 자동완성 키워드 검색 | No |
| `ct search region --region <name>` | 지역 기반 매장 검색 | No |
| `ct shop info <alias>` | 매장 상세 + 예약 가능일 조회 | No |
| `ct schema show "<command>"` | 커맨드 JSON 스키마 조회 | No |
| `ct schema list` | 등록된 커맨드 목록 | No |

## Global Options (모든 커맨드 공통)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format / -f` | json\|table\|compact | json | 출력 형식 |
| `--fields` | string | None | 응답 필드 선택 (쉼표 구분) |
| `--json-body` | string | None | Raw JSON 요청 본문 직접 전달 |
| `--params` | string | None | 쿼리 파라미터 오버라이드 (key=value) |
| `--dry-run` | flag | false | API 미호출, 요청 계획만 출력 |

## Output Contract

- **stdout**: 구조화된 데이터 (JSON, compact TSV) — 파이프/jq 호환
- **stderr**: 사람용 출력 (Rich 테이블, 에러 메시지)
- **Exit codes**: `0` 성공, `1` API/런타임 오류, `2` 입력검증/인증 오류

## Agent Workflow Patterns

### 1. 스키마 먼저 확인 (Zero-shot Discovery)
```bash
ct schema list                          # 사용 가능한 커맨드 목록
ct schema show "search region"          # 파라미터/응답 스키마 조회
```

### 2. Dry-run으로 요청 미리보기
```bash
ct search "스시" --dry-run              # API 호출 없이 요청 계획 확인
```

### 3. JSON + 필드 선택 (토큰 절약)
```bash
ct search region --region "강남" --fields shop_name,avg_rating --format json
ct shop info myrestaurant --fields shop_name,road_address,avg_rating
```

### 4. Raw Payload로 API 직접 제어
```bash
ct search "한우" --json-body '{"query":"한우","type":"SHOP"}'
ct search region --region "판교" --params "sortMethod=REVIEW,personCount=4"
```

### 5. 파이프라인 조합
```bash
ct search "스시" --format json | jq '.data.suggestions[].label'
ct search region --region "강남" --format compact | head -5
```

## Error Handling for Agents

```bash
# Exit code로 분기
ct search "test" --format json; echo "exit: $?"

# 에러 시 JSON은 stdout에 없음 → stderr만 출력됨
# Agent는 exit code로 성공/실패 판단해야 함
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CT_SESSION_COOKIE` | x-ct-a 인증 쿠키 | (empty) |
| `CT_USE_CURL_CFFI` | Cloudflare 우회 사용 | true |
| `CT_API_BASE_URL` | API 엔드포인트 | https://ct-api.catchtable.co.kr |

## Limitations

- `reserve`, `notify` 커맨드는 미구현 (exit 1)
- 인증 필요 API는 `CT_SESSION_COOKIE` 필수
- Rate limiting 정보 없음 — 과도한 호출 자제
