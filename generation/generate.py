from openai import OpenAI
from generation.prompts import SYSTEM_PROMPT

client = OpenAI()

def generate_text(payload: dict) -> str:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": payload
            }
        ]
    )

    return response.output_text
