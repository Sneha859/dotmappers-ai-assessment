import json

import requests

from app.llm.prompts import SYSTEM_PROMPT
from app.models.schemas import GeneratedQuery


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "qwen3:4b-instruct"


def generate_sql(question: str) -> GeneratedQuery:
    """
    Convert a natural-language question into a structured SQL query
    using the local Ollama model.
    """

    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "sql": {"type": "string"},
                "explanation": {"type": "string"},
            },
            "required": [
                "intent",
                "sql",
                "explanation",
            ],
        },
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        "options": {
            "temperature": 0,
            "num_ctx": 4096,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            "Unable to connect to the local Ollama server."
        ) from exc

    try:
        data = response.json()
        content = data["message"]["content"]
        parsed = json.loads(content)

        return GeneratedQuery.model_validate(parsed)

    except (KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Ollama returned an invalid structured response."
        ) from exc