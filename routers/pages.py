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


@router.get("/teams", name="teams")
async def teams(
    request: Request,
    args: TableArgs = Depends(table_args),
    team: str | None = None,
    report: str = "summary",
        service: StatsService = Depends(get_service)):

    table, seasons = await asyncio.gather(
        service.team_table(
            season=args.season, game_type=args.game_type, sort=args.sort,
            direction=args.direction, page=args.page, page_size=32,
            report=report,
        ),
        service.season_options(),
    )
    return render(request, "table.html", "teams", table=table, title="Teams",
                  endpoint="teams", teams=teams, seasons=seasons, positions=None,
                  reports=K.TEAM_REPORTS, link_players=False, link_teams=True)


@router.get("/players/{player_id}", name="player")
async def player(request: Request, player_id: int, args: TableArgs = Depends(table_args),
                 log_season: int | None = None,
                 service: StatsService = Depends(get_service)):
    detail = await service.player_detail(player_id, season=log_season,
                                         game_type=args.game_type)
    return render(request, "player.html", None, **detail)


@router.get("/search", name="search")
async def search(request: Request, q: str = "", active: str = "",
                 service: StatsService = Depends(get_service)):
    query = q.strip()
    results = await service.search(query, active_only=active == "1")
    if len(results) == 1 and query:
        return RedirectResponse(
            str(request.url_for("player", player_id=results[0]["player_id"])),
            status_code=302,
        )
    return render(request, "search.html", None, query=query, results=results)


@router.get("/movers", name="movers")
async def movers(
    request: Request,
    args: TableArgs = Depends(table_args),
    kind: str = "skater",
    stat: str | None = None,
    since: str | None = None,
    settings: Settings = Depends(get_settings),
    store: SnapshotStore = Depends(get_store),
):
    if not settings.snapshots_enabled:
        return render(request, "movers.html", "movers", enabled=False, kind="skater",
                      stat="p", board={"rows": []}, stats=[], dates=[])

    kind = kind if kind in MOVER_STATS else "skater"
    stats = MOVER_STATS[kind]
    stat = stat if stat in dict(stats) else stats[0][0]

    board = await run_in_threadpool(store.movers, kind, args.season, args.game_type,
                                    stat, 50, since)
    dates = await run_in_threadpool(store.capture_dates, kind, args.season, args.game_type)
    return render(request, "movers.html", "movers", enabled=True, board=board, kind=kind,
                  stat=stat, stats=stats, stat_label=dict(
                      stats)[stat], dates=dates,
                  season=args.season, game_type=args.game_type)
