from __future__ import annotations

from typing import Any


def text(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("default") or next(iter(value.values()), None)
    return value


def _pick(row: dict, *names, default=None):
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
        return default


def _full_name(row: dict) -> str:
    direct = _pick(row, "skaterFullName", "goalieFullName", "fullName", "name")
    if direct:
        return text(direct)
    first = text(row.get("firstName")) or ""
    last = text(row.get("lastName")) or ""
    return f"{first} {last}".strip()


def _team(row: dict) -> str:
    team = _pick(row, "teamAbbrevs", "teamAbbrev",
                 "currentTeamAbbrevs", "triCode")
    team = text(team)
    if isinstance(team, str) and "," in team:
        return team.replace(",", "/")
    return team or ""


def skater_row(row: dict, team_fallback: str | None = None) -> dict:
    return {
        "player_id": _pick(row, "playerId", "id"),
        "name": _full_name(row),
        "team": _team(row) or (team_fallback or ""),
        "position": text(_pick(row, "positionCode", "position", default="")),
        "sweater": _pick(row, "sweaterNumber"),
        "headshot": row.get("headshot"),
        "gp": _pick(row, "gamesPlayed"),
        "g": _pick(row, "goals"),
        "a": _pick(row, "assists"),
        "p": _pick(row, "points"),
        "points_per_game": _pick(row, "pointsPerGame"),
        "plus_minus": _pick(row, "plusMinus"),
        "pim": _pick(row, "penaltyMinutes", "pim"),
        "ppg": _pick(row, "ppGoals", "powerPlayGoals"),
        "ppp": _pick(row, "ppPoints", "powerPlayPoints"),
        "shg": _pick(row, "shGoals", "shorthandedGoals"),
        "gwg": _pick(row, "gameWinningGoals"),
        "otg": _pick(row, "otGoals", "overtimeGoals"),
        "shots": _pick(row, "shots"),
        "shooting_pct": _pick(row, "shootingPct", "shootingPctg"),
        "toi_per_game": _pick(row, "timeOnIcePerGame", "avgTimeOnIcePerGame"),
        "faceoff_pct": _pick(row, "faceoffWinPct", "faceoffWinPctg"),
    }


def goalie_row(row: dict, team_fallback: str | None = None) -> dict:
    return {
        "player_id": _pick(row, "playerId", "id"),
        "name": _full_name(row),
        "team": _team(row) or (team_fallback or ""),
        "position": "G",
        "sweater": _pick(row, "sweaterNumber"),
        "headshot": row.get("headshot"),
        "gp": _pick(row, "gamesPlayed"),
        "gs": _pick(row, "gamesStarted"),
        "w": _pick(row, "wins"),
        "l": _pick(row, "losses"),
        "otl": _pick(row, "otLosses", "overtimeLosses"),
        "sv_pct": _pick(row, "savePct", "savePercentage", "savePctg"),
        "gaa": _pick(row, "goalsAgainstAverage", "goalsAgainstAvg"),
        "so": _pick(row, "shutouts"),
        "saves": _pick(row, "saves"),
        "shots_against": _pick(row, "shotsAgainst"),
        "goals_against": _pick(row, "goalsAgainst"),
        "toi": _pick(row, "timeOnIce"),
    }


def team_row(row: dict) -> dict:
    return {
        "team_id": _pick(row, "teamId"),
        "name": text(_pick(row, "teamFullName", "teamName", default="")),
        "abbrev": _team(row),
        "gp": _pick(row, "gamesPlayed"),
        "w": _pick(row, "wins"),
        "l": _pick(row, "losses"),
        "otl": _pick(row, "otLosses"),
        "points": _pick(row, "points"),
        "point_pct": _pick(row, "pointPct"),
        "gf": _pick(row, "goalsFor"),
        "ga": _pick(row, "goalsAgainst"),
        "gf_pg": _pick(row, "goalsForPerGame"),
        "ga_pg": _pick(row, "goalsAgainstPerGame"),
        "pp_pct": _pick(row, "powerPlayPct"),
        "pk_pct": _pick(row, "penaltyKillPct"),
        "shots_for_pg": _pick(row, "shotsForPerGame"),
        "shots_against_pg": _pick(row, "shotsAgainstPerGame"),
        "faceoff_pct": _pick(row, "faceoffWinPct"),
    }


def standings_row(row: dict) -> dict:
    streak_code = row.get("streakCode")
    streak_count = row.get("streakCount")
    return {
        "abbrev": text(row.get("teamAbbrev")),
        "name": text(row.get("teamName")),
        "logo": row.get("teamLogo"),
        "conference": row.get("conferenceName"),
        "division": row.get("divisionName"),
        "gp": row.get("gamesPlayed"),
        "w": row.get("wins"),
        "l": row.get("losses"),
        "otl": row.get("otLosses"),
        "points": row.get("points"),
        "point_pct": row.get("pointPctg"),
        "row": row.get("regulationPlusOtWins"),
        "gf": row.get("goalFor"),
        "ga": row.get("goalAgainst"),
        "diff": row.get("goalDifferential"),
        "l10": f"{row.get('l10Wins', 0)}-{row.get('l10Losses', 0)}-{row.get('l10OtLosses', 0)}",
        "streak": f"{streak_code}{streak_count}" if streak_code else "—",
        "clinch": row.get("clinchIndicator"),
        "wildcard_sequence": row.get("wildcardSequence"),
    }


def player_profile(landing: dict) -> dict:
    draft = landing.get("draftDetails") or {}
    return {
        "player_id": landing.get("playerId"),
        "first_name": text(landing.get("firstName")),
        "last_name": text(landing.get("lastName")),
        "name": f"{text(landing.get('firstName')) or ''} {text(landing.get('lastName')) or ''}".strip(),
        "team": landing.get("currentTeamAbbrev"),
        "team_name": text(landing.get("fullTeamName")),
        "team_logo": landing.get("teamLogo"),
        "headshot": landing.get("headshot"),
        "hero_image": landing.get("heroImage"),
        "sweater": landing.get("sweaterNumber"),
        "position": landing.get("position"),
        "is_goalie": landing.get("position") == "G",
        "is_active": landing.get("isActive"),
        "height_in": landing.get("heightInInches"),
        "weight_lb": landing.get("weightInPounds"),
        "birth_date": landing.get("birthDate"),
        "birth_city": text(landing.get("birthCity")),
        "birth_state": text(landing.get("birthStateProvince")),
        "birth_country": landing.get("birthCountry"),
        "shoots": landing.get("shootsCatches"),
        "draft": (
            f"{draft.get('year')} round {draft.get('round')}, "
            f"#{draft.get('overallPick')} by {draft.get('teamAbbrev')}"
            if draft.get("year")
            else "Undrafted"
        ),
    }


def season_totals(landing: dict, is_goalie: bool, game_type: int | None = None) -> list[dict]:
    rows = []
    for entry in landing.get("seasonTotals", []) or []:
        if game_type is not None and entry.get("gameTypeId") != game_type:
            continue
        base = goalie_row(entry) if is_goalie else skater_row(entry)
        base.update(
            {
                "season": entry.get("season"),
                "league": entry.get("leagueAbbrev"),
                "team": text(entry.get("teamName")) or base.get("team"),
                "game_type": entry.get("gameTypeId"),
            }
        )
        if is_goalie:
            base["toi"] = entry.get("timeOnIce")
        else:
            base["toi_per_game"] = entry.get(
                "avgToi") or base.get("toi_per_game")
        rows.append(base)
    rows.sort(key=lambda r: (r.get("season") or 0), reverse=True)
    return rows


def game_log_rows(payload: dict, is_goalie: bool) -> list[dict]:
    rows = []
    for game in payload.get("gameLog", []) or []:
        common = {
            "game_id": game.get("gameId"),
            "date": game.get("gameDate"),
            "team": game.get("teamAbbrev"),
            "opponent": game.get("opponentAbbrev"),
            "home_road": game.get("homeRoadFlag"),
            "toi": game.get("toi"),
        }
        if is_goalie:
            common.update(
                {
                    "decision": game.get("decision"),
                    "shots_against": game.get("shotsAgainst"),
                    "saves": game.get("saves"),
                    "goals_against": game.get("goalsAgainst"),
                    "sv_pct": game.get("savePctg"),
                    "started": game.get("gamesStarted"),
                }
            )
        else:
            common.update(
                {
                    "g": game.get("goals"),
                    "a": game.get("assists"),
                    "p": game.get("points"),
                    "plus_minus": game.get("plusMinus"),
                    "pim": game.get("pim"),
                    "shots": game.get("shots"),
                    "ppg": game.get("powerPlayGoals"),
                    "shg": game.get("shorthandedGoals"),
                }
            )
        rows.append(common)
    return rows


def search_results(payload: Any) -> list[dict]:
    items = payload if isinstance(
        payload, list) else payload.get("results", [])
    out = []

    for item in items:
        out.append(
            {
                "player_id": item.get("playerId"),
                "name": item.get("name"),
                "position": item.get("positionCode"),
                "team": item.get("teamAbbrev"),
                "sweater": item.get("sweaterNumber"),
                "active": item.get("active"),
                "height": item.get("height"),
                "weight": item.get("weight"),
                "birth_city": item.get("birthCity"),
                "birth_country": item.get("birthCountry"),
                "last_season": item.get("lastSeasonId"),
            }
        )
    return out
