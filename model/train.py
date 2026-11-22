import time

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from model.baseline import load_results, clean, mae

TARGET = "finish_position"
TEST_SEASONS = (2023, 2024, 2025)
LEAK_CHECK = True  # set to False once you've verified it

FEATURE_SETS = {
    "grid + pit_lane": ["grid_position", "pit_lane_start"],
    "+ driver_form": ["grid_position", "pit_lane_start", "driver_form"],
    "+ team_form": ["grid_position", "pit_lane_start", "driver_form", "team_form"],
}
LOSSES = ("squared_error", "absolute_error")


def add_form_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add features built only from earlier races."""
    df = df.sort_values(["season", "round"]).copy()
    by_driver = df.groupby("driver_abbr")["finish_position"]
    df["driver_form"] = by_driver.transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    )
    return df


def add_team_form(df: pd.DataFrame) -> pd.DataFrame:
    """Average finish of each team's previous races (both cars), excluding the current race."""
    team_race = (
        df.groupby(["team", "season", "round"])["finish_position"]
        .mean()
        .reset_index()
        .sort_values(["season", "round"])
    )
    team_race["team_form"] = team_race.groupby("team")["finish_position"].transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    )
    return df.merge(
        team_race[["team", "season", "round", "team_form"]],
        on=["team", "season", "round"],
        how="left",
    )


def evaluate(df, test_season, features, loss):
    """Train on seasons before test_season, test on test_season.
    Returns (baseline MAE, model MAE, number of test rows)."""
    train = df[df["season"] < test_season]
    test = df[df["season"] == test_season]

    X_train = train[features].astype(float)
    X_test = test[features].astype(float)

    model = GradientBoostingRegressor(loss=loss, random_state=0)
    model.fit(X_train, train[TARGET])
    preds = model.predict(X_test)

    model_mae = (test[TARGET] - preds).abs().mean()
    return mae(test), model_mae, len(test)


if __name__ == "__main__":
    t0 = time.time()
    df = clean(load_results())
    df = df[df["season"] < 2026]
    df = add_form_features(df)

    if LEAK_CHECK:
        check = df[df["driver_abbr"] == "VER"].sort_values(["season", "round"])
        print(check[["season", "round", "finish_position", "driver_form"]].head(8))

    df = df.dropna(subset=["driver_form"])
    df = add_team_form(df)
    df = df.dropna(subset=["team_form"])

    for name, features in FEATURE_SETS.items():
        for loss in LOSSES:
            print(f"{name} | {loss}")
            for season in TEST_SEASONS:
                base, model_err, n = evaluate(df, season, features, loss)
                print(f"  {season}: baseline {base:.3f}  model {model_err:.3f}  ({n} rows)")
    print(f"Total time: {time.time() - t0:.1f} s")