from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from .cosmos_inventory import get_cosmos_container

DOCUMENT_TYPE = "agent-query-usage"
SCHEMA_VERSION = 1


def _utc_month(now: datetime | None = None) -> tuple[datetime, datetime, str]:
    current = (now or datetime.now(UTC)).astimezone(UTC)
    start = datetime(current.year, current.month, 1, tzinfo=UTC)
    if current.month == 12:
        reset = datetime(current.year + 1, 1, 1, tzinfo=UTC)
    else:
        reset = datetime(current.year, current.month + 1, 1, tzinfo=UTC)
    return start, reset, start.strftime("%Y-%m")


def _usage_container() -> Any:
    if os.getenv("COSMOS_INVENTORY_ENABLED", "false").lower() != "true":
        raise RuntimeError("Cosmos agent usage persistence is not enabled")
    return get_cosmos_container()


def _nonnegative_int(value: Any, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Foundry agent {name} must be an integer") from exc
    if parsed < 0:
        raise RuntimeError(f"Foundry agent {name} must not be negative")
    return parsed


def _cost(value: Any) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RuntimeError("Foundry agent estimated cost must be a decimal number") from exc
    if parsed < 0:
        raise RuntimeError("Foundry agent estimated cost must not be negative")
    return parsed


def get_monthly_agent_usage(
    *,
    now: datetime | None = None,
    container: Any | None = None,
) -> dict[str, Any]:
    start, reset, period = _utc_month(now)
    partition = f"__agent_usage__:{period}"
    target = container or _usage_container()
    rows = list(
        target.query_items(
            query=(
                "SELECT COUNT(1) AS query_count, "
                "SUM(c.input_tokens) AS input_tokens, "
                "SUM(c.cached_input_tokens) AS cached_input_tokens, "
                "SUM(c.output_tokens) AS output_tokens, "
                "SUM(c.total_tokens) AS total_tokens, "
                "SUM(c.estimated_cost_usd) AS estimated_cost_usd "
                "FROM c WHERE c.document_type = @document_type AND c.period = @period"
            ),
            parameters=[
                {"name": "@document_type", "value": DOCUMENT_TYPE},
                {"name": "@period", "value": period},
            ],
            partition_key=partition,
        )
    )
    aggregate = rows[0] if rows else {}
    return {
        "period": period,
        "period_start": start.isoformat(),
        "resets_at": reset.isoformat(),
        "query_count": int(aggregate.get("query_count") or 0),
        "input_tokens": int(aggregate.get("input_tokens") or 0),
        "cached_input_tokens": int(aggregate.get("cached_input_tokens") or 0),
        "output_tokens": int(aggregate.get("output_tokens") or 0),
        "total_tokens": int(aggregate.get("total_tokens") or 0),
        "estimated_cost_usd": float(
            _cost(aggregate.get("estimated_cost_usd") or 0).quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP,
            )
        ),
        "currency": "USD",
    }


def record_agent_usage(
    agent_result: dict[str, Any],
    *,
    now: datetime | None = None,
    container: Any | None = None,
) -> dict[str, Any]:
    current = (now or datetime.now(UTC)).astimezone(UTC)
    _, _, period = _utc_month(current)
    partition = f"__agent_usage__:{period}"
    conversation_id = str(agent_result.get("conversation_id") or "").strip()
    model = str(agent_result.get("model") or "").strip()
    if not conversation_id or not model:
        raise RuntimeError("Foundry agent usage is missing conversation or model metadata")

    usage = agent_result.get("usage")
    cost = agent_result.get("cost")
    if not isinstance(usage, dict) or not isinstance(cost, dict):
        raise RuntimeError("Foundry agent usage or cost metadata is missing")

    input_tokens = _nonnegative_int(usage.get("input_tokens"), "input tokens")
    cached_input_tokens = _nonnegative_int(
        usage.get("cached_input_tokens", 0),
        "cached input tokens",
    )
    output_tokens = _nonnegative_int(usage.get("output_tokens"), "output tokens")
    total_tokens = _nonnegative_int(usage.get("total_tokens"), "total tokens")
    if cached_input_tokens > input_tokens or total_tokens != input_tokens + output_tokens:
        raise RuntimeError("Foundry agent response included inconsistent token usage")
    estimated_cost = _cost(cost.get("estimated_cost_usd"))

    target = container or _usage_container()
    target.upsert_item(
        body={
            "id": f"agent-usage-{hashlib.sha256(conversation_id.encode('utf-8')).hexdigest()}",
            "subscription_id": partition,
            "document_type": DOCUMENT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "period": period,
            "recorded_at": current.isoformat(),
            "conversation_id": conversation_id,
            "model": model,
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": float(estimated_cost),
            "currency": str(cost.get("currency") or "USD"),
        }
    )
    return get_monthly_agent_usage(now=current, container=target)
