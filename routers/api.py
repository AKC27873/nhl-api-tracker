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
