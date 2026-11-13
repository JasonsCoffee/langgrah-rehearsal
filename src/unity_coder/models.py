"""Model adapters.

The coder and judge are behind a narrow protocol so the graph can run against
a real provider, a scripted fake, or your own local model endpoint without
touching node code.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol, runtime_checkable

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


@runtime_checkable
class ModelClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


def extract_json(text: str) -> Any:
    """Pull the first JSON object/array out of a model response."""
    match = _JSON_FENCE.search(text)
    candidate = match.group(1) if match else text
    candidate = candidate.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = candidate.find(opener)
        end = candidate.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"no JSON found in model response: {text[:400]}")


class ChatModelClient:
    """LangChain-backed client. Provider is chosen by ``UNITY_CODER_MODEL``."""

    def __init__(self, model_id: str | None = None, temperature: float = 0.0):
        from langchain.chat_models import init_chat_model

        resolved = model_id or os.environ.get("UNITY_CODER_MODEL")
        if not resolved:
            raise RuntimeError(
                "UNITY_CODER_MODEL is not set. Example: "
                'UNITY_CODER_MODEL="anthropic:claude-sonnet-4-5" in .env'
            )
        self._model = init_chat_model(resolved, temperature=temperature)

    def complete(self, system: str, user: str) -> str:
        message = self._model.invoke([("system", system), ("human", user)])
        content = getattr(message, "content", message)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        return str(content)


class ScriptedClient:
    """Deterministic fake so the graph can be exercised without a provider."""

    def __init__(self, coder_payload: dict[str, Any] | None = None):
        self._coder_payload = coder_payload or {
            "patches": [],
            "notes": "scripted client: no patches produced",
            "ok": True,
        }

    def complete(self, system: str, user: str) -> str:
        if "[JUDGE]" in system:
            return json.dumps(
                {
                    "passed": True,
                    "failed_units": [],
                    "learned_constraints": [],
                    "summary": "scripted judge: auto-pass",
                }
            )
        return json.dumps(self._coder_payload)
