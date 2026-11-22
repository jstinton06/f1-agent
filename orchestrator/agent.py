from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools.lookup import get_driver_results

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
    "instead of counting yourself, and say plainly when a tool returns an error."
)

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

TOOLS = {"get_driver_results": get_driver_results}


def run_tool(call):
    func = TOOLS.get(call.name)
    if func is None:
        return {"error": f"Unknown tool: {call.name}"}
    try:
        return func(**call.args)
    except Exception as e:
        return {"error": f"Tool failed: {e}"}


def ask(question: str) -> str:
    tools = types.Tool(function_declarations=[get_driver_results_declaration])
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
    print(ask("How has Verstappen done at Monza?"))