import sqlite3
from pathlib import Path

from model.baseline import CIRCUIT_ALIASES

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "f1.db"

def _avg(values):
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 1) if vals else None

def get_circuit_weather(circuit: str) -> dict:
    """Historical weather at a circuit, from the races in the database."""
    key = circuit.lower().strip()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT season, round, event_name, location, rain, "
        "avg_air_temp, avg_track_temp, avg_wind_speed FROM races"
    )]
    conn.close()

    for r in rows:
        r["location"] = CIRCUIT_ALIASES.get(r["location"], r["location"])

    matches = [
        r for r in rows
        if key in r["location"].lower() or key in r["event_name"].lower()
    ]
    if not matches:
        return {"error": f"No races found for '{circuit}'"}

    if len(set(r["location"] for r in matches)) > 1:
        locations = set(r["location"] for r in matches)
        return {"error": f"Multiple locations found for '{circuit}': {', '.join(sorted(locations))}"}

    races_in_data = len(matches)
    rainy_races = sum(1 for r in matches if r["rain"] == 1)
    share_of_races_with_rain = round(rainy_races / races_in_data, 2) if races_in_data > 0 else 0

    avg_air_temp_c = _avg(r["avg_air_temp"] for r in matches if r["avg_air_temp"] is not None)
    avg_track_temp_c = _avg(r["avg_track_temp"] for r in matches if r["avg_track_temp"] is not None)
    avg_wind_speed = _avg(r["avg_wind_speed"] for r in matches if r["avg_wind_speed"] is not None)

    return {
        "circuit": matches[0]["location"],
        "races_in_data": races_in_data,
        "rainy_races": rainy_races,
        "share_of_races_with_rain": share_of_races_with_rain,
        "avg_air_temp_c": avg_air_temp_c,
        "avg_track_temp_c": avg_track_temp_c,
        "avg_wind_speed": avg_wind_speed,
        "is_forecast": False,
        "source": "Historical average from past races in the database, not a forecast",
    }