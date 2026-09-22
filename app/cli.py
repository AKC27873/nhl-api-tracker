from __future__ import annotations


import argparse
import asyncio
import sys

from config import Settings
from nhl import NHLAPIError, NHLCLIENT
from services import StatsService
from storage import SnapshotStore


async def _snapshot(settings: Settings, season: str | None, game_type: int) -> int:
    client = NHLCLIENT(
        web_api=settings.web_api,
        stats_api=settings.stats_api,
        search_api=settings.search_api,
        timeout=settings.http_timeout,
        retries=settings.http_retries,
        user_agent=settings.user_agent,
        default_ttl=0,  # Always capture fresh
    )
    store = SnapshotStore(settings.database)
    store.init()
    try:
        result = await StatsService(client, store).capture_snapshot(season, game_type)
    except NHLAPIError as exc:
        print(f"NHL API error: {exc.message} {exc.url}", file=sys.stderr)
        return 1
    finally:
        await client.aclose()

    for kind, count in result["counts"].items():
        print(f"{kind}: {count} rows")
    print(f"Captured {result['season']} on {result['captured_on']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cli.py", description="NHL stat tracker tasks")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Create the snapshot table")

    snap = sub.add_parser(
        "snapshot", help="Capture today's skater, goalie and team lines")
    snap.add_argument(
        "--season", help="Season id, e.g. 20252026. Default to current.")
    snap.add_argument("--game-type", type=int, choices=(2, 3), default=2,
                      help="2 regular season, 3 playoffs")

    prune = sub.add_parser("prune", help="Delete old captures")
    prune.add_argument("--keep-days", type=int, default=400)

    args = parser.parse_args(argv)
    settings = Settings.from_env()

    if args.command == "init-db":
        SnapshotStore(settings.database).init()
        print(f"Ready: {settings.database}")
        return 0
    if args.command == "snapshot":
        return asyncio.run(_snapshot(settings, args.season, args.game_type))
    if args.command == "prune":
        store = SnapshotStore(settings.database)
        print(f"Deleted {store.prune(args.keep_days)} rows")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
