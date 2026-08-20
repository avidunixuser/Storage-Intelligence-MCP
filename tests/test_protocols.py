from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from protocols.a2a_server import build_agent_card, register_a2a_routes
from protocols.mcp_server import build_mcp_http_app, build_mcp_server, transport_security
from protocols.service import StorageIntelligenceService
from storage_intelligence import IntelligenceEngine, generate_accounts


def _service() -> StorageIntelligenceService:
    return StorageIntelligenceService(IntelligenceEngine(generate_accounts(50)))


def test_protocol_service_preserves_engine_contract():
    result = _service().investigate(
        "Which accounts grew abnormally last week?",
        {"environment": "Prod"},
    )

    assert result["tool"] == "capacity.growth_anomalies"
    assert result["scope"]["filters"] == {"environment": "Prod"}
    assert result["assumptions"]
    assert result["confidence"]["level"] in {"low", "medium", "high"}


def test_mcp_server_builds_http_transport(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "agent.example.com,testserver")
    server = build_mcp_server(IntelligenceEngine(generate_accounts(10)))
    app = build_mcp_http_app(server)

    assert app is not None
    assert transport_security().allowed_hosts == ["agent.example.com", "testserver"]


def test_a2a_card_and_routes_advertise_v1_interfaces():
    service = _service()
    app = FastAPI()
    card = register_a2a_routes(app, service, "https://agent.example.com")

    assert build_agent_card("https://agent.example.com").name == "Storage Intelligence Agent"
    assert {interface.protocol_version for interface in card.supported_interfaces} == {"1.0"}
    paths = {route.path for route in app.routes}
    assert "/.well-known/agent-card.json" in paths
    assert "/a2a" in paths


def test_integrated_mcp_and_a2a_wire_endpoints(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "true")
    from web.app import app

    mcp_headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    a2a_request = {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "SendMessage",
        "params": {
            "message": {
                "messageId": "message-1",
                "role": "ROLE_USER",
                "parts": [{"text": "Which accounts grew abnormally last week?"}],
                "metadata": {"filters": {"environment": "Prod"}},
            }
        },
    }
    with TestClient(app) as client:
        initialized = client.post(
            "/mcp",
            headers=mcp_headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            },
        )
        tools = client.post(
            "/mcp",
            headers=mcp_headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        a2a = client.post("/a2a", headers={"A2A-Version": "1.0"}, json=a2a_request)

    assert initialized.status_code == 200
    assert tools.status_code == 200
    assert "investigate_storage" in tools.text
    assert "summarize_storage_portfolio" in tools.text
    assert a2a.status_code == 200
    assert a2a.json()["result"]["task"]["status"]["state"] == "TASK_STATE_COMPLETED"
