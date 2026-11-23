from unittest.mock import patch
from google.genai import errors
import orchestrator.agent as agent


def fail(*args, **kwargs):
    raise errors.ClientError(429, {"error": {"message": "requests per day PerDay"}}, None)


with patch.object(agent.client.models, "generate_content", fail):
    print(agent.ask("test question"))