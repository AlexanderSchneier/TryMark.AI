import json
import os
from openai import OpenAI
from generation.prompts import SYSTEM_PROMPT

client = OpenAI()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1")


def generate_text(payload: dict) -> str:
    """
    Sends a structured, serialized payload to OpenAI and returns text output.
    """

    serialized_payload = json.dumps(payload, indent=2)

    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": serialized_payload
            }
        ],
    )

    return response.output_text
