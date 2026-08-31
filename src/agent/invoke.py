from __future__ import annotations

import json
import os
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def _context_window() -> int:
    raw_value = os.environ.get("AZURE_AI_MODEL_CONTEXT_WINDOW", "400000")
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("AZURE_AI_MODEL_CONTEXT_WINDOW must be an integer") from exc
    if value <= 0:
        raise RuntimeError("AZURE_AI_MODEL_CONTEXT_WINDOW must be greater than zero")
    return value


def _response_payload(response: Any, *, conversation_id: str, model: str) -> dict[str, Any]:
    usage = response.usage
    if usage is None:
        raise RuntimeError("Foundry agent response did not include token usage")
    return {
        "conversation_id": conversation_id,
        "answer": response.output_text,
        "model": model,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
            "context_used_tokens": usage.input_tokens,
            "context_window": _context_window(),
        },
    }


def invoke_agent(
    question: str | None = None,
    filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    agent_name = os.environ.get("STORAGE_AGENT_NAME", "storage-intelligence-agent")
    model = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4-mini")
    prompt = question or os.environ.get(
        "AGENT_QUESTION",
        "Which storage accounts grew abnormally last week?",
    )
    if filters:
        prompt += (
            "\n\nApply these exact storage inventory filters when calling tools:\n"
            + json.dumps(filters, sort_keys=True)
        )
    managed_identity_client_id = os.environ.get("AZURE_CLIENT_ID")
    with (
        DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id) as credential,
        AIProjectClient(credential=credential, endpoint=endpoint) as project,
        project.get_openai_client() as openai,
    ):
        conversation = openai.conversations.create()
        response = openai.responses.create(
            conversation=conversation.id,
            input=prompt,
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        )
        result = _response_payload(response, conversation_id=conversation.id, model=model)
        print(json.dumps(result))
        return result


def main() -> None:
    invoke_agent()


if __name__ == "__main__":
    main()
