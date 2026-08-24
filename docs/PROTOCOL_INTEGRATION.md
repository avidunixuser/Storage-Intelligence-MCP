# MCP and A2A integration

The web container exposes the same read-only Storage Atlas agent through
three interfaces:

| Interface | Endpoint | Best for |
|---|---|---|
| REST API | `/api/query` | Existing application and direct HTTP integrations |
| MCP Streamable HTTP | `/mcp/` | AI hosts that discover and call tools |
| A2A JSON-RPC | `/a2a` | Agents that exchange messages and track tasks |
| A2A HTTP+JSON | `/a2a/rest` | REST-oriented A2A clients |
| A2A Agent Card | `/.well-known/agent-card.json` | Agent discovery |

Every interface delegates to `StorageIntelligenceService` and
`IntelligenceEngine`. Results therefore have the same scope, evidence, assumptions,
confidence, and read-only guarantees.

## Deployed endpoints

The current Sweden Central deployment is hosted at:

`https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io`

| Interface | Fully qualified endpoint |
|---|---|
| MCP Streamable HTTP | `https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io/mcp/` |
| A2A Agent Card | `https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io/.well-known/agent-card.json` |
| A2A JSON-RPC | `https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io/a2a` |
| A2A HTTP+JSON | `https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io/a2a/rest` |

For another environment, replace the base URL and keep the same paths. MCP clients
should use the canonical trailing-slash URL `/mcp/`; `/mcp` redirects to it.

## Authentication

Azure Container Apps Easy Auth protects every public endpoint. External callers
must acquire a Microsoft Entra access token for the web application's
`api://<WEB_AUTH_CLIENT_ID>` audience and send:

```http
Authorization: Bearer <access-token>
```

For local development only, set `AUTH_DISABLED=true`. Do not use this setting in
Azure or any shared environment.

## MCP

The server uses the official Python MCP SDK and stateless Streamable HTTP, which
supports horizontal Container Apps replicas. It publishes:

- Tool `investigate_storage(question, filters?)`
- Tool `summarize_storage_portfolio(filters?)`
- Resource `storage-intelligence://capabilities`
- Prompt `storage_investigation(question, scope?)`

Example client configuration:

```json
{
  "mcpServers": {
    "storage-intelligence": {
      "type": "http",
      "url": "https://<container-app-host>/mcp/",
      "headers": {
        "Authorization": "Bearer ${STORAGE_INTELLIGENCE_TOKEN}"
      }
    }
  }
}
```

An MCP client first sends `initialize`, then `tools/list` or `resources/list`, and
finally `tools/call`. A representative tool call is:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "investigate_storage",
    "arguments": {
      "question": "Which publicly accessible accounts have no private endpoint?",
      "filters": {
        "environment": "Prod"
      }
    }
  }
}
```

For local stdio integrations:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\storage-intelligence-mcp.exe
```

## A2A

Discover the agent before sending work:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://<container-app-host>/.well-known/agent-card.json
```

The card advertises protocol v1.0 JSON-RPC and HTTP+JSON interfaces. A JSON-RPC
message uses the question as its text part. Optional storage filters belong in
message metadata under `filters`:

```bash
curl https://<container-app-host>/a2a \
  -H "Authorization: Bearer $TOKEN" \
  -H "A2A-Version: 1.0" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "request-1",
    "method": "SendMessage",
    "params": {
      "message": {
        "messageId": "message-1",
        "role": "ROLE_USER",
        "parts": [{"text": "Which accounts grew abnormally last week?"}],
        "metadata": {
          "filters": {"environment": "Prod"}
        }
      }
    }
  }'
```

The executor emits submitted and working task states, a
`storage-intelligence-result` artifact containing both text and structured JSON,
and a completed state. Invalid questions or filters produce a failed task rather
than a success-shaped fallback. A2A task cancellation is supported; push
notifications are intentionally not advertised. The supplied deployment uses one
Container Apps replica because the A2A SDK's active-task and cancellation registry
is process-local. Replace the task handler with shared durable state before scaling
the combined web/protocol workload beyond one replica.

## Runtime configuration

| Variable | Purpose | Local default |
|---|---|---|
| `A2A_PUBLIC_URL` | Absolute base URL written into the Agent Card | `http://localhost:8000` |
| `MCP_ALLOWED_HOSTS` | Comma-separated Host allowlist for DNS-rebinding protection | localhost and test hosts |
| `MCP_ALLOWED_ORIGINS` | Comma-separated Origin allowlist | localhost origins |
| `MCP_TRANSPORT` | Standalone MCP transport | `stdio` |

Azure Bicep sets the public A2A URL and exact MCP Host/Origin allowlists from the
Container App FQDN.
