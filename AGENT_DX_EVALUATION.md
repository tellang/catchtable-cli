# Agent DX 8대 원칙 평가 — catchtable-cli

> 평가 기준: 80점 만점 (각 원칙 10점), 평가일: 2026-04-11

## 총점: 64/80 (80%)

| # | 원칙 | 점수 | 등급 |
|---|------|:----:|:----:|
| 1 | JSON-First Output | 9/10 | A |
| 2 | Raw Payload Passthrough | 8/10 | B+ |
| 3 | Schema Introspection | 8/10 | B+ |
| 4 | Input Hardening | 8/10 | B+ |
| 5 | Context Window Discipline | 7/10 | B |
| 6 | Safety Rails | 8/10 | B+ |
| 7 | Skill Files | 7/10 | B |
| 8 | Smart Search | 7/10 | B |

---

## 1. JSON-First Output — 9/10

**근거:**
- `--format json` 기본값, 모든 커맨드에서 `json.dumps(indent=2, ensure_ascii=False)` 출력
- stdout/stderr 완전 분리: 데이터는 stdout, 에러/테이블은 stderr (Rich Console)
- `compact` 모드로 TSV 파이프라인 호환
- `jq` 조합 예시 README에 문서화

**감점 사유 (-1):**
- 에러 발생 시 stdout에 JSON 에러 객체를 출력하지 않음 (stderr에만 human-readable 메시지). 에이전트가 에러 원인을 파싱하려면 stderr를 읽어야 함.

---

## 2. Raw Payload Passthrough — 8/10

**근거:**
- `--json-body`: 요청 본문 전체를 JSON 문자열로 직접 전달, 내부 파라미터 빌딩 완전 우회
- `--params`: key=value 쉼표 구분으로 쿼리 파라미터 오버라이드
- `search`, `region`, `shop info` 모든 커맨드에서 일관 지원

**감점 사유 (-2):**
- `--params`가 쉼표 구분이라 value에 쉼표 포함 시 파싱 오류 가능. JSON 형식 지원 또는 반복 플래그(`--param key=value --param key2=value2`) 미지원.
- 응답 원본(raw response headers, status code)을 함께 출력하는 `--verbose` 모드 없음.

---

## 3. Schema Introspection — 8/10

**근거:**
- `ct schema list`: 등록된 커맨드 목록 JSON 출력
- `ct schema show "search region"`: 파라미터 타입/필수여부/제약조건 + Pydantic 응답 모델 JSON Schema + exit codes
- Zero-shot discovery: 에이전트가 스키마만 보고 올바른 호출 가능

**감점 사유 (-2):**
- 등록되지 않은 커맨드(`reserve`, `notify`, `version`, `overview`)의 스키마 없음.
- `ct schema show` 결과에 예제(example) 필드 없음 — few-shot 학습 불가.

---

## 4. Input Hardening — 8/10

**근거:**
- `sanitize_text()`: ASCII 제어문자, 위험 유니코드(ZWJ, BOM, 방향 포맷터), percent-encoding 차단, NFC 정규화
- `sanitize_identifier()`: 위 + 경로순회 문자(`.`, `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) 추가 차단
- 커맨드별 적절한 수준 적용: 검색어 → `sanitize_text`, alias → `sanitize_identifier`

**감점 사유 (-2):**
- `--visit-date` 포맷 검증 없음 (YYYY-MM-DD 형식 미검증, 잘못된 날짜 전달 가능)
- `--json-body`로 전달된 JSON 내부 값에 대한 검증 없음 (의도적 우회지만 문서화 미흡)

---

## 5. Context Window Discipline — 7/10

**근거:**
- `--fields`: 응답에서 필요한 필드만 선택 (토큰 절약)
- `--limit`, `--page`, `--page-size`: 페이지네이션으로 결과 크기 제한
- `--format compact`: TSV 형식으로 최소 토큰 소비

**감점 사유 (-3):**
- `shop info`에 `--limit` 없음 (day_slots 개수 제한 불가)
- 필드 필터링이 최상위 레벨만 지원, 중첩 필드 선택(`shop.address.road`) 미지원
- 응답에 `_metadata` (요청 시간, 토큰 힌트 등) 없음

---

## 6. Safety Rails — 8/10

**근거:**
- `--dry-run`: 모든 커맨드에서 API 호출 없이 요청 계획을 JSON으로 출력
- `mask_value()`, `mask_config()`: 민감 필드(cookie, token, password 등) 자동 마스킹
- Exit code 분리: 0(성공), 1(런타임), 2(검증/인증)
- `config.py`의 `SENSITIVE_FIELDS` 목록으로 일괄 관리

**감점 사유 (-2):**
- `--dry-run`이 multi-step 커맨드(`shop info`)에서 step 간 의존성을 `<placeholder>`로 표시 — 실제 URL 미리보기 불가
- rate-limit 경고/보호 메커니즘 없음

---

## 7. Skill Files — 7/10 (개선됨: 3→7)

**이전 상태 (3점):**
- SKILL.md 없음, .gitignore에서 제외 처리
- 에이전트가 프로젝트 사용법을 파악하려면 README 전체를 읽어야 함

**개선 내용:**
- `SKILL.md` 신규 생성: 커맨드 표, 글로벌 옵션, 워크플로우 패턴, 에러 핸들링 가이드
- `.gitignore`에서 `SKILL.md` 제거 → 저장소에 포함되어 에이전트 접근 가능

**잔여 감점 (-3):**
- SKILL.md에 커맨드별 예제 입출력 쌍(example request → response) 없음
- 에이전트 프레임워크별 통합 가이드(LangChain, CrewAI 등) 없음
- `.well-known/agent.json` 또는 MCP manifest 미지원

---

## 8. Smart Search — 7/10 (개선됨: 5→7)

**이전 상태 (5점):**
- 기본 자동완성만 지원, 결과 0건 시 빈 응답 반환
- 오타/유사어 제안 없음

**개선 내용:**
- `--suggest` 플래그 추가 (search, region 커맨드)
- 결과 0건 시 키워드 prefix로 자동완성 API 재시도 → 유사 키워드 최대 5개 제안
- JSON 모드: `"suggestions": [...]` 필드로 구조화 출력
- table 모드: `혹시 이 키워드를 찾으셨나요?` stderr 메시지
- 스키마에 `--suggest` 파라미터 등록

**잔여 감점 (-3):**
- 초성 검색/한영 오타 교정 미지원 (예: `ㅅㅅ` → `스시`)
- 검색어 자동 확장(synonym) 미지원
- 검색 히스토리 기반 제안 미지원

---

## 개선 이력

| 날짜 | 원칙 | Before | After | 변경 내용 |
|------|------|:------:|:-----:|-----------|
| 2026-04-11 | 7. Skill Files | 3 | 7 | SKILL.md 생성, .gitignore에서 제거 |
| 2026-04-11 | 8. Smart Search | 5 | 7 | `--suggest` 플래그, prefix 기반 유사 키워드 제안 |

## 다음 개선 후보 (우선순위)

1. **에러 JSON 출력** (원칙 1, +1): stderr 에러를 stdout JSON `{"ok":false,"error":...}`로도 출력
2. **예제 필드 추가** (원칙 3, +1): 스키마에 `examples` 배열 추가
3. **날짜 포맷 검증** (원칙 4, +1): `--visit-date` YYYY-MM-DD 형식 검증
4. **중첩 필드 선택** (원칙 5, +1): `--fields "shop.name,shop.address"` 지원
5. **초성 검색** (원칙 8, +1): 한글 초성 → 자동완성 키워드 변환
