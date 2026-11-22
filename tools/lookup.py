import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "f1.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_driver_results(driver_name: str, season: int | None = None,
                       circuit: str | None = None, limit: int = 10) -> dict:
    """Return a driver's race results, optionally filtered by season or circuit."""
    if not DB_PATH.exists():
        return {"error": "Database not found. Run the ingestion script first."}

    limit = max(1, min(int(limit), 25))

    # Build the filters once, then reuse them for both queries.
    where = "WHERE LOWER(res.driver_name) LIKE ?"
    params = [f"%{driver_name.lower().strip()}%"]
    if season is not None:
        where += " AND r.season = ?"
        params.append(int(season))
    if circuit:
        where += " AND (LOWER(r.location) LIKE ? OR LOWER(r.event_name) LIKE ?)"
        params += [f"%{circuit.lower().strip()}%"] * 2

    base = (
        "FROM results res JOIN races r "
        "ON r.season = res.season AND r.round = res.round "
    )

    rows_sql = (
        "SELECT r.season, r.round, r.event_name, r.location, r.rain, "
        "res.driver_name, res.team, res.grid_position, res.finish_position, res.status "
        + base + where +
        " ORDER BY r.season DESC, r.round DESC LIMIT ?"
    )
    totals_sql = (
        "SELECT COUNT(*) AS total_races, "
        "COALESCE(SUM(CASE WHEN res.finish_position = 1 THEN 1 ELSE 0 END), 0) AS wins, "
        "COALESCE(SUM(CASE WHEN res.finish_position <= 3 THEN 1 ELSE 0 END), 0) AS podiums, "
        "AVG(res.finish_position) AS avg_finish "
        + base + where
    )

    with _connect() as conn:
        rows = [dict(row) for row in conn.execute(rows_sql, params + [limit]).fetchall()]
        totals = dict(conn.execute(totals_sql, params).fetchone())

    if not rows:
        return {"error": f"No results found for '{driver_name}' with those filters"}

    avg = totals["avg_finish"]
    return {
        "driver": rows[0]["driver_name"],
        "total_races": totals["total_races"],
        "wins": totals["wins"],
        "podiums": totals["podiums"],
        "average_finish": round(avg, 2) if avg is not None else None,
        "races_returned": len(rows),
        "results": rows,
    }