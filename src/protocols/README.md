# MCP and A2A protocol adapters

This directory exposes the shared `StorageIntelligenceService` through MCP and
A2A without duplicating analytics logic.

## Endpoints

The deployed base URL is:

`https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io`

| Implementation | Endpoint | Purpose |
|---|---|---|
| `mcp_server.py` | `/mcp/` | Stateless MCP Streamable HTTP transport |
| `mcp_server.py` | stdio entry point | Local MCP process integration |
| `a2a_server.py` | `/.well-known/agent-card.json` | A2A capability discovery |
| `a2a_server.py` | `/a2a` | A2A v1 JSON-RPC |
| `a2a_server.py` | `/a2a/rest` | A2A v1 HTTP+JSON |

The fully qualified MCP URL is
`https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io/mcp/`.
Use the trailing slash to avoid an HTTP redirect at the FastAPI mount boundary.

## Authentication

Azure Container Apps Easy Auth protects public protocol calls. Acquire a
Microsoft Entra access token for `api://<WEB_AUTH_CLIENT_ID>` and send:

```http
Authorization: Bearer <access-token>
```

`AUTH_DISABLED=true` is only for local development.

## MCP usage

Configure an MCP client with the Streamable HTTP URL and bearer header:

```json
{
  "mcpServers": {
    "storage-intelligence": {
      "type": "http",
      "url": "https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io/mcp/",
      "headers": {
        "Authorization": "Bearer <access-token>"
      }
    }
  }
}
```

After `initialize`, call `tools/list`, then invoke `investigate_storage` or
`summarize_storage_portfolio`. The server also publishes the
`storage-intelligence://capabilities` resource and `storage_investigation` prompt.

For local stdio use:

```powershell
.\.venv\Scripts\storage-intelligence-mcp.exe
```

## A2A usage

Fetch the Agent Card first, then send `SendMessage` to `/a2a` with
`A2A-Version: 1.0`. The user question belongs in a text part; optional storage
scope belongs in `message.metadata.filters`.

```json
{
  "jsonrpc": "2.0",
  "id": "request-1",
  "method": "SendMessage",
  "params": {
    "message": {
      "messageId": "message-1",
      "role": "ROLE_USER",
      "parts": [
        {
          "text": "Which accounts grew abnormally last week?"
        }
      ],
      "metadata": {
        "filters": {
          "environment": "Prod"
        }
      }
    }
  }
}
```

The response task progresses through submitted, working, and completed or failed
states and includes a `storage-intelligence-result` artifact. Cancellation is
supported. Task state is process-local, so the deployment remains at one web
replica until the A2A task store is made durable.

See [`../../docs/PROTOCOL_INTEGRATION.md`](../../docs/PROTOCOL_INTEGRATION.md)
for complete request examples and runtime configuration.
