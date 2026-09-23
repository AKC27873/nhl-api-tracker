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
