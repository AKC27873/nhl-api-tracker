from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool

from config import Settings
from deps import TableArgs, get_service, get_settings, get_store, table_args
from nhl import constants as K
from services import POSITION_FILTERS, StatsService
from storage import SnapshotStore


router = APIRouter(include_in_scheme=False,
                   default_response_class=HTMLResponse)

MOVER_STATS = {
    "skater": [("p", "Points"), ("g", "Goals"), ("a", "Assists"), ("shots", "Shots")],
    "goalie": [("w", "Wins"), ("saves", "Saves"), ("so", "Shutouts")],
    "team": [("points", "Points"), ("gf", "Goals for"), ("w", "Wins")],
}


def render(request: Request, template: str, active: str | None = None,
           status_code: int = 200, **context):
    return request.app.state.templates.TemplateResponse(
        request, template, {"active": active, **context}, status_code=status_code
    )


@router.get("/", name="index")
async def index(request: Request, args: TableArgs = Depends(table_args),
                service: StatsService = Depends(get_service)):
    leaders, standings = await asyncio.gather(
        service.leaders(season=args.season, game_type=args.game_type),
        service.standings("division"),
    )
    return render(request, "index.html", "index", leaders=leaders, standings=standings, season=args.season, game_type=args.game_type)


@router.get("/standings", name="standings")
async def standings(request: Request, group_by: str = "division", date: str | None = None,
                    service: StatsService = Depends(get_service)):
    data = await service.standings(group_by, date=date or None)
    return render(request, "standing.html", "standings", **data)


@router.get("/skaters", name="skaters")
async def skaters(
    request: Request,
    args: TableArgs = Depends(table_args),
    team: str | None = None,
    position: str = "all",
    report: str = "summary",
    service: StatsService = Depends(get_service),
    settings: Settings = Depends(get_settings),
):
    table, teams, season = await asyncio.gather(
        service.skater_table(
            seasons=args.season, game_type=args.game_type, sort=args.sort,
            direction=args.direction, page=args.page, page_size=settings.page_size,
            team=team or None, position=position, report=report,
        ),
        service.teams(),
        service.season_options(),
    )
    return render(request, "table.html", "skaters", table=table, title="Skaters",
                  endpoint="skaters", teams=teams, seasons=seasons,
                  position=list(POSITION_FILTERS), reports=K.SKATER_REPORTS,
                  link_players=True, link_teams=False)


@router.get("/goalies", name="goalies")
async def goalies(
    request: Request,
    args: TableArgs = Depends(table_args),
    team: str | None = None,
    position: str = "all",
    report: str = "summary",
    service: StatsService = Depends(get_service),
    settings: Settings = Depends(get_settings),
):
    table, teams, season = await asyncio.gather(
        service.goalie_table(
            seasons=args.season, game_type=args.game_type, sort=args.sort,
            direction=args.direction, page=args.page, page_size=settings.page_size,
            team=team or None, report=report,
        ),
        service.teams(),
        service.season_options(),
    )
    return render(request, "table.html", "goalies", table=table, title="Skaters",
                  endpoint="goalies", teams=teams, seasons=seasons,
                  positions=None, reports=K.GOALIE_REPORTS,
                  link_players=True, link_teams=False)
