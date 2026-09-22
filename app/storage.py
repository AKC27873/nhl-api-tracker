
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshot (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_on TEXT    NOT NULL,   -- YYYY-MM-DD, one capture per day
    captured_at TEXT    NOT NULL,   -- full UTC timestamp
    season      INTEGER NOT NULL,
    game_type   INTEGER NOT NULL,
    kind        TEXT    NOT NULL,   -- skater | goalie | team
    entity_id   INTEGER NOT NULL,   -- playerId or teamId
    name        TEXT,
    team        TEXT,
    payload     TEXT    NOT NULL    -- the normalised row, as JSON
);

CREATE UNIQUE INDEX IF NOT EXISTS snapshot_unique
    ON snapshot (captured_on, season, game_type, kind, entity_id);

CREATE INDEX IF NOT EXISTS snapshot_entity
    ON snapshot (kind, entity_id, season, game_type, captured_on);
"""


class SnapshotStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._ready = False

    @contextmanager
    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            if not self._ready:
                conn.executescript(SCHEMA)
                self._ready = True
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self._connect():
            pass

    def save_rows(self, kind: str, season: int, game_type: int, rows: list[dict],
                  on: date | None = None) -> int:
        """Write one capture. Re-running on the same day overwrites it."""
        captured_on = (on or datetime.now(timezone.utc).date()).isoformat()
        captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

        payload = []
        for row in rows:
            entity_id = row.get("player_id") or row.get("team_id")
            if entity_id is None:
                continue
            payload.append((
                captured_on, captured_at, int(season), int(game_type), kind,
                int(entity_id), row.get("name"), row.get(
                    "team") or row.get("abbrev"),
                json.dumps(row, separators=(",", ":")),
            ))

        with self._connect() as conn:
            conn.executemany(
                """INSERT INTO snapshot
                       (captured_on, captured_at, season, game_type, kind, entity_id,
                        name, team, payload)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (captured_on, season, game_type, kind, entity_id)
                   DO UPDATE SET payload = excluded.payload,
                                 captured_at = excluded.captured_at,
                                 name = excluded.name,
                                 team = excluded.team""",
                payload,
            )
        return len(payload)

    def capture_dates(self, kind: str, season: int, game_type: int, limit: int = 30) -> list[str]:
        """Most recent capture dates, newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT DISTINCT captured_on FROM snapshot
                   WHERE kind = ? AND season = ? AND game_type = ?
                   ORDER BY captured_on DESC LIMIT ?""",
                (kind, int(season), int(game_type), limit),
            ).fetchall()
        return [r["captured_on"] for r in rows]

    def rows_on(self, kind: str, season: int, game_type: int, captured_on: str) -> dict[int, dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT entity_id, payload FROM snapshot
                   WHERE kind = ? AND season = ? AND game_type = ? AND captured_on = ?""",
                (kind, int(season), int(game_type), captured_on),
            ).fetchall()
        return {r["entity_id"]: json.loads(r["payload"]) for r in rows}

    def movers(self, kind: str, season: int, game_type: int, stat: str, limit: int = 25,
               since: str | None = None) -> dict:
        """Difference between the newest capture and an earlier one."""
        dates = self.capture_dates(kind, season, game_type, limit=400)
        if len(dates) < 2:
            return {"rows": [], "latest": dates[0] if dates else None, "previous": None}

        latest = dates[0]
        previous = since if since in dates and since != latest else dates[1]
        now_rows = self.rows_on(kind, season, game_type, latest)
        then_rows = self.rows_on(kind, season, game_type, previous)

        out = []
        for entity_id, current in now_rows.items():
            before = then_rows.get(entity_id)
            if not before:
                continue
            try:
                delta = float(current.get(stat) or 0) - \
                    float(before.get(stat) or 0)
                games = float(current.get("gp") or 0) - \
                    float(before.get("gp") or 0)
            except (TypeError, ValueError):
                continue
            if delta == 0 and games == 0:
                continue
            out.append({**current, "delta": delta, "games_played": games,
                        "before": before.get(stat)})

        out.sort(key=lambda r: r["delta"], reverse=True)
        return {"rows": out[:limit], "latest": latest, "previous": previous}

    def history(self, kind: str, entity_id: int, season: int, game_type: int) -> list[dict]:
        """Every capture held for one player or team, oldest first."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT captured_on, payload FROM snapshot
                   WHERE kind = ? AND entity_id = ? AND season = ? AND game_type = ?
                   ORDER BY captured_on ASC""",
                (kind, int(entity_id), int(season), int(game_type)),
            ).fetchall()
        return [{"captured_on": r["captured_on"], **json.loads(r["payload"])} for r in rows]

    def prune(self, keep_days: int = 400) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM snapshot WHERE captured_on < date('now', ?)",
                (f"-{int(keep_days)} days",),
            )
            return cur.rowcount
