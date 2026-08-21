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

- Follow blue steps **1-4** for every browser, MCP, or A2A request: send the request,
  authenticate with Entra, route it through the Container App protocol handler, then run
  the shared application service and query or persist data in Cosmos DB.
- Follow purple steps **A-C** only when the application selects an agent tool: invoke the
  private Foundry agent, call the managed-authentication Function tool, then access the
  Function dependencies.
- The lower panels document security controls and workload placement. They are not
  additional request hops and intentionally have no arrows.
- The private network panel identifies all four VNet subnets, VNet-linked Private DNS,
  Private Link, and the public-network-access policy.
- The identity panel lists the actual least-privilege RBAC granted to the web and Function
  user-assigned managed identities.
- Cosmos DB contains the `storage-intelligence` application database. The
  `storage-accounts` container is partitioned by `/subscription_id`; saved questions are
  also persisted there.
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
