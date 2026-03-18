"""입력 검증 유틸리티 모듈 (Agent DX 원칙 4: Input Hardening)."""
from __future__ import annotations

import unicodedata


# 거부할 위험 유니코드 코드포인트 집합
_DANGEROUS_UNICODE = frozenset(
    [
        "\u200b",  # Zero Width Space
        "\u200c",  # Zero Width Non-Joiner
        "\u200d",  # Zero Width Joiner
        "\u200e",  # Left-to-Right Mark
        "\u200f",  # Right-to-Left Mark
        "\u202a",  # Left-to-Right Embedding
        "\u202b",  # Right-to-Left Embedding
        "\u202c",  # Pop Directional Formatting
        "\u202d",  # Left-to-Right Override
        "\u202e",  # Right-to-Left Override (특히 위험)
        "\u2060",  # Word Joiner
        "\u2061",  # Function Application
        "\u2062",  # Invisible Times
        "\u2063",  # Invisible Separator
        "\u2064",  # Invisible Plus
        "\ufeff",  # BOM / Zero Width No-Break Space
    ]
)

# 경로순회에 사용되는 문자 집합
_PATH_TRAVERSAL_CHARS = frozenset([".", "/", "\\", ":", "*", "?", '"', "<", ">", "|"])


def sanitize_text(value: str, *, field_name: str = "입력값") -> str:
    """텍스트 입력을 검증하고 NFC 정규화하여 반환.

    다음 항목을 거부합니다:
    - ASCII 제어문자 (0x00-0x1F, 0x7F)
    - 위험 유니코드 문자
    - 이중 인코딩 패턴 (% 포함)

    Returns:
        NFC 정규화된 문자열

    Raises:
        ValueError: 유효하지 않은 입력
    """
    # 제어문자 거부 (ASCII 0x00-0x1F, 0x7F)
    for ch in value:
        code = ord(ch)
        if (0x00 <= code <= 0x1F) or code == 0x7F:
            raise ValueError(
                f"{field_name}에 제어문자(U+{code:04X})가 포함되어 있습니다."
            )

    # 위험 유니코드 거부
    for ch in value:
        if ch in _DANGEROUS_UNICODE:
            raise ValueError(
                f"{field_name}에 위험한 유니코드 문자(U+{ord(ch):04X})가 포함되어 있습니다."
            )

    # 이중 인코딩 방지 (% 포함 거부)
    if "%" in value:
        raise ValueError(
            f"{field_name}에 퍼센트 인코딩 문자(%)가 포함되어 있습니다. 디코딩된 값을 사용하세요."
        )

    # NFC 정규화
    return unicodedata.normalize("NFC", value)


def sanitize_identifier(value: str, *, field_name: str = "식별자") -> str:
    """alias, shop_id 등 식별자 검증.

    sanitize_text 검증에 더해 경로순회 문자를 거부합니다.

    Returns:
        NFC 정규화된 식별자 문자열

    Raises:
        ValueError: 유효하지 않은 입력
    """
    # 기본 텍스트 검증
    value = sanitize_text(value, field_name=field_name)

    # 경로순회 문자 거부
    for ch in value:
        if ch in _PATH_TRAVERSAL_CHARS:
            raise ValueError(
                f"{field_name}에 경로순회 문자('{ch}')가 포함되어 있습니다."
            )

    return value
