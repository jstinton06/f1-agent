import re

NUMBER = re.compile(r"\d+(?:\.\d+)?")
# numbers the model may state that aren't tool output (training years)
ALLOWED = {2018.0, 2024.0, 2025.0, 2026.0}


def numbers_in(text):
    return {round(float(x), 1) for x in NUMBER.findall(text)}


def numbers_in_results(obj, found=None):
    """Collect every number found anywhere in a tool result (nested dicts and lists)."""
    found = set() if found is None else found

    if isinstance(obj, dict):
        for value in obj.values():
            numbers_in_results(value, found)
    elif isinstance(obj, list):
        for item in obj:
            numbers_in_results(item, found)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        found.add(round(float(obj), 1))
        if 0 < obj < 1:
            found.add(round(float(obj) * 100, 1))
    elif isinstance(obj, str):
        found |= numbers_in(obj)

    return found


def check_answer(answer, question, tool_results):
    """Return the numbers in the answer that no tool result (or the question) supports."""
    supported = ALLOWED | numbers_in(question)
    for result in tool_results:
        supported |= numbers_in_results(result)

    return sorted(numbers_in(answer) - supported)