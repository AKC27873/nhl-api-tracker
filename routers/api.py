from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.concurrency import run_in_threadpool

from config import Settings
from deps import TableArgs, get_service, get_settings, get_store, table_args

from nhl import constants as K
from services import StatsService
from storage import SnapshotStore

router = APIRouter(prefix="/api/v1")

Kind = Literal["skater", "goalie", "team"]
Position = Literal["all", "forwards", "centers", "wingers", "defense"]


def _envelope(table: dict) -> dict:
    return {
        "season": table["season"],
        "game_type": table["game_type"],
        "report": table["report"],
        "sort": table["sort"],
        "direction": table["direction"],
        "page": table["page"],
        "pages": table["pages"],
        "total": table["total"],
        "rows": table["rows"],
    }


@router.get("/health", name="api_health", tags=["meta"])
async def health(request: Request, service: StatsService = Depends(get_service)):
    return {"status": "ok", "cache": service.client.cache.stats(),
            "season": await service.current_season()}


@router.get("/seasons", name="api_seasons", tags=["meta"])
async def seasons(service: StatsService = Depends(get_service)):
    return {"data": await service.season_options(limit=200)}


@router.get("/glossary", name="api_glossary", tags=["meta"])
async def glossary():
    return {
        "skater_columns": [asdict(c) for c in K.SKATER_COLUMNS],
        "goalies_columns": [asdict(c) for c in K.GOALIE_COLUMNS],
        "team_columns": [asdict(c) for c in K.TEAM_COLUMNS],
        "skater_reports": K.SKATER_REPORTS,
        "goalies_reports": K.GOALIE_REPORTS,
        "team_reports": K.TEAM_REPORTS,
    }


@router.get("/teams", name="api_teams", tags=["teams"])
async def teams(service: StatsService = Depends(get_service)):
    return {"data": await service.teams()}


@router.get("/standings", name="api_standings", tags=["teams"])
async def standings(
    group_by: Literal["division", "conference", "league"] = "division",
    date: str | None = Query(None, description="YYYY-MM-DD. Omitting today"),
    service: StatsService = Depends(get_service),
):
    data = await service.standings(group_by, data=date)
    data.pop("columns", None)
    return data


@router.get("/skaters", name="api_skaters", tags=["players"])
async def skaters(
    args: TableArgs = Depends(table_args),
    team: str | None = Query(None, description="Three-letter code, e.g. TOR"),
    position: Position = "all",
    report: str = Query(
        "summary", description="See /api/v1/glossary for the list"),
    limit: int = Query(50, ge=1, le=500),
    service: StatsService = Depends(get_service),
):
    return _envelope(await service.skater_table(
        season=args.season, game_type=args.game_type, sort=args.sort,
        direction=args.direction, page=args.page, page_size=limit,
        team=team or None, position=position, report=report,
    ))


@router.get("/goalies", name="api_goalies", tags=["players"])
async def goalies(
    args: TableArgs = Depends(table_args),
    team: str | None = None,
    report: str = "summary",
    limit: int = Query(50, ge=1, le=500),
    service: StatsService = Depends(get_service),
):
    return _envelope(await service.goalie_table(
        season=args.season, game_type=args.game_type, sort=args.sort,
        direction=args.direction, page=args.page, page_size=limit,
        team=team or None, report=report,
    ))
