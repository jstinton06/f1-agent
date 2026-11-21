from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools.fake_tools import get_driver_info

load_dotenv()
client = genai.Client()

get_driver_info_declaration = {
    "name": "get_driver_info",
    "description": "Looks up information about a specific F1 driver. Returns the driver's team, car number, and nationality. "
    "Use this when answering questions about a specific driver. Returns an error if the driver isn't found.",
    "parameters": {
        "type": "object",
        "properties": {
            "driver_name": {
                "type": "string",
                "description": "The driver's full name, first and last, such as 'Max Verstappen'.",
            },
        },
        "required": ["driver_name"],
    },
}

tools = types.Tool(function_declarations=[get_driver_info_declaration])
config = types.GenerateContentConfig(tools=[tools])

question = "Which teams do Max Verstappen and Lewis Hamilton race for?"

MAX_STEPS = 5
contents = [types.Content(role="user", parts=[types.Part(text=question)])]

for step in range(MAX_STEPS):
    response = client.models.generate_content(
        model="gemini-3.5-flash", contents=contents, config=config
    )
    model_turn = response.candidates[0].content
    calls = [part.function_call for part in model_turn.parts if part.function_call]

    if not calls:
        # no tool requested, so this is the final answer: print it and stop
        print(response.text)
        break

    contents.append(model_turn)
    result_parts = []
    for call in calls:
        # run your function with call.args, then build a function-response part
        # for it (the same Part.from_function_response you used before)
        result = get_driver_info(**call.args)
        result_parts.append(types.Part.from_function_response(name=call.name, response={"result": result}))

    contents.append(types.Content(role="user", parts=result_parts))
else:
    # the loop hit MAX_STEPS without a final answer: print a clear message
    print(f"Stopped after {MAX_STEPS} steps without a final answer.")


