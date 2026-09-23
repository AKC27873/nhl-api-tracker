from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    fmt: str = "int"
    sort: str | None = None
    title: str = ""


SKATER_COLUMNS = [
    Column("name", "Player", "text", "lastName"),
    Column("team", "Team", "text"),
    Column("position", "Pos", "text", "positionCode"),
    Column("gp", "GP", "int", "gamesPlayed", "Games played"),
    Column("g", "G", "int", "goals", "Goals"),
    Column("a", "A", "int", "assists", "Assists"),
    Column("p", "P", "int", "points", "Points"),
    Column("points_per_game", "P/GP", "float2",
           "pointsPerGame", "Points per game"),
    Column("plus_minus", "+/-", "signed", "plusMinus", "Plus-minus"),
    Column("pim", "PIM", "int", "penaltyMinutes", "Penalty minutes"),
    Column("ppg", "PPG", "int", "ppGoals", "Power-play goals"),
    Column("shg", "SHG", "int", "shGoals", "Short-handed goals"),
    Column("gwg", "GWG", "int", "gameWinningGoals", "Game-winning goals"),
    Column("shots", "S", "int", "shots", "Shots on goal"),
    Column("shooting_pct", "S%", "pct", "shootingPct", "Shooting percentage"),
    Column("toi_per_game", "TOI/GP", "toi",
           "timeOnIcePerGame", "Time on ice per game"),
    Column("faceoff_pct", "FO%", "pct",
           "faceoffWinPct", "Faceoff win percentage"),
]

GOALIE_COLUMNS = [
    Column("name", "Goalie", "text", "lastName"),
    Column("team", "Team", "text"),
    Column("gp", "GP", "int", "gamesPlayed", "Games played"),
    Column("gs", "GS", "int", "gamesStarted", "Games started"),
    Column("w", "W", "int", "wins", "Wins"),
    Column("l", "L", "int", "losses", "Losses"),
    Column("otl", "OTL", "int", "otLosses", "Overtime losses"),
    Column("sv_pct", "SV%", "float3", "savePct", "Save percentage"),
    Column("gaa", "GAA", "float2", "goalsAgainstAverage",
           "Goals against average"),
    Column("so", "SO", "int", "shutouts", "Shutouts"),
    Column("saves", "SV", "int", "saves", "Saves"),
    Column("shots_against", "SA", "int", "shotsAgainst", "Shots against"),
    Column("goals_against", "GA", "int", "goalsAgainst", "Goals against"),
    Column("toi", "TOI", "toi", "timeOnIce", "Total time on ice"),
]

TEAM_COLUMNS = [
    Column("name", "Team", "text", "teamFullName"),
    Column("gp", "GP", "int", "gamesPlayed"),
    Column("w", "W", "int", "wins"),
    Column("l", "L", "int", "losses"),
    Column("otl", "OTL", "int", "otLosses"),
    Column("points", "PTS", "int", "points"),
    Column("point_pct", "P%", "float3", "pointPct", "Points percentage"),
    Column("gf", "GF", "int", "goalsFor"),
    Column("ga", "GA", "int", "goalsAgainst"),
    Column("gf_pg", "GF/GP", "float2", "goalsForPerGame"),
    Column("ga_pg", "GA/GP", "float2", "goalsAgainstPerGame"),
    Column("pp_pct", "PP%", "pct", "powerPlayPct", "Power-play percentage"),
    Column("pk_pct", "PK%", "pct", "penaltyKillPct", "Penalty-kill percentage"),
    Column("shots_for_pg", "S/GP", "float1", "shotsForPerGame"),
    Column("shots_against_pg", "SA/GP", "float1", "shotsAgainstPerGame"),
    Column("faceoff_pct", "FO%", "pct", "faceoffWinPct"),
]

STANDINGS_COLUMNS = [
    Column("name", "Team", "text"),
    Column("gp", "GP", "int"),
    Column("w", "W", "int"),
    Column("l", "L", "int"),
    Column("otl", "OTL", "int"),
    Column("points", "PTS", "int"),
    Column("point_pct", "P%", "float3"),
    Column("row", "ROW", "int", title="Regulation plus overtime wins"),
    Column("gf", "GF", "int"),
    Column("ga", "GA", "int"),
    Column("diff", "DIFF", "signed", title="Goal differential"),
    Column("l10", "L10", "text", title="Record over the last ten games"),
    Column("streak", "STRK", "text"),
]

SKATER_SORTS = {c.key: c.sort for c in SKATER_COLUMNS if c.sort}
GOALIE_SORTS = {c.key: c.sort for c in GOALIE_COLUMNS if c.sort}
TEAM_SORTS = {c.key: c.sort for c in TEAM_COLUMNS if c.sort}

SKATER_REPORTS = ["summary", "realtime", "powerplay", "penaltyShots", "faceoffpercentages",
                  "timeonice", "shottype", "goalsForAgainst", "penalties", "bios"]
GOALIE_REPORTS = ["summary", "advanced", "daysrest", "penaltyShots", "savesByStrength",
                  "shootout", "startedVsRelieved", "bios"]
TEAM_REPORTS = ["summary", "faceoffpercentages", "goalsForAgainst", "penalties",
                "penaltykill", "powerplay", "realtime", "shottype", "summaryshooting"]
GAME_TYPES = {2: "Regular season", 3: "Playoffs"}


def season_label(season: int | str | None) -> str:
    if value is None or value == "":
        return "—"
    try:
        if fmt == "text":
            return str(value)
        if fmt == "int":
            return f"{int(round(float(value))):,}"
        if fmt == "signed":
            n = int(round(float(value)))
            return f"+{n}" if n > 0 else str(n)
        if fmt == "float1":
            return f"{float(value):.1f}"
        if fmt == "float2":
            return f"{float(value):.2f}"
        if fmt == "float3":
            return f"{float(value):.3f}".lstrip("0") or "0"
        if fmt == "pct":
            return f"{float(value) * 100:.1f}"
        if fmt == "toi":
            return format_toi(value)
    except (TypeError, ValueError):
        return str(value)
    return str(value)


def format_toi(seconds) -> str:
    if seconds is None:
        return "-"
    try:
        total = int(round(float(seconds)))
    except (TypeError, ValueError):
        return str(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
