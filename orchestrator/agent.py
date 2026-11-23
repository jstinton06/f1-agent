from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools.lookup import get_driver_results
from model.predict import predict_race

load_dotenv()
client = genai.Client()

MODEL = "gemini-3.5-flash"
MAX_STEPS = 5

SYSTEM_INSTRUCTION = (
    "Answer only using tool results. If the tools can't answer, say so. "
    "Do not add reasons, penalties, incidents, or other details the tool didn't return. "
    "Grid position is not pole position, and anything the data doesn't cover should be "
    "reported as unavailable instead of filled in from memory. "
    "The data covers seasons 2018 to 2026. "
    "Use the tool's wins and podiums fields to answer questions about a driver's form "
    "instead of counting yourself, and say plainly when a tool returns an error. "
    "When giving a prediction, say the race was held out of training and the model was trained on 2018 to 2024. "
    "Report model_mae_estimates, model_mae_ranked, and baseline_mae exactly as returned. Do not claim the model beats the baseline based on one race. " 
    "Predictions only exist for races occurring in 2025 and later, which were held out of training. "
)


predict_race_declaration = {
    "name": "predict_race",
    "description": (
        "Predicts the finishing order of a past race that was held out of the model's training "
        "(2025 and later, already in the database) and compares it with what actually happened. "
        "Returns, for each driver, the starting grid position, estimated position (the model's raw estimate), "
        "predicted position (the ranking of those estimates), and actual finish, plus "
        "the average error (in finishing positions) of the model and of a baseline that "
        "assumes everyone finishes where they started. "
        "Use this when asked to predict or compare predictions for a specific race. "
        "Identify the race by season plus either the round number or the circuit name. "
        "Three error values: model_mae_estimates, which returns the average gap in finishing positions between the model's raw estimates and the actual finishes; "
        "model_mae_ranked, which returns the same gap after ranking the estimates; "
        "and baseline_mae, which returns the average gap if every driver simply finished where they started. "
        "After the table, summarize in two or three sentences how the errors compare, using only the returned values. "
        "Explain each error value in one short sentence."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "season": {
                "type": "integer",
                "description": "The season year, such as 2025.",
            },
            "round_number": {
                "type": "integer",
                "description": "Optional round number within the season, such as 16.",
            },
            "circuit": {
                "type": "string",
                "description": "Optional circuit or city name, such as 'Monza'. Use instead of round_number.",
            },
        },
        "required": ["season"],
    },
}


get_driver_results_declaration = {
    "name": "get_driver_results",
    "description": (
        "Looks up a driver's race results, optionally filtered by season or circuit. "
        "Use this when answering questions about a driver's results, form, or history. "
        "Returns the driver's name, total races, wins, podiums, and average finish position "
        "across all matching races, plus a list of the most recent matching races "
        "(newest first) with season, round, event name, location, rain flag, team, "
        "grid position, finish position, and status. "
        "Covers seasons 2018 to 2026. Returns an error if no results are found."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "driver_name": {
                "type": "string",
                "description": "The driver's full name, first and last, such as 'Max Verstappen'.",
            },
            "season": {
                "type": "integer",
                "description": "An optional season filter, such as 2024. If not provided, results from all seasons are included.",
            },
            "circuit": {
                "type": "string",
                "description": "An optional circuit or city filter, such as 'Monza'.",
            },
            "limit": {
                "type": "integer",
                "description": "An optional maximum number of listed races to return. Defaults to 10, maximum 25.",
            },
        },
        "required": ["driver_name"],
    },
}

TOOLS = {
    "get_driver_results": get_driver_results,
    "predict_race": predict_race,
}

def run_tool(call):
    func = TOOLS.get(call.name)
    if func is None:
        return {"error": f"Unknown tool: {call.name}"}
    try:
        return func(**call.args)
    except Exception as e:
        return {"error": f"Tool failed: {e}"}


def ask(question: str) -> str:
    tools = types.Tool(function_declarations=[get_driver_results_declaration, predict_race_declaration])
    config = types.GenerateContentConfig(
        tools=[tools],
        system_instruction=SYSTEM_INSTRUCTION,
    )
    contents = [types.Content(role="user", parts=[types.Part(text=question)])]

    for step in range(MAX_STEPS):
        response = client.models.generate_content(
            model=MODEL, contents=contents, config=config
        )
        model_turn = response.candidates[0].content
        calls = [p.function_call for p in model_turn.parts if p.function_call]

        if not calls:
            return response.text

        contents.append(model_turn)
        result_parts = []
        for call in calls:
            result = run_tool(call)
            result_parts.append(
                types.Part.from_function_response(
                    name=call.name, response={"result": result}
                )
            )
        contents.append(types.Content(role="user", parts=result_parts))

    return f"Stopped after {MAX_STEPS} steps without a final answer."


if __name__ == "__main__":
    print(ask("Predict the 2025 Italian Grand Prix and compare it with what actually happened."))