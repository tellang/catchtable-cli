"""런타임 스키마 자체검사 모듈 (Agent DX 원칙 3: Runtime Schema Introspection)."""
from __future__ import annotations

from typing import Any

from catchtable_cli.models import (
    AutocompleteData,
    AutocompleteSuggestion,
    DaySlot,
    DaySlotsData,
    SearchListData,
    SearchShop,
    ShopDetail,
    ValidUrlData,
)

# 커맨드별 스키마 메타데이터 정의
_COMMAND_SCHEMAS: dict[str, dict[str, Any]] = {
    "search search": {
        "description": "자동완성 API로 검색 키워드 제안을 조회합니다.",
        "parameters": {
            "keyword": {"type": "string", "required": True, "description": "자동완성 키워드"},
            "--limit": {"type": "integer", "default": 20, "min": 1, "max": 100, "description": "최대 표시 건수"},
            "--format": {"type": "string", "default": "json", "enum": ["json", "table", "compact"], "description": "출력 형식"},
            "--fields": {"type": "string", "default": None, "description": "응답 필드 선택 (쉼표 구분)"},
            "--json-body": {"type": "string", "default": None, "description": "요청 본문 JSON 직접 전달"},
            "--params": {"type": "string", "default": None, "description": "API 쿼리 파라미터 오버라이드 (key=value 쉼표 구분)"},
            "--dry-run": {"type": "boolean", "default": False, "description": "API 미호출, 요청 계획만 출력"},
        },
        "response_model": AutocompleteData.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 요청 실패",
            "2": "인증 오류",
        },
    },
    "search region": {
        "description": "지역 기반 매장 검색을 수행합니다.",
        "parameters": {
            "--region": {"type": "string", "required": True, "description": "지역명 (예: 판교, 강남)"},
            "--category": {"type": "string", "default": None, "description": "카테고리"},
            "--visit-date": {"type": "string", "default": None, "description": "방문일 (YYYY-MM-DD)"},
            "--person-count": {"type": "integer", "default": 2, "description": "인원수"},
            "--sort": {"type": "string", "default": "RATING", "enum": ["RATING", "REVIEW", "DISTANCE"], "description": "정렬"},
            "--food-kind": {"type": "string", "default": None, "description": "음식 종류 코드"},
            "--page": {"type": "integer", "default": 1, "min": 1, "description": "페이지 번호"},
            "--page-size": {"type": "integer", "default": 15, "min": 1, "max": 100, "description": "페이지당 결과 수"},
            "--format": {"type": "string", "default": "json", "enum": ["json", "table", "compact"], "description": "출력 형식"},
            "--fields": {"type": "string", "default": None, "description": "응답 필드 선택 (쉼표 구분)"},
            "--json-body": {"type": "string", "default": None, "description": "요청 본문 JSON 직접 전달"},
            "--params": {"type": "string", "default": None, "description": "API 쿼리 파라미터 오버라이드 (key=value 쉼표 구분)"},
            "--dry-run": {"type": "boolean", "default": False, "description": "API 미호출, 요청 계획만 출력"},
        },
        "response_model": SearchListData.model_json_schema(),
        "shop_model": SearchShop.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 요청 실패",
            "2": "인증 오류",
        },
    },
    "shop info": {
        "description": "alias를 shopRef로 변환한 뒤 매장 상세/예약 가능 날짜를 조회합니다.",
        "parameters": {
            "alias": {"type": "string", "required": True, "description": "매장 alias (예: bornandbredoriginal)"},
            "--format": {"type": "string", "default": "json", "enum": ["json", "table", "compact"], "description": "출력 형식"},
            "--fields": {"type": "string", "default": None, "description": "응답 필드 선택 (쉼표 구분)"},
            "--json-body": {"type": "string", "default": None, "description": "요청 본문 JSON 직접 전달"},
            "--params": {"type": "string", "default": None, "description": "API 쿼리 파라미터 오버라이드 (key=value 쉼표 구분)"},
            "--dry-run": {"type": "boolean", "default": False, "description": "API 미호출, 요청 계획만 출력"},
        },
        "response_model": ShopDetail.model_json_schema(),
        "day_slot_model": DaySlot.model_json_schema(),
        "exit_codes": {
            "0": "성공",
            "1": "API 오류 또는 요청 실패",
            "2": "인증 오류",
        },
    },
}


def get_command_schema(command: str) -> dict[str, Any] | None:
    """커맨드 이름으로 스키마를 조회합니다.

    Args:
        command: 커맨드 경로 (예: "search region", "shop info")

    Returns:
        스키마 딕셔너리 또는 None
    """
    return _COMMAND_SCHEMAS.get(command)


def list_commands() -> list[str]:
    """사용 가능한 커맨드 목록을 반환합니다."""
    return sorted(_COMMAND_SCHEMAS.keys())
