import json
import sys
import time
from pathlib import Path

from google.genai import types

from orchestrator import agent

OUT = Path(__file__).resolve().parent / "results.json"

# acceptable = lists of tool names that count as correct (sorted)
CASES = [
    {"id": 1, "question": "How has Verstappen done at Monza?",
     "acceptable": [["get_driver_results"]]},
    {"id": 2, "question": "How many races has Verstappen won?",
     "acceptable": [["get_driver_results"]]},
    {"id": 3, "question": "Tell me about Red Bull",
     "acceptable": [[]]},
    {"id": 4, "question": "Predict the 2025 Italian Grand Prix and compare it with what actually happened.",
     "acceptable": [["predict_race"]]},
    {"id": 5, "question": "How often does it rain at Monaco?",
     "acceptable": [["get_circuit_weather"]]},
    {"id": 6, "question": "Will it rain at Monza next weekend?",
     "acceptable": [[], ["get_circuit_weather"]]},
    {"id": 7, "question": "What was Lewis Hamilton's average finish in 2024?",
     "acceptable": [["get_driver_results"]]},
    {"id": 8, "question": "Predict the 2025 Monaco Grand Prix.",
     "acceptable": [["predict_race"]]},
    {"id": 9, "question": "How do Leclerc and Norris compare at Silverstone?",
     "acceptable": [["get_driver_results", "get_driver_results"]]},
    {"id": 10, "question": "What is the average track temperature at Silverstone?",
     "acceptable": [["get_circuit_weather"]]},
]


def first_tool_calls(question):
    """One model call; return (sorted tool names requested, seconds)."""
    tools = types.Tool(function_declarations=[
        agent.get_driver_results_declaration,
        agent.predict_race_declaration,
        agent.get_weather_declaration,
    ])
    config = types.GenerateContentConfig(
        tools=[tools], system_instruction=agent.SYSTEM_INSTRUCTION
    )
    contents = [types.Content(role="user", parts=[types.Part(text=question)])]
    t0 = time.time()
    response = agent.call_model("eval", contents, config)
    parts = response.candidates[0].content.parts
    names = sorted(p.function_call.name for p in parts if p.function_call)
    return names, round(time.time() - t0, 2)


def run_select(ids=None):
    saved = {}
    if OUT.exists():
        saved = {r["id"]: r for r in json.loads(OUT.read_text(encoding="utf-8"))}

    for c in CASES:
        if ids and c["id"] not in ids:
            continue
        try:
            names, secs = first_tool_calls(c["question"])
        except agent.ModelUnavailable as e:
            print("STOPPED:", e)
            break
        ok = names in c["acceptable"]
        saved[c["id"]] = {"id": c["id"], "question": c["question"], "tools": names,
                          "acceptable": c["acceptable"], "correct": ok, "seconds": secs}
        print(f"Q{c['id']}: {'PASS' if ok else 'FAIL'}  tools={names}  {secs}s")

    results = [saved[k] for k in sorted(saved)]
    if results:
        n = sum(r["correct"] for r in results)
        print(f"\nTool selection: {n}/{len(results)} = {n / len(results):.0%}")
        OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Saved {OUT}")


def run_full(ids):
    for c in CASES:
        if c["id"] in ids:
            t0 = time.time()
            answer = agent.ask(c["question"])
            print(f"\n--- Q{c['id']} ({round(time.time() - t0, 1)} s) ---\n{answer}\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "full":
        run_full({int(x) for x in args[1:]})
    elif args and args[0] == "select":
        run_select({int(x) for x in args[1:]} or None)
    else:
        run_select()