"""매장 정보 커맨드.

Agent DX 원칙 적용:
- 1. JSON-First Output: --format 옵션 (json/table/compact), stderr 분리
- 2. Raw Payload Passthrough: --json-body, --params
- 4. Input Hardening: alias 입력 검증
- 5. Context Window Discipline: --fields
- 6. Safety Rails: --dry-run
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from catchtable_cli.client import CatchTableAPIError, CatchTableClient
from catchtable_cli.commands.search import OutputFormat
from catchtable_cli.models import (
    ApiEnvelope,
    DaySlot,
    DaySlotsData,
    ShopDetail,
    ValidUrlData,
)
from catchtable_cli.validate import sanitize_identifier

# stderr 전용 콘솔 (에러, 테이블 등 human-readable 출력)
err_console = Console(stderr=True)

shop_app = typer.Typer(help="매장 정보")


def _format_http_status_error(exc: httpx.HTTPStatusError) -> str:
    """HTTP 상태 오류 메시지를 사람이 읽기 좋은 형태로 변환."""
    body = (exc.response.text or "").strip()
    content_type = (exc.response.headers.get("content-type") or "").lower()
    if "text/html" in content_type or body.startswith("<!DOCTYPE html"):
        reason = exc.response.reason_phrase or "HTTP Error"
        return f"[{exc.response.status_code}] {reason}"
    body = " ".join(body.split())
    if len(body) > 300:
        body = f"{body[:300]}..."
    return f"[{exc.response.status_code}] {body or '요청이 실패했습니다.'}"


def _extract_shop_payload(data: Any) -> dict[str, Any]:
    """응답 데이터에서 매장 상세 딕셔너리를 추출합니다."""
    if isinstance(data, dict):
        nested = data.get("shop")
        if isinstance(nested, dict):
            return nested
        return data
    return {}


def _extract_day_slot_payload(data: Any) -> list[dict[str, Any]]:
    """응답 데이터에서 예약 슬롯 목록을 추출합니다."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("daySlots", "slots", "dates", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _format_yymmdd(value: str | None) -> str:
    """YYYYMMDD 형식의 날짜를 YYYY-MM-DD 형식으로 변환합니다."""
    if value and len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value or "-"


def _filter_fields(data: Any, fields: list[str]) -> Any:
    """응답 데이터에서 지정된 필드만 추출합니다."""
    if not fields:
        return data
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k in fields}
    if isinstance(data, list):
        return [_filter_fields(item, fields) for item in data]
    return data


def _parse_params(params_str: str) -> dict[str, str]:
    """'key=value,key2=value2' 형식의 파라미터 문자열을 딕셔너리로 변환."""
    result: dict[str, str] = {}
    for pair in params_str.split(","):
        pair = pair.strip()
        if "=" in pair:
            k, _, v = pair.partition("=")
            result[k.strip()] = v.strip()
    return result


def _exit_with_error(message: str, code: int = 1) -> None:
    """에러 메시지를 stderr로 출력하고 종료."""
    err_console.print(f"[red]{message}[/red]")
    raise typer.Exit(code=code)


