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
from catchtable_cli.models import (
    ApiEnvelope,
    DaySlot,
    DaySlotsData,
    ShopDetail,
    ValidUrlData,
)

console = Console()

shop_app = typer.Typer(help="매장 정보")


def _format_http_status_error(exc: httpx.HTTPStatusError) -> str:
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
    if isinstance(data, dict):
        nested = data.get("shop")
        if isinstance(nested, dict):
            return nested
        return data
    return {}


def _extract_day_slot_payload(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("daySlots", "slots", "dates", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _format_yymmdd(value: str | None) -> str:
    if value and len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value or "-"


@shop_app.command()
def info(
    alias: str = typer.Argument(help="매장 alias (예: bornandbredoriginal)"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """alias를 shopRef로 변환한 뒤 매장 상세/예약 가능 날짜를 조회합니다."""
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
        console.print(f"[red]API 오류: [{code}] {exc}[/red]")
        raise typer.Exit(code=1) from exc
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]API 오류: {_format_http_status_error(exc)}[/red]")
        raise typer.Exit(code=1) from exc
    except httpx.RequestError as exc:
        console.print(f"[red]요청 실패: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
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
    console.print(Panel(content, title="매장 상세"))

    if not day_slots:
        console.print("[yellow]예약 가능 날짜 정보가 없습니다.[/yellow]")
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

    console.print(table)
