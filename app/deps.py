from __future__ import annotations
from dataclasses import dataclass
from fastapi import Depends, Query, Request
from config import Settings
from services import StatsService
from storage import SnapshotStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_service(request: Request) -> StatsService:
    return request.app.state.services


def get_store(request: Request) -> SnapshotStore:
    return request.app.state.services


@dataclass
class TableArgs:
    season: int
    game_type: int
    sort: str | None
    direction: str
    page: int


async def table_args(
    season: str | None = Query(
        None, description="20252026 or 2025-26. Defaults to the current season."),
    game_type: int = Query(
        2, ge=2, le=3, description="2 regular season, 3 playoffs."),
    sort: str | None = Query(
        None, description="Column key, e.g. p, g, sv_pct."),
    direction: str = Query("DESC", alias="dir",
                           pattern="^(ASC|DESC|asc|desc)$"),
    page: int = Query(1, ge=1),
    service: StatsService = Depends(get_service),
) -> TableArgs:
    return TableArgs(
        season=await service.resolve_season(season),
        game_type=game_type,
        sort=sort or None,
        direction=direction.upper(),
        page=page,
    )