@shop_app.command()
def info(
    alias: str = typer.Argument(help="매장 alias (예: bornandbredoriginal)"),
    fmt: OutputFormat = typer.Option(OutputFormat.json, "--format", "-f", help="출력 형식 (json/table/compact)"),
    fields: str | None = typer.Option(None, "--fields", help="응답 필드 선택 (쉼표 구분, 예: shop_name,avg_rating)"),
    json_body: str | None = typer.Option(None, "--json-body", help="요청 본문 JSON 직접 전달"),
    params_override: str | None = typer.Option(None, "--params", help="API 쿼리 파라미터 오버라이드 (key=value 쉼표 구분)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="API 미호출, 요청 계획만 출력"),
) -> None:
    """alias를 shopRef로 변환한 뒤 매장 상세/예약 가능 날짜를 조회합니다."""
    # 입력 검증 (원칙 4): alias는 식별자이므로 경로순회 문자도 거부
    try:
        alias = sanitize_identifier(alias, field_name="alias")
    except ValueError as exc:
        _exit_with_error(f"입력값 오류: {exc}")

    # 쿼리 파라미터 오버라이드
    extra_params: dict[str, str] = {}
    if params_override:
        extra_params = _parse_params(params_override)

    # dry-run 모드 (원칙 6)
    if dry_run:
        plan = {
            "command": "shop info",
            "steps": [
                {
                    "step": 1,
                    "method": "GET",
                    "url": f"/api/v4/shops/{alias}",
                    "params": extra_params or None,
                    "note": "매장 상세 조회 (alias가 shopRef로 자동 처리됨)",
                },
                {
                    "step": 2,
                    "method": "GET",
                    "url": "/api/reservation/v1/dining/day-slots",
                    "params": {"shopRef": "<step1에서 획득한 shopRef>", **extra_params},
                    "note": "예약 가능 날짜 조회",
                },
            ],
        }
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    client = CatchTableClient()

    async def _run() -> dict[str, Any]:
        try:
            # alias로 직접 v4/shops 호출 — shopDetailVO 안에 전체 데이터
            shop_raw = await client.get_shop(alias)
            shop_data = shop_raw.get("data", {})
            vo = shop_data.get("shopDetailVO", shop_data) if isinstance(shop_data, dict) else {}
            shop_ref = vo.get("shopRef", alias)

            day_slots: dict[str, Any] = {}
            if shop_ref:
                try:
                    day_slots = await client.get_day_slots(shop_ref)
                except Exception:
                    pass  # 예약 비활성 매장은 day-slots 실패 가능

            return {
                "alias": alias,
                "shop_ref": shop_ref,
                "shop": shop_raw,
                "day_slots": day_slots,
            }
        finally:
            await client.close()

    try:
        payload = asyncio.run(_run())
    except CatchTableAPIError as exc:
        code = exc.result_code if exc.result_code is not None else "API"
        exit_code = 2 if str(code) in {"401", "UNAUTHORIZED", "AUTH"} else 1
        _exit_with_error(f"API 오류: [{code}] {exc}", exit_code)
        return
    except httpx.HTTPStatusError as exc:
        exit_code = 2 if exc.response.status_code == 401 else 1
        _exit_with_error(f"API 오류: {_format_http_status_error(exc)}", exit_code)
        return
    except httpx.RequestError as exc:
        _exit_with_error(f"요청 실패: {exc}")
        return

    # 필드 필터링 (원칙 5)
    field_list = [f.strip() for f in fields.split(",")] if fields else []

    if fmt == OutputFormat.json:
        # stdout에 JSON 출력 (파이프 호환)
        if field_list:
            shop_data = payload["shop"].get("data", {})
            vo = shop_data.get("shopDetailVO", shop_data) if isinstance(shop_data, dict) else {}
            shop = ShopDetail.model_validate(vo)
            shop_dict = shop.model_dump(exclude_none=True)
            filtered = _filter_fields(shop_dict, field_list)
            output = {"ok": True, "alias": alias, "shop": filtered}
        else:
            output = payload
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    shop_data = payload["shop"].get("data", {})
    vo = shop_data.get("shopDetailVO", shop_data) if isinstance(shop_data, dict) else {}
    shop = ShopDetail.model_validate(vo)

    day_slots_env = ApiEnvelope[Any].model_validate(payload["day_slots"])
    day_slots_raw = day_slots_env.data
    if isinstance(day_slots_raw, dict):
        day_slots = DaySlotsData.model_validate(day_slots_raw).day_slots
    else:
        day_slots = [DaySlot.model_validate(item) for item in _extract_day_slot_payload(day_slots_raw)]

    shop_ref = shop.shop_ref or payload.get("shop_ref") or "-"
    category = shop.food_kind_name or shop.shop_type_name or "-"
    address = shop.road_address or shop.lot_address or "-"
    rating = f"{shop.avg_rating:.1f}" if shop.avg_rating is not None else "-"
    review_count = str(shop.review_count) if shop.review_count is not None else "-"

    price_parts = []
    if shop.lunch_price:
        price_parts.append(f"점심 {shop.lunch_price}")
    if shop.dinner_price:
        price_parts.append(f"저녁 {shop.dinner_price}")
    price_text = " / ".join(price_parts) if price_parts else "-"

    if fmt == OutputFormat.compact:
        # compact: 탭 구분 한 줄 출력
        parts = [
            shop.shop_name or alias,
            category,
            address,
            rating,
            review_count,
            price_text,
        ]
        print("\t".join(parts))

        if day_slots:
            for slot in day_slots:
                slot_parts = [
                    _format_yymmdd(slot.visit_yymmdd),
                    slot.status_code or "-",
                    "Y" if slot.is_available else "N",
                    str(slot.remaining_count) if slot.remaining_count is not None else "-",
                ]
                print("\t".join(slot_parts))
        return

    # table 형식 (stderr)
    content = (
        f"[bold]{shop.shop_name or alias}[/bold]\n"
        f"Alias: {alias}\n"
        f"ShopRef: {shop_ref}\n"
        f"카테고리: {category}\n"
        f"주소: {address}\n"
        f"가격: {price_text}\n"
        f"평점: {rating} (리뷰 {review_count})\n"
        f"전화: {shop.phone_number or '-'}\n"
        f"설명: {shop.short_introduction or '-'}"
    )
    err_console.print(Panel(content, title="매장 상세"))

    if not day_slots:
        err_console.print("[yellow]예약 가능 날짜 정보가 없습니다.[/yellow]")
        return

    table = Table(title=f"예약 가능 날짜 ({len(day_slots)}건)")
    table.add_column("날짜", style="cyan")
    table.add_column("상태")
    table.add_column("예약가능", justify="center")
    table.add_column("잔여", justify="right")

    for slot in day_slots:
        if slot.is_available is True:
            available_text = "[green]Y[/green]"
        elif slot.is_available is False:
            available_text = "[red]N[/red]"
        else:
            available_text = "-"
        table.add_row(
            _format_yymmdd(slot.visit_yymmdd),
            slot.status_code or "-",
            available_text,
            str(slot.remaining_count) if slot.remaining_count is not None else "-",
        )

    err_console.print(table)
