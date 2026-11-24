# F1 Agent

An LLM agent (Gemini Flash) built for PRV 201, Track A. It answers questions about Formula 1 driver results, historical circuit weather, and predictions for held-out 2025+ races. It decides which tool to call, runs it, and answers only from the tool results.

## How it works

- **Orchestrator** (`orchestrator/agent.py`): the LLM reads the question, calls tools in a loop (up to 5 steps), and writes the answer. Retries temporary API errors (503, per-minute 429) and returns a clear message if the daily limit is reached.
- **Tools**
  - `get_driver_results` (`tools/lookup.py`): fixed, parameterized SQLite queries on past results (totals, wins, podiums, recent races).
  - `get_circuit_weather` (`tools/weather.py`): historical averages (rain share, air and track temperature, wind speed) at a circuit. This is not a forecast.
  - `predict_race` (`model/predict.py`): predicts the finishing order of a race held out of training (2025 and later) and compares it with the actual result and a grid-position baseline.
- **Output check** (`orchestrator/check.py`): flags numbers in an answer that no tool result supports and logs them (it does not change the answer).
- **Logging**: every question, model call, tool call, and answer is written to `logs/runs.jsonl` with a run ID.
- **Offline pipeline**: `ingestion/ingest.py` pulls race results and weather from FastF1 into SQLite (`data/f1.db`); `model/` builds features, the baseline, and the gradient-boosted model.
- **Evaluation harness** (`evaluation/run_eval.py`): checks whether the model picks the correct tool(s) for a set of 10 questions and saves `evaluation/results.json`.

Not implemented: live in-race prediction, race-strategy prediction, and weather forecasts for upcoming races (planned as future work).

## Layout

```
ingestion/     FastF1 -> SQLite
tools/         lookup.py, weather.py
model/         baseline.py, train.py, predict.py
orchestrator/  agent.py, check.py
evaluation/    run_eval.py, questions.md, results.json
notes/         experiments.md (model experiment log)
docs/          sample_trace.jsonl (one logged run)
data/f1.db     processed race database (2018-2026)
```

## Setup

1. Clone the repo and open it in VS Code.
2. Create and activate a virtual environment (Python 3.13 was used):
   - `python -m venv .venv`
   - Windows: `.venv\Scripts\Activate.ps1` / macOS and Linux: `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. Create a file named `.env` in the project root:
    1. GEMINI_API_KEY=your_key
    2. F1_USERNAME=your_f1_email
    3. F1_PASSWORD=your_password

- `GEMINI_API_KEY` is needed only for the agent and `run_eval`.
- `F1_USERNAME` and `F1_PASSWORD` are needed only to ingest new data (FastF1 now requires an F1 TV Access account or higher).
- Never commit `.env`; it is listed in `.gitignore`.

`data/f1.db` is included, so the tools and model can be run without an F1 account.

## Running

- Ingest more data (optional): `python -m ingestion.ingest 2024` (more years can be added, e.g. `2023 2022`). Data covers 2018 to the latest completed race.
- Train and compare models: `python -m model.baseline` (grid-position baseline) and `python -m model.train` (feature experiments).
- Ask the agent a question: edit the question at the bottom of `orchestrator/agent.py`, then run `python -m orchestrator.agent`.
- Check tool selection: `python -m evaluation.run_eval` (about 10 API requests; `select 10` re-runs one question, `full 4` runs a full answer).

## Limits

- The free Gemini tier allows 20 requests per day. A question takes at least two (the tool call and the final answer), so about 8 to 10 questions fit in a day. The free tier is also sometimes busy (503 errors) and slow.
- FastF1 allows about 500 calls per hour, so ingesting takes roughly one season per hour.
- Data covers 2018 onward. Older seasons are not used because regulation changes make them less comparable.
- The agent predicts past (held-out) races, not future ones.

## Results

Model experiments are logged in [notes/experiments.md](notes/experiments.md).

Best model: gradient-boosted trees on grid position, pit-lane start, driver form, and team form, trained with absolute-error loss (mean absolute error in finishing positions, lower is better):

| Test season | Baseline (finish = grid) | Model | Improvement |
|---|---|---|---|
| 2023 | 3.761 | 3.187 | 15.3% |
| 2024 | 2.883 | 2.665 | 7.6% |
| 2025 | 3.312 | 3.054 | 7.8% |

The average improvement is about 10%. Circuit history and rain added no gain. The model's raw estimates beat the baseline, but turning them into a strict 1-to-20 ranking did not (2025: 3.377 ranked vs 3.312 baseline).

Tool selection: the correct tool(s) were chosen on 10 of 10 test questions (small, self-written set; only the first tool choice is checked, and answer quality was reviewed separately in `evaluation/questions.md`).
