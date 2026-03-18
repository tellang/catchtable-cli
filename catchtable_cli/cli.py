from __future__ import annotations

import typer

from catchtable_cli import __version__
from catchtable_cli.commands.search import search_app
from catchtable_cli.commands.shop import shop_app

app = typer.Typer(
    name="ct",
    help="캐치테이블 비공식 CLI",
    no_args_is_help=True,
)

app.add_typer(search_app, name="search")
app.add_typer(shop_app, name="shop")


@app.command()
def reserve() -> None:
    """예약을 생성합니다. (미구현)"""
    typer.echo("reserve 커맨드는 아직 구현되지 않았습니다.")
    raise typer.Exit(1)


@app.command()
def notify() -> None:
    """빈자리 알림을 설정합니다. (미구현)"""
    typer.echo("notify 커맨드는 아직 구현되지 않았습니다.")
    raise typer.Exit(1)


@app.command()
def version() -> None:
    """버전을 출력합니다."""
    typer.echo(f"catchtable-cli v{__version__}")


@app.command()
def overview() -> None:
    """CLI 개요를 출력합니다."""
    typer.echo(
        f"catchtable-cli v{__version__}\n"
        "캐치테이블 비공식 CLI\n\n"
        "사용 가능한 명령어:\n"
        "  search   매장 검색\n"
        "  shop     매장 정보 조회\n"
        "  reserve  예약 생성\n"
        "  notify   빈자리 알림\n"
        "  version  버전 출력"
    )
