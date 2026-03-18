"""설정 모듈. 민감정보 마스킹 유틸리티 포함 (Agent DX 원칙 6: Safety Rails)."""
from __future__ import annotations

from typing import Any

from pydantic_settings import BaseSettings


class CatchTableConfig(BaseSettings):
    model_config = {"env_prefix": "CT_"}

    api_base_url: str = "https://ct-api.catchtable.co.kr"
    session_cookie: str = ""  # x-ct-a 쿠키 값 (브라우저 로그인 후 획득)
    use_curl_cffi: bool = True


# 마스킹할 민감 필드 이름 집합 (소문자 비교)
_SENSITIVE_FIELDS = frozenset(
    [
        "session_cookie",
        "sessioncookie",
        "cookie",
        "token",
        "access_token",
        "accesstoken",
        "secret",
        "password",
        "passwd",
        "api_key",
        "apikey",
        "authorization",
    ]
)


def mask_value(value: str) -> str:
    """민감한 값을 마스킹합니다. 앞 4자리만 표시하고 나머지를 ***로 치환."""
    if not value:
        return ""
    visible = value[:4]
    return f"{visible}{'*' * min(len(value) - 4, 8)}"


def mask_config(data: dict[str, Any]) -> dict[str, Any]:
    """설정 딕셔너리에서 민감 필드를 마스킹한 복사본을 반환합니다."""
    masked: dict[str, Any] = {}
    for key, val in data.items():
        if key.lower() in _SENSITIVE_FIELDS and isinstance(val, str) and val:
            masked[key] = mask_value(val)
        else:
            masked[key] = val
    return masked
