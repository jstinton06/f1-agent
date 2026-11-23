import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "f1.db"
TEST_SEASON = 2025

CIRCUIT_ALIASES = {
    "Monte Carlo": "Monaco",
    "Miami Gardens": "Miami",
    "Marina Bay": "Singapore",
    "Yas Island": "Yas Marina",
}

def load_results() -> pd.DataFrame:
    """All driver-race rows with grid and finishing positions."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT r.season, r.round, r.event_name, r.location, r.rain, "
        "res.driver_abbr, res.team, res.grid_position, res.finish_position "
        "FROM results res JOIN races r ON r.season = res.season AND r.round = res.round",
        conn,
    )
    conn.close()
    df["location"] = df["location"].replace(CIRCUIT_ALIASES)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop missing values and handle pit-lane starts (grid_position == 0)."""
    df = df.dropna(subset=["grid_position", "finish_position"]).copy()
    df["pit_lane_start"] = df["grid_position"] == 0

    field_size = df.groupby(["season", "round"])["driver_abbr"].transform("count")
    df.loc[df["pit_lane_start"], "grid_position"] = field_size[df["pit_lane_start"]]
    return df


def mae(df: pd.DataFrame) -> float:
    """Mean absolute error of the baseline 'finish = grid'."""
    return (df["grid_position"] - df["finish_position"]).abs().mean()


if __name__ == "__main__":
    df = clean(load_results())
    df = df[df["season"] < 2026]  # leave 2026 out for now
    test = df[df["season"] == TEST_SEASON]
    print(f"Baseline MAE on {TEST_SEASON}: {mae(test):.3f} ({len(test)} rows)")
    for season, season_df in df.groupby("season"):
        print(f"Baseline MAE on {season}: {mae(season_df):.3f} ({len(season_df)} rows)")