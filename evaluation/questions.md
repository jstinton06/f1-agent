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
- Expected tool(s): predict_race (once)
- Correct answer should include: errors 2.84 / 3.4 / 3.0, says race was held out of training
- Must NOT include: invented reasons for any driver's result
- Result so far: numbers all correct; weakness: lists data without comparing it