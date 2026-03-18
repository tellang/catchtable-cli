from __future__ import annotations

import asyncio
import json

import httpx
import typer
from rich.console import Console
from rich.table import Table

from catchtable_cli.client import CatchTableAPIError, CatchTableClient
from catchtable_cli.models import ApiEnvelope, AutocompleteData, SearchListData, SearchShop

console = Console()

search_app = typer.Typer(help="매장 검색")


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


@search_app.command()
def search(
    keyword: str = typer.Argument(..., help="자동완성 키워드"),
    limit: int = typer.Option(20, "--limit", "-n", min=1, max=100, help="최대 표시 건수"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """자동완성 API로 검색 키워드 제안을 조회합니다."""
    client = CatchTableClient()

    async def _run() -> dict:
        try:
            return await client.autocomplete(query=keyword)
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

    envelope = ApiEnvelope[AutocompleteData].model_validate(payload)
    suggestions = (envelope.data or AutocompleteData()).suggestions[:limit]
    if not suggestions:
        console.print("[yellow]자동완성 결과가 없습니다.[/yellow]")
        return

    table = Table(title=f"자동완성 결과 ({len(suggestions)}건)")
    table.add_column("Type", style="cyan")
    table.add_column("Label", style="bold")
    table.add_column("Matching", justify="right")

    for item in suggestions:
        table.add_row(
            item.item_type or "-",
            item.label or "-",
            str(item.matching_count) if item.matching_count is not None else "-",
        )

    console.print(table)


@search_app.command()
def region(
    region_name: str = typer.Option(..., "--region", "-r", help="지역명 (예: 판교, 강남)"),
    category: str | None = typer.Option(None, "--category", "-c", help="카테고리"),
    visit_date: str | None = typer.Option(None, "--visit-date", "-d", help="방문일 (YYYY-MM-DD)"),
    person_count: int = typer.Option(2, "--person-count", "-p", help="인원수"),
    sort: str = typer.Option("RATING", "--sort", "-s", help="정렬 (RATING, REVIEW, DISTANCE)"),
    food_kind: str | None = typer.Option(None, "--food-kind", help="음식 종류 코드"),
    page: int = typer.Option(1, "--page", min=1, help="페이지"),
    size: int = typer.Option(15, "--size", min=1, max=100, help="페이지당 결과 수"),
    as_json: bool = typer.Option(False, "--json", help="JSON 출력"),
) -> None:
    """지역 기반 매장 검색을 수행합니다."""
    client = CatchTableClient()

    async def _run() -> dict:
        try:
            return await client.search(
                location=region_name,
                category=category,
                date=visit_date,
                party_size=person_count,
                sort_method=sort,
                food_kind_code=food_kind,
                page=page,
                size=size,
            )
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

    data = payload.get("data", {}) or {}
    search_data = SearchListData.model_validate(data)
    raw_shops = (data.get("shopResults", {}) or {}).get("shops", [])
    shops = [SearchShop.from_shop_result(s) for s in raw_shops]

    if not shops:
        console.print("[yellow]검색 결과가 없습니다.[/yellow]")
        return

    total = search_data.total_shop_count
    title = f"검색 결과: {region_name}"
    if total is not None:
        title += f" ({total}건 중 {len(shops)}건)"

    table = Table(title=title)
    table.add_column("매장명", style="bold")
    table.add_column("카테고리", style="cyan")
    table.add_column("지역", style="green")
    table.add_column("평점", justify="right")
    table.add_column("리뷰수", justify="right")

    for shop in shops:
        table.add_row(
            shop.shop_name or "-",
            shop.food_kind_name or "-",
            shop.land_name or "-",
            f"{shop.avg_rating:.1f}" if shop.avg_rating is not None else "-",
            str(shop.review_count) if shop.review_count is not None else "-",
        )

    console.print(table)
