from __future__ import annotations

import json
import logging
from typing import Any

import azure.durable_functions as df
import azure.functions as func

from storage_intelligence import IntelligenceEngine, generate_accounts
from storage_intelligence.analytics import portfolio_summary

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)
ACCOUNTS = generate_accounts()
ENGINE = IntelligenceEngine(ACCOUNTS)


def _json(payload: Any, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, separators=(",", ":")),
        status_code=status,
        mimetype="application/json",
    )


@app.route(route="healthz", methods=["GET"])
def healthz(req: func.HttpRequest) -> func.HttpResponse:
    return _json({"status": "healthy", "service": "storage-intelligence-tools"})


@app.route(route="tools/portfolio", methods=["POST"])
def tool_portfolio(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json() if req.get_body() else {}
        filters = payload.get("filters", {})
        rows = ENGINE.filter(filters)
        answer = ENGINE.answer("portfolio overview", filters)
        answer["data"] = portfolio_summary(rows)
        return _json(answer)
    except (ValueError, json.JSONDecodeError) as exc:
        return _json({"error": str(exc)}, 400)


@app.route(route="tools/query", methods=["POST"])
def tool_query(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
        return _json(ENGINE.answer(payload.get("question", ""), payload.get("filters", {})))
    except (ValueError, json.JSONDecodeError) as exc:
        return _json({"error": str(exc)}, 400)


@app.route(route="orchestrations/collect", methods=["POST"])
@app.durable_client_input(client_name="client")
async def collect_start(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    payload = req.get_json() if req.get_body() else {"mode": "synthetic"}
    if payload.get("mode", "synthetic") != "synthetic":
        return _json(
            {
                "error": "Production connectors are disabled in the pilot.",
                "required_flags": [
                    "ENABLE_RESOURCE_GRAPH",
                    "ENABLE_BLOB_INVENTORY",
                    "ENABLE_AZURE_MONITOR_METRICS",
                    "ENABLE_COST_EXPORTS",
                    "ENABLE_DATABRICKS_EXPORTS",
                ],
            },
            409,
        )
    instance_id = await client.start_new("collect_orchestrator", client_input=payload)
    return client.create_check_status_response(req, instance_id)


@app.orchestration_trigger(context_name="context")
def collect_orchestrator(context: df.DurableOrchestrationContext):
    payload = context.get_input() or {}
    partitions = [
        {"start": start, "count": min(250, len(ACCOUNTS) - start), "mode": payload.get("mode", "synthetic")}
        for start in range(0, len(ACCOUNTS), 250)
    ]
    results = yield context.task_all(
        [context.call_activity("collect_partition", partition) for partition in partitions]
    )
    return {
        "mode": "synthetic",
        "partitions": len(results),
        "records": sum(result["records"] for result in results),
        "idempotency_keys": [result["idempotency_key"] for result in results],
    }


@app.activity_trigger(input_name="partition")
def collect_partition(partition: dict) -> dict[str, Any]:
    start = int(partition["start"])
    count = int(partition["count"])
    logging.info("Collecting synthetic partition start=%s count=%s", start, count)
    return {
        "records": count,
        "idempotency_key": f"synthetic-v1-{start:05d}-{count}",
    }
