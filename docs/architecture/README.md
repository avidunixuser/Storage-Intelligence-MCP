# Architecture diagram assets

The architecture diagram represents the application and its deployed Sweden Central
topology from authenticated UI, MCP, and A2A clients through the shared application
service, Microsoft Foundry, private Function tools, and persistent Azure services.

| File | Purpose |
|---|---|
| [`storage-intelligence-architecture.vsdx`](storage-intelligence-architecture.vsdx) | Native, editable Microsoft Visio drawing with embedded Azure service icons |
| [`storage-intelligence-architecture.drawio`](storage-intelligence-architecture.drawio) | Cross-platform editable source for diagrams.net |
| [`storage-intelligence-architecture.svg`](storage-intelligence-architecture.svg) | Rendered source used by GitHub Markdown |

## Reading the diagram

- Blue arrows represent Entra-authenticated public HTTPS ingress.
- Green arrows represent private VNet or Private Link data-plane traffic.
- Dashed purple arrows represent managed-identity or control relationships.
- The Container App exposes the browser UI, REST API, MCP Streamable HTTP, and A2A
  endpoints through one FastAPI/Uvicorn process and one protocol-neutral service facade.
- Microsoft Foundry invokes the private Function OpenAPI tools with managed
  authentication. The Function App reaches its storage, ADLS, Key Vault, Durable Task,
  and monitoring dependencies through VNet integration and private endpoints.
- Cosmos DB contains both Foundry backing data and the `storage-intelligence` application
  database. The `storage-accounts` container is partitioned by `/subscription_id`; saved
  questions are also persisted there.
- Application Insights and Log Analytics are reached through Azure Monitor Private Link
  Scope (AMPLS).

## Regeneration

Run the generator from the repository root:

```powershell
python scripts\generate_architecture_assets.py
```

The generator downloads Microsoft's official Azure architecture SVG icon package and a
minimal Open Packaging Convention Visio template, then recreates the synchronized VSDX,
draw.io, and SVG assets from one topology model. Microsoft permits the icon set for
architecture diagrams, training, and documentation under the terms on the
[Azure Architecture Center icon page](https://learn.microsoft.com/azure/architecture/icons/).
