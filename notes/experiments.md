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

Total runtime for all 18 evaluations: 1.8 s

## Observations
- absolute_error beat squared_error in every feature set and season (same features, one change)
- driver_form added about 4 points of average improvement under absolute_error (5.7% to 9.6%)
- team_form added little on average (9.6% to 10.2%): it helped 2023 a lot and was flat or slightly worse in 2024 and 2025
- Best run (6) averages above the 10% target, but only 2023 clears it individually; 2024 and 2025 are about 7.6-7.8%

## Caveats / next
- Only three test seasons and one random seed, so small differences (under about 0.02 MAE) may be noise
- Ideas: circuit history, rain flag, more test seasons, multiple seeds, 2026 as a separate test