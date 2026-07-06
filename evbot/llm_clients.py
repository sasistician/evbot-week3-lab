"""Single call-site for every LLM generation in EVBot.

Everything in this lab runs on local models via Ollama. Adding Claude later
means adding one branch inside `call_llm` (e.g. routing a model name like
"claude-*" to the Anthropic SDK instead) — callers never need to change.
"""

import ollama

from evbot.config import OLLAMA_HOST

_client = ollama.Client(host=OLLAMA_HOST)


def call_llm(model: str, prompt: str, system: str | None = None) -> str:
    """Generate a response from the given local Ollama model."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = _client.chat(model=model, messages=messages)
    return response["message"]["content"]
