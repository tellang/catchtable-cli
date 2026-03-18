"""매장 검색 커맨드.

Agent DX 원칙 적용:
- 1. JSON-First Output: --format 옵션 (json/table/compact), stderr 분리
- 2. Raw Payload Passthrough: --json-body, --params
- 4. Input Hardening: 입력값 검증
- 5. Context Window Discipline: --fields, --page, --page-size
- 6. Safety Rails: --dry-run
"""
from __future__ import annotations

import asyncio
import json
import sys
from enum import Enum
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.table import Table

from catchtable_cli.client import CatchTableAPIError, CatchTableClient
from catchtable_cli.models import ApiEnvelope, AutocompleteData, SearchListData, SearchShop
from catchtable_cli.validate import sanitize_text

# stderr 전용 콘솔 (에러, 테이블 등 human-readable 출력)
err_console = Console(stderr=True)

search_app = typer.Typer(help="매장 검색")


class OutputFormat(str, Enum):
    """출력 형식."""
    json = "json"
    table = "table"
    compact = "compact"


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


@search_app.command()
def search(
    keyword: str = typer.Argument(..., help="자동완성 키워드"),
    limit: int = typer.Option(20, "--limit", "-n", min=1, max=100, help="최대 표시 건수"),
    fmt: OutputFormat = typer.Option(OutputFormat.json, "--format", "-f", help="출력 형식 (json/table/compact)"),
    fields: str | None = typer.Option(None, "--fields", help="응답 필드 선택 (쉼표 구분, 예: label,item_type)"),
    json_body: str | None = typer.Option(None, "--json-body", help="요청 본문 JSON 직접 전달 (기존 파라미터 덮어씀)"),
    params_override: str | None = typer.Option(None, "--params", help="API 쿼리 파라미터 오버라이드 (key=value 쉼표 구분)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="API 미호출, 요청 계획만 출력"),
) -> None:
    """자동완성 API로 검색 키워드 제안을 조회합니다."""
    # 입력 검증 (원칙 4)
    try:
        keyword = sanitize_text(keyword, field_name="keyword")
    except ValueError as exc:
        _exit_with_error(f"입력값 오류: {exc}")

    # 요청 본문 결정
    if json_body is not None:
        try:
            body = json.loads(json_body)
        except json.JSONDecodeError as exc:
            _exit_with_error(f"--json-body 파싱 오류: {exc}")
    else:
        body = {"query": keyword}

    # 쿼리 파라미터 오버라이드
    extra_params: dict[str, str] = {}
    if params_override:
        extra_params = _parse_params(params_override)

    # dry-run 모드 (원칙 6)
    if dry_run:
        plan = {
            "command": "search search",
            "method": "POST",
            "url": "/api/v5/autocomplete/_list",
            "body": body,
            "params": extra_params or None,
            "limit": limit,
        }
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    client = CatchTableClient()

    async def _run() -> dict:
        try:
            return await client.autocomplete(query=keyword if json_body is None else body.get("query", keyword))
        finally:
            await client.close()

    try:
        payload = asyncio.run(_run())
    except CatchTableAPIError as exc:
        code = exc.result_code if exc.result_code is not None else "API"
        # 인증 오류 코드 감지 (401, AUTH 계열)
        exit_code = 2 if str(code) in {"401", "UNAUTHORIZED", "AUTH"} else 1
        _exit_with_error(f"API 오류: [{code}] {exc}", exit_code)
        return  # 타입체커용 unreachable
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
        output = payload
        if field_list:
            data_part = (output.get("data") or {})
            suggestions = data_part.get("suggestions") or data_part.get("items") or data_part.get("list") or []
            filtered = [_filter_fields(s, field_list) for s in suggestions[:limit]]
            output = {"ok": True, "items": filtered, "total": len(filtered)}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    envelope = ApiEnvelope[AutocompleteData].model_validate(payload)
    suggestions = (envelope.data or AutocompleteData()).suggestions[:limit]

    if not suggestions:
        err_console.print("[yellow]자동완성 결과가 없습니다.[/yellow]")
        return

    if fmt == OutputFormat.compact:
        # compact: 한 줄씩 출력
        for item in suggestions:
            parts = [item.item_type or "-", item.label or "-"]
            if item.matching_count is not None:
                parts.append(str(item.matching_count))
            print("\t".join(parts))
        return

    # table 형식 (stderr)
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

    err_console.print(table)


@search_app.command()
def region(
    region_name: str = typer.Option(..., "--region", "-r", help="지역명 (예: 판교, 강남)"),
    category: str | None = typer.Option(None, "--category", "-c", help="카테고리"),
    visit_date: str | None = typer.Option(None, "--visit-date", "-d", help="방문일 (YYYY-MM-DD)"),
    person_count: int = typer.Option(2, "--person-count", "-p", help="인원수"),
    sort: str = typer.Option("RATING", "--sort", "-s", help="정렬 (RATING, REVIEW, DISTANCE)"),
    food_kind: str | None = typer.Option(None, "--food-kind", help="음식 종류 코드"),
    page: int = typer.Option(1, "--page", min=1, help="페이지"),
    page_size: int = typer.Option(15, "--page-size", min=1, max=100, help="페이지당 결과 수"),
    fmt: OutputFormat = typer.Option(OutputFormat.json, "--format", "-f", help="출력 형식 (json/table/compact)"),
    fields: str | None = typer.Option(None, "--fields", help="응답 필드 선택 (쉼표 구분, 예: shop_name,avg_rating)"),
    json_body: str | None = typer.Option(None, "--json-body", help="요청 본문 JSON 직접 전달 (기존 파라미터 덮어씀)"),
    params_override: str | None = typer.Option(None, "--params", help="API 쿼리 파라미터 오버라이드 (key=value 쉼표 구분)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="API 미호출, 요청 계획만 출력"),
) -> None:
    """지역 기반 매장 검색을 수행합니다."""
    # 입력 검증 (원칙 4)
    try:
        region_name = sanitize_text(region_name, field_name="region")
        if category:
            category = sanitize_text(category, field_name="category")
        if food_kind:
            food_kind = sanitize_text(food_kind, field_name="food_kind")
    except ValueError as exc:
        _exit_with_error(f"입력값 오류: {exc}")

    # 정렬 값 검증
    valid_sorts = {"RATING", "REVIEW", "DISTANCE"}
    if sort not in valid_sorts:
        _exit_with_error(f"잘못된 정렬 값: {sort}. 허용값: {', '.join(sorted(valid_sorts))}")

    # 요청 본문 결정
    if json_body is not None:
        try:
            body = json.loads(json_body)
        except json.JSONDecodeError as exc:
            _exit_with_error(f"--json-body 파싱 오류: {exc}")
    else:
        offset = (page - 1) * page_size
        body: dict[str, Any] = {"paging": {"page": page, "size": page_size, "offset": offset}}
        body["region"] = region_name
        if category:
            body["category"] = category
        if visit_date:
            body["visitDate"] = visit_date
        body["personCount"] = person_count
        if food_kind:
            body["foodKindCode"] = food_kind
        body["sortMethod"] = sort

    # 쿼리 파라미터 오버라이드
    extra_params: dict[str, str] = {}
    if params_override:
        extra_params = _parse_params(params_override)

    # dry-run 모드 (원칙 6)
    if dry_run:
        plan = {
            "command": "search region",
            "method": "POST",
            "url": "/api/v6/search/list",
            "body": body,
            "params": extra_params or None,
        }
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    client = CatchTableClient()

    async def _run() -> dict:
        try:
            if json_body is not None:
                # --json-body 사용 시 클라이언트 내부 메서드 우회, 직접 요청
                return await client._request("POST", "/api/v6/search/list", json_body=body)
            return await client.search(
                location=region_name,
                category=category,
                date=visit_date,
                party_size=person_count,
                sort_method=sort,
                food_kind_code=food_kind,
                page=page,
                size=page_size,
            )
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
            data = payload.get("data", {}) or {}
            raw_shops = (data.get("shopResults", {}) or {}).get("shops", [])
            shops = [SearchShop.from_shop_result(s).model_dump(exclude_none=True) for s in raw_shops]
            filtered_shops = [_filter_fields(s, field_list) for s in shops]
            search_data = SearchListData.model_validate(data)
            output = {
                "ok": True,
                "total": search_data.total_shop_count,
                "page": page,
                "page_size": page_size,
                "items": filtered_shops,
            }
        else:
            output = payload
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    data = payload.get("data", {}) or {}
    search_data = SearchListData.model_validate(data)
    raw_shops = (data.get("shopResults", {}) or {}).get("shops", [])
    shops = [SearchShop.from_shop_result(s) for s in raw_shops]

    if not shops:
        err_console.print("[yellow]검색 결과가 없습니다.[/yellow]")
        return

    if fmt == OutputFormat.compact:
        # compact: 한 줄씩 탭 구분 출력
        for shop in shops:
            parts = [
                shop.shop_name or "-",
                shop.food_kind_name or "-",
                shop.land_name or "-",
                f"{shop.avg_rating:.1f}" if shop.avg_rating is not None else "-",
                str(shop.review_count) if shop.review_count is not None else "-",
            ]
            print("\t".join(parts))
        return

    # table 형식 (stderr)
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

    err_console.print(table)
