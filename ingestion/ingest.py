import os
import sys
import time
import sqlite3

import pandas as pd
import fastf1
from dotenv import load_dotenv

load_dotenv()
os.makedirs("data", exist_ok=True)
os.makedirs("cache", exist_ok=True)
fastf1.Cache.enable_cache("cache")  # deprecated, still works; swap for Cache.configure later

DB_PATH = "data/f1.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS races (
    season INTEGER NOT NULL,
    round INTEGER NOT NULL,
    event_name TEXT,
    location TEXT,
    country TEXT,
    race_date TEXT,
    rain INTEGER,
    avg_air_temp REAL,
    avg_track_temp REAL,
    avg_wind_speed REAL,
    PRIMARY KEY (season, round)
);
CREATE TABLE IF NOT EXISTS results (
    season INTEGER NOT NULL,
    round INTEGER NOT NULL,
    driver_abbr TEXT NOT NULL,
    driver_name TEXT,
    team TEXT,
    grid_position INTEGER,
    finish_position INTEGER,
    status TEXT,
    points REAL,
    PRIMARY KEY (season, round, driver_abbr),
    FOREIGN KEY (season, round) REFERENCES races (season, round)
);
"""


def num(x, cast=float):
    """Convert pandas values (including NaN) to plain Python numbers or None."""
    if x is None or pd.isna(x):
        return None
    return cast(x)


def weather_summary(session):
    """One row of weather per race: rain flag and average temperatures and wind."""
    try:
        w = session.weather_data
    except Exception:
        return (None, None, None, None)
    if w is None or len(w) == 0:
        return (None, None, None, None)
    return (
        int(bool(w["Rainfall"].any())),
        num(w["AirTemp"].mean()),
        num(w["TrackTemp"].mean()),
        num(w["WindSpeed"].mean()),
    )


def ingest_season(conn, season):
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    for _, ev in schedule.iterrows():
        rnd = int(ev["RoundNumber"])

        if pd.Timestamp(ev["EventDate"]) > pd.Timestamp.now():
            print(f"{season} round {rnd}: in the future, skipping")
            continue

        done = conn.execute(
            "SELECT 1 FROM races WHERE season=? AND round=?", (season, rnd)
        ).fetchone()
        if done:
            print(f"{season} round {rnd}: already in database, skipping")
            continue

        try:
            session = fastf1.get_session(season, rnd, "R")
            session.load(laps=False, telemetry=False, weather=True, messages=False)
            results = session.results
            if results is None or len(results) == 0:
                raise ValueError("empty results")

            rain, air, track, wind = weather_summary(session)
            conn.execute(
                "INSERT OR REPLACE INTO races VALUES (?,?,?,?,?,?,?,?,?,?)",
                (season, rnd, ev["EventName"], ev["Location"], ev["Country"],
                 str(pd.Timestamp(ev["EventDate"]).date()), rain, air, track, wind),
            )
            for _, r in results.iterrows():
                conn.execute(
                    "INSERT OR REPLACE INTO results VALUES (?,?,?,?,?,?,?,?,?)",
                    (season, rnd, r["Abbreviation"], r["FullName"], r["TeamName"],
                     num(r["GridPosition"], int), num(r["Position"], int),
                     r["Status"], num(r["Points"])),
                )
            conn.commit()
            print(f"{season} round {rnd}: {ev['EventName']} saved ({len(results)} drivers)")
        except Exception as e:
            conn.rollback()
            print(f"FAILED {season} round {rnd}: {e}")

        time.sleep(5)  # be gentle with the data servers


if __name__ == "__main__":
    seasons = [int(s) for s in sys.argv[1:]] or [2024]
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    for s in seasons:
        ingest_season(conn, s)
    conn.close()