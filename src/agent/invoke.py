from __future__ import annotations

import json
import os
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
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


def _price_per_million(name: str, default: str) -> Decimal:
    raw_value = os.environ.get(name, default)
    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise RuntimeError(f"{name} must be a decimal number") from exc
    if value < 0:
        raise RuntimeError(f"{name} must not be negative")
    return value


def _cost_estimate(input_tokens: int, output_tokens: int, cached_tokens: int) -> dict[str, Any]:
    if min(input_tokens, output_tokens, cached_tokens) < 0 or cached_tokens > input_tokens:
        raise RuntimeError("Foundry agent response included invalid token usage")
    input_rate = _price_per_million("AZURE_AI_INPUT_COST_PER_MILLION_USD", "0.75")
    cached_input_rate = _price_per_million("AZURE_AI_CACHED_INPUT_COST_PER_MILLION_USD", "0.075")
    output_rate = _price_per_million("AZURE_AI_OUTPUT_COST_PER_MILLION_USD", "4.50")
    million = Decimal(1_000_000)
    estimated_cost = (
        Decimal(input_tokens - cached_tokens) * input_rate
        + Decimal(cached_tokens) * cached_input_rate
        + Decimal(output_tokens) * output_rate
    ) / million
    return {
        "estimated_cost_usd": float(
            estimated_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        ),
        "currency": "USD",
        "input_cost_per_million": float(input_rate),
        "cached_input_cost_per_million": float(cached_input_rate),
        "output_cost_per_million": float(output_rate),
        "disclaimer": "Estimate excludes infrastructure, negotiated pricing, taxes, and non-model charges.",
    }


def _response_payload(response: Any, *, conversation_id: str, model: str) -> dict[str, Any]:
    usage = response.usage
    if usage is None:
        raise RuntimeError("Foundry agent response did not include token usage")
    input_details = getattr(usage, "input_tokens_details", None)
    cached_tokens = int(getattr(input_details, "cached_tokens", 0) or 0)
    return {
        "conversation_id": conversation_id,
        "answer": response.output_text,
        "model": model,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
            "cached_input_tokens": cached_tokens,
            "context_used_tokens": usage.input_tokens,
            "context_window": _context_window(),
        },
        "cost": _cost_estimate(usage.input_tokens, usage.output_tokens, cached_tokens),
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
