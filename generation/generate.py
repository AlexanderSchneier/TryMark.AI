import os
from openai import OpenAI
from openai import RateLimitError, APIError
from generation.prompts import SYSTEM_PROMPT

client = OpenAI()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1")


def generate_text(payload: dict) -> str:
    """
    Sends a structured drafting prompt to OpenAI and returns the generated section text.
    """

    # We now expect payload to contain a single drafting prompt string
    prompt_text = payload.get("prompt")

    if not prompt_text:
        raise ValueError("Payload missing 'prompt' field for generation.")

    try:
        response = client.responses.create(
            model=MODEL_NAME,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ],
            temperature=0.2,  # Low temperature = stable legal drafting
        )

        return response.output_text.strip()

    except RateLimitError:
        return "\n⚠️ API quota exceeded. Please check billing.\n"

    except APIError as e:
        return f"\n⚠️ OpenAI API error: {str(e)}\n"

    except Exception as e:
        return f"\n⚠️ Unexpected generation error: {str(e)}\n"
