| Run |            Features           |      Loss      | 2023 (base/model) | 2024 (base/model) | 2025 (base/model) |            Notes             |
|-----|-------------------------------|----------------|-------------------|-------------------|-------------------|------------------------------|
|  1  | grid_position, pit_lane_start |  squared_error |   3.763 / 3.628   |   2.894 / 3.144   |   3.344 / 3.311   |      model loses in 2024     |
|  2  | grid_position, pit_lane_start | absolute_error |   3.763 / 3.494   |   2.894 / 2.816   |   3.344 / 3.073   | beats baseline all 3 seasons |

# Experiment log: finishing-position model

## Setup
- Target: finish_position; metric: mean absolute error (MAE), lower is better
- Baseline: finish = grid position (pit-lane starts set to field size)
- Model: GradientBoostingRegressor(random_state=0), default settings
- Walk-forward test: train on seasons before the test season, test on 2023, 2024, 2025
- 2026 excluded (new regulations; to be tested separately)
- Rows dropped: drivers/teams with no earlier races (no form history). Test rows: 2023 = 436, 2024 = 472, 2025 = 475
- Form features use only earlier races (shift(1)); leak check passed on VER's first 8 rows

## Results (baseline / model, improvement vs baseline)

| Run | Features | Loss | 2023 | 2024 | 2025 | Avg improvement |
|---|---|---|---|---|---|---|
| 1 | grid, pit_lane | squared_error | 3.761 / 3.634 (+3.4%) | 2.883 / 3.151 (-9.3%) | 3.312 / 3.280 (+1.0%) | -1.7% |
| 2 | grid, pit_lane | absolute_error | 3.761 / 3.510 (+6.7%) | 2.883 / 2.823 (+2.1%) | 3.312 / 3.035 (+8.4%) | +5.7% |
| 3 | + driver_form | squared_error | 3.761 / 3.475 (+7.6%) | 2.883 / 2.995 (-3.9%) | 3.312 / 3.258 (+1.6%) | +1.8% |
| 4 | + driver_form | absolute_error | 3.761 / 3.285 (+12.7%) | 2.883 / 2.651 (+8.0%) | 3.312 / 3.041 (+8.2%) | +9.6% |
| 5 | + team_form | squared_error | 3.761 / 3.432 (+8.7%) | 2.883 / 3.037 (-5.3%) | 3.312 / 3.331 (-0.6%) | +0.9% |
| 6 | + team_form | absolute_error | 3.761 / 3.187 (+15.3%) | 2.883 / 2.665 (+7.6%) | 3.312 / 3.054 (+7.8%) | +10.2% |
| 7 | + circuit_form (on run 6) | absolute_error | 3.761 / 3.162 (+15.9%) | 2.883 / 2.723 (+5.6%) | 3.312 / 3.085 (+6.9%) | +9.4% |
| 8 | + rain (on run 6) | absolute_error | 3.761 / 3.197 (+15.0%) | 2.883 / 2.666 (+7.5%) | 3.312 / 3.042 (+8.2%) | +10.2% |
| 9 | + circuit_form + rain (on run 6) | absolute_error | 3.761 / 3.167 (+15.8%) | 2.883 / 2.716 (+5.8%) | 3.312 / 3.086 (+6.8%) | +9.5% |

Total runtime for all 18 evaluations: 1.8 s

## Observations
- absolute_error beat squared_error in every feature set and season (same features, one change)
- driver_form added about 4 points of average improvement under absolute_error (5.7% to 9.6%)
- team_form added little on average (9.6% to 10.2%): it helped 2023 a lot and was flat or slightly worse in 2024 and 2025
- Best run (6) averages above the 10% target, but only 2023 clears it individually; 2024 and 2025 are about 7.6-7.8%
- I tried circuit history and rain, and neither improved the model

## Caveats / next
- Only three test seasons and one random seed, so small differences (under about 0.02 MAE) may be noise
- Ideas: circuit history, rain flag, more test seasons, multiple seeds, 2026 as a separate test

## Decisions
- Frozen model: grid_position, pit_lane_start, driver_form, team_form; loss=absolute_error (run 6)
- Trained on 2018-2024 for the agent tool; 2025-2026 held out
- absolute_error chosen over squared_error (beat it in every comparison)

## Data notes
- Grid position 0 = pit-lane start (checked against real races); set to field size, flagged in pit_lane_start
- Circuit names merged: Monte Carlo/Monaco, Miami Gardens/Miami, Marina Bay/Singapore, Yas Island/Yas Marina
- Rows dropped: drivers/teams with no earlier races (no form history)
- rain flag = rain at any point in session (about 25% of rows); only known after the race, so test results for it are optimistic
- 2026 round 16: labeled "Bahrain Grand Prix", location "Kuala Lumpur", 22 results; relocated race; event name unchanged, location Kuala Lumpur (source: formula1.com article).
- 2026 excluded from training/testing (new regulations); Las Vegas 2026 not yet ingested

## Target status
- M2 target was >=10% lower MAE than baseline on a held-out season
- Best run averages 10.2% across 2023-2025, but 2024 and 2025 are about 7.6-7.8%: met on average, not per season