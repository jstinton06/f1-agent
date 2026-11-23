from functools import lru_cache

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from model.baseline import load_results, clean
from model.train import add_form_features, add_team_form

FEATURES = ["grid_position", "pit_lane_start", "driver_form", "team_form"]
TRAIN_THROUGH = 2024


@lru_cache(maxsize=1)
def _prepare():
    """Build features for every season and train once on seasons up to TRAIN_THROUGH."""
    df = clean(load_results())
    df = add_form_features(df)
    df = add_team_form(df)
    train = df[df["season"] <= TRAIN_THROUGH].dropna(subset=FEATURES)
    model = GradientBoostingRegressor(loss="absolute_error", random_state=0)
    model.fit(train[FEATURES].astype(float), train["finish_position"])
    return model, df


def predict_race(season: int, round_number: int | None = None, circuit: str | None = None) -> dict:
    """Predict the finishing order of a held-out race (after TRAIN_THROUGH) in the database."""
    season = int(season)
    if season <= TRAIN_THROUGH:
        return {"error": f"The model was trained on seasons up to {TRAIN_THROUGH}. "
                         f"Choose a later season so the race was held out of training."}

    model, df = _prepare()

    if round_number is None:
        if not circuit:
            return {"error": "Provide either a round number or a circuit name"}
        key = circuit.lower().strip()
        season_races = df[df["season"] == season][["round", "event_name", "location"]].drop_duplicates()
        hit = season_races[
            season_races["location"].str.lower().str.contains(key, regex=False)
            | season_races["event_name"].str.lower().str.contains(key, regex=False)
        ]
        if hit.empty:
            return {"error": f"No {season} race matches '{circuit}'"}
        if len(hit) > 1:
            return {"error": f"'{circuit}' matches several {season} races: "
                             + ", ".join(f"round {r.round} ({r.event_name})" for r in hit.itertuples())}
        round_number = int(hit.iloc[0]["round"])
    else:
        round_number = int(round_number)

    race = df[(df["season"] == season) & (df["round"] == round_number)]
    if race.empty:
        return {"error": f"No race found for season {season}, round {round_number}"}

    usable = race.dropna(subset=FEATURES).copy()
    skipped = sorted(set(race["driver_abbr"]) - set(usable["driver_abbr"]))

    if usable.empty:
        return {"error": "Not enough earlier races to build features for this race"}

    usable["score"] = model.predict(usable[FEATURES].astype(float))
    estimate_mae = (usable["score"] - usable["finish_position"]).abs().mean()
    usable = usable.sort_values("score")
    usable["predicted_position"] = range(1, len(usable) + 1)

    ranked_mae = (usable["predicted_position"] - usable["finish_position"]).abs().mean()
    baseline_mae = (usable["grid_position"] - usable["finish_position"]).abs().mean()

    drivers = [
        {
            "driver": r["driver_abbr"],
            "team": r["team"],
            "grid_position": int(r["grid_position"]),
            "estimated_position": round(float(r["score"]), 1),
            "predicted_position": int(r["predicted_position"]),
            "actual_finish": int(r["finish_position"]),
        }
        for _, r in usable.iterrows()
    ]

    first = race.iloc[0]
    return {
        "race": first["event_name"],
        "location": first["location"],
        "season": season,
        "round": round_number,
        "held_out": True,
        "note": f"Model trained on 2018-{TRAIN_THROUGH}; uses the stored starting grid and form from earlier races only.",
        "model_mae_estimates": round(float(estimate_mae), 2),
        "model_mae_ranked": round(float(ranked_mae), 2),
        "baseline_mae": round(float(baseline_mae), 2),
        "drivers_without_history": skipped,
        "drivers": drivers,
    }