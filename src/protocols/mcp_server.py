from __future__ import annotations

import json
import os
from collections.abc import Iterable

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from storage_intelligence import IntelligenceEngine, generate_accounts

from .service import StorageIntelligenceService


def build_mcp_server(engine: IntelligenceEngine) -> MCPServer:
    service = StorageIntelligenceService(engine)
    server = MCPServer(
        "storage-intelligence",
        instructions=(
            "Use these read-only tools to investigate Azure Storage estates. "
            "Preserve returned scope, evidence, assumptions, and confidence."
        ),
    )

    @server.tool(
        name="investigate_storage",
        description=(
            "Answer a Storage Atlas question using deterministic analytics. "
            "Returns scope, evidence, assumptions, confidence, and structured findings."
        ),
    )
    def investigate_storage(
        question: str,
        filters: dict[str, str] | None = None,
    ) -> dict:
        return service.investigate(question, filters)

    @server.tool(
        name="summarize_storage_portfolio",
        description=(
            "Return deterministic portfolio capacity, cost, growth, savings, "
            "freshness, and risk for an optional scope."
        ),
    )
    def summarize_storage_portfolio(
        filters: dict[str, str] | None = None,
    ) -> dict:
        return service.portfolio(filters)

    @server.resource(
        "storage-intelligence://capabilities",
        name="Storage Atlas capabilities",
        mime_type="application/json",
    )
    def capabilities() -> str:
        return json.dumps(service.capabilities(), separators=(",", ":"))

    @server.prompt(
        name="storage_investigation",
        description="Build a trustworthy read-only storage investigation request.",
    )
    def storage_investigation(question: str, scope: str = "entire estate") -> str:
        return (
            f"Investigate this question for {scope}: {question}\n"
            "Use investigate_storage. Preserve every returned evidence identifier, "
            "assumption, confidence value, and per-account reason."
        )

    return server


def _items(value: str | None, defaults: Iterable[str]) -> list[str]:
    if not value:
        return list(defaults)
    return [item.strip() for item in value.split(",") if item.strip()]


def transport_security() -> TransportSecuritySettings:
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_items(
            os.getenv("MCP_ALLOWED_HOSTS"),
            ("localhost:*", "127.0.0.1:*", "testserver", "testserver:*"),
        ),
        allowed_origins=_items(
            os.getenv("MCP_ALLOWED_ORIGINS"),
            ("http://localhost:*", "http://127.0.0.1:*"),
        ),
    )


def build_mcp_http_app(server: MCPServer):
    return server.streamable_http_app(
        streamable_http_path="/",
        stateless_http=True,
        transport_security=transport_security(),
    )


def main() -> None:
    server = build_mcp_server(IntelligenceEngine(generate_accounts()))
    server.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))


if __name__ == "__main__":
    main()
