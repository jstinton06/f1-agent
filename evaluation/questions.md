# Evaluation questions

## Q1
- Question: How has Verstappen done at Monza?
- Expected tool(s): get_driver_results
- Correct answer should include: 9 races, 3 wins, 4 podiums, average finish 6.67 (from the database)
- Must NOT include: stories, penalties, pole counts, reasons
- Result so far: passed (after the system instruction was added)

## Q2
- Question: How many races has Verstappen won?
- Expected tool(s): get_driver_results
- Correct answer should include: 71
- Result so far: passed

## Q3
- Question: Tell me about Red Bull
- Expected tool(s): none (out of scope)
- Correct answer should: say the tools only cover driver results and race predictions
- Result so far: declined, but only after a wasted tool call with "Red Bull" as a driver name

## Q4
- Question: Predict the 2025 Italian Grand Prix and compare it with what actually happened.
- Expected tool(s): predict_race, called once
- Correct answer should include: errors 2.84 (estimates), 3.4 (ranked), 3.0 (baseline); says the race was held out of training and the model was trained on 2018-2024
- Must NOT include: invented reasons for any driver's result; a claim that the model beats the baseline based on one race

### Run on 2026-11-23 (run_id 8ca6f746)
- Tool calls: predict_race(season=2025, circuit="Monza"), one call, no wasted lookup
- LLM calls: 2; total time 16.14 s; tokens 1,231 (step 1) and 5,660 (step 2)
- Result: all 20 table rows and all three errors match the tool output; error explanations are correct; no invented reasons
- Weaknesses:
  1. Latency is over the 15 s target (step 2 took about 14 s, mostly writing out a 20-row table)
  2. The summary says the raw estimates were closest overall, without saying this is a single race
- Fixes to try: tell the model to show only the top 10 rows; add a single-race caveat rule to the system instruction; rerun and compare