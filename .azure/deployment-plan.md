# Azure Deployment Plan

> **Status:** Deployed

Generated: 2026-08-11

---

## 1. Project Overview

**Product:** Storage Intelligence Agent

**Goal:** Build and deploy a production-like stakeholder pilot for StorageOps, FinOps, DataOps, and Databricks optimization. The design scales to 2,000+ Azure Storage Accounts while the pilot uses realistic synthetic data and disabled-by-default production connectors.

**Path:** New Project

**Repository:** `https://github.com/avidunixuser/storage-intelligence-agent` (private)

---

## 2. Quick Product Spec

### Users

- Cloud platform and storage operations teams
- FinOps practitioners and subscription owners
- Data engineering and Databricks platform teams
- Business-unit technology and finance leaders

### Core experience

1. **Estate overview:** Capacity, monthly cost, tier mix, growth, forecast, freshness, risk,
   and savings opportunity across synthetic tenants, management groups,
   subsidiaries/business units, 339 subscriptions, Dev/QA/Perf/Prod environments, regions,
   and accounts.
   A persistent top-right English/Spanish switch localizes all application views and
   accessibility text for global PepsiCo teams without changing data identifiers.
2. **Natural-language investigations:** Ask operational and financial questions and receive
   concise answers backed by deterministic tools, cited records, formulas, data timestamps,
   and confidence. The UI includes a broad creative catalog and lets authenticated users
   save a new question into private Cosmos DB as a future reusable option.
3. **Account drilldown:** Explain growth, cost changes, transaction patterns, tier
   distribution, lifecycle-policy gaps, Databricks relationships, forecasted capacity,
   access/network posture, resilience, and project governance.
4. **Savings simulator:** Model Cool, Cold, and Archive movement while accounting for access frequency, retrieval, transactions, early-deletion windows, and rehydration risk.
5. **Findings inbox:** Prioritized anomalies, risks, stale inventory, connector failures, and recommended actions with status and owner.
   Five actionable summary tiles filter the scrollable inbox; duplicate category buttons
   are not rendered.
6. **Forecasting:** 30/90/180-day capacity and budget forecasts with confidence ranges and threshold dates.
7. **Data quality:** Connector health, report age, missing tags, incomplete inventory, and unsupported-account visibility.
8. **Pilot onboarding:** PepsiCo-branded manual account entry plus atomic XLSX/CSV
   imports using tenant ID, management group, subscription, environment,
   subsidiary/business unit, region, and tier selection values. These
   features update only the pilot inventory and never provision Azure resources.
9. **Selection catalogs:** Authenticated users can add tenant IDs, management groups,
   subscriptions, subsidiaries/business units, and tracked regions. Region selectors expose every customer-facing Azure public cloud
   physical region while excluding sovereign and internal STG/EUAP locations.
10. **Admin discovery:** Users with the `StorageIntelligence.Admin` role can run
    tenant-wide read-only Azure CLI discovery across every authorized management group
    and subscription. Tenant ID, management-group membership/tags, subsidiary/business
    unit, environment, region, access tier, and SKU refresh the pilot idempotently.
11. **Scheduled discovery:** A six-hour cron configuration runs the bounded CLI command
    and atomically writes a JSON inventory snapshot without requesting keys or mutating
    Azure resources. In-app manual and scheduled pulls also upsert account details into a
    private Cosmos DB container through the web managed identity.
12. **Configurable scheduling:** Administrators can edit and persist a validated
    five-field cron expression, see the next scheduled tenant-wide discovery run, and
    inspect Cosmos DB persistence status/upsert counts.
13. **Platform highlights:** Databricks-, Fabric Lakehouse-, SAP-, Azure Data Factory-,
    SFTP-, and Application Insights-linked storage accounts display small accessible marks
    and relationship names. Links are deterministically randomized in the synthetic estate.
14. **Risk concentration:** List Growth, Cost, Freshness, Operations, Databricks,
    Configuration, Security, and Governance risk types, identify each account's dominant
    risk, and use a calm, consistent light-theme palette in a donut-style pie chart with
    counts and percentages.
    Include every scoped account with score 20 or higher in a vertically scrollable ranked
    list below the chart. Hovering a segment reveals its risk description/count/percentage,
    and keyboard focus exposes equivalent accessible details.
15. **Priority findings guidance:** Explain that Operations is the 0–100
    throttling/request-latency subscore and that the far-right value is the weighted
    overall risk score out of 100.
16. **Functional navigation:** Implement separate responsive views for Agent
    Investigation, Savings Simulator, Findings, and Data Health. Each view uses a
    deterministic authenticated API contract and the common portfolio filters.
17. **Connector controls:** Data Health allows administrators to enable and run each
    connector in explicitly labeled pilot-fixture mode, showing synced/eligible record
    counts and last-run timestamps.
18. **Footer attribution:** Display the PepsiCo copyright message and compact Microsoft
    and Azure marks at the bottom-left of desktop navigation.

### Agent query catalog

The pilot will support the supplied questions plus:

- Which accounts grew abnormally last week?
- Which Storage Accounts should I worry about, and why?
- Which accounts are negatively impacting Databricks?
- How much can we save by tiering cold data?
- Why did storage costs increase 22% last month?
- What should move to Cool, Cold, or Archive?
- Where are we wasting money?
- When will we need more capacity?
- Which business unit drives growth?
- Which subscriptions are outliers?
- Which accounts will cross a capacity or budget threshold first?
- Which lifecycle policies are missing, ineffective, or overly aggressive?
- Where would Archive create high rehydration or early-deletion risk?
- Which accounts have high transaction cost relative to stored TB?
- Which containers show small-file patterns that hurt Databricks?
- Which Databricks workspaces or external locations drive the most storage IO and cost?
- Which accounts have stale or missing inventory reports?
- Which accounts have versioning, snapshots, or soft-delete retention driving avoidable growth?
- Which replication choices appear over-provisioned relative to business criticality?
- What changed since the previous weekly review?
- What are the top five actions by savings, risk reduction, and implementation effort?
- Show a what-if comparison for 10%, 25%, and 50% tiering adoption.
- Which findings are based on incomplete data and should not be acted on yet?

### Safety and trust

- The agent is read-only; it never changes tiers, lifecycle policies, or Azure resources.
- Every answer includes scope, “data as of” time, evidence links/IDs, assumptions, and confidence.
- Numerical answers come from deterministic analytics tools, not model arithmetic.
- Missing/stale data is explicit; the system does not create success-shaped fallbacks.
- Cost recommendations include retrieval and early-deletion caveats.
- Prompt input cannot execute arbitrary SQL/KQL or access resources outside the user’s authorized scope.

### Out of scope for the pilot

Automatic remediation, Power BI, Teams, Microsoft 365 Copilot, production SLA/DR, and
direct changes to lifecycle policies. The pilot models multi-tenant and management-group
scope; real collection remains limited to tenants and management groups where the managed
identity has explicit read-only RBAC.

---

## 3. Requirements

| Attribute | Value |
|-----------|-------|
| Classification | Production-like stakeholder pilot |
| Scale | Production design for 2,000+ accounts; synthetic pilot dataset |
| Tenant topology | Three synthetic PepsiCo tenants, four management groups, five subsidiaries/business units, and 339 mapped subscriptions across Dev/QA/Perf/Prod |
| Budget | Cost-optimized where compatible with end-to-end private Foundry |
| Subscription | `ME-MngEnvMCAP585394-nrp-at-microsoft-dot-com` (`c82406dd-f84c-42df-9586-c6f02abda6df`) |
| Tenant | `da5fd6a4-899f-4b53-b4e9-7e3e5a8a58b6` |
| Location | Sweden Central |
| Residency | European Union |
| Network | New standalone VNet, Azure Private DNS, private data plane |
| Authentication | Microsoft Entra ID and managed identities only |
| Interaction | Web dashboard and natural-language chat |

### Subscription readiness

- Deploying user has `Owner` and inherited `User Access Administrator`.
- Deploying user has `Foundry User`; execution will add/verify `Foundry Account Owner` before Foundry provisioning.
- Active policies target open-source relational databases and SQL Servers on machines; neither blocks the selected architecture.
- No blocking region, SKU, tag, or public-network policy assignment was detected.

---

## 4. Data and Analytics Design

### Production connector interfaces

| Source | Connector behavior |
|--------|--------------------|
| Azure Resource Graph | Discovers accounts and captures subscription, region, SKU, redundancy, SAS/shared-key, public/private endpoint, NSG/ASG, service-principal, project, business-unit, last-accessed, defunct, networking, and lifecycle configuration snapshots |
| Blob Inventory | Reads the latest Parquet manifest/report from each reachable source account using managed identity and bounded fan-out |
| Azure Monitor Metrics | Uses batched metrics queries for capacity, transactions, ingress, egress, availability, throttling, and latency |
| Cost Management | Ingests scheduled management-group/subscription cost exports delivered to central ADLS Gen2 |
| Databricks telemetry | Ingests exported system-table data for storage paths, jobs, workspaces, external locations, IO, scan volume, and query/job attribution |

Connectors are disabled in the pilot environment. Their contracts, authorization checks,
retry/idempotency behavior, and fixtures are implemented and tested. A synthetic connector
seeds 2,500 accounts across tenants, management groups, subsidiaries/business units,
339 subscriptions, Dev/QA/Perf/Prod environments, regions, tiers, and platform relationships.

### Lake layout

| Zone | Purpose |
|------|---------|
| `raw/` | Immutable source snapshots and manifests, partitioned by source/date/subscription/account |
| `normalized/` | Schema-normalized Parquet with quality flags and lineage |
| `curated/` | Daily account/container/tier/cost/Databricks aggregates |
| `findings/` | Anomalies, forecasts, recommendations, evidence, and evaluation datasets |

### Analytics

- Growth anomalies: seasonal comparison plus robust median-absolute-deviation scoring.
- Cost change explanation: capacity, tier mix, operations, retrieval, egress, redundancy, and price decomposition.
- Tier recommendations: last-access distributions and scenario pricing with minimum-retention/rehydration guards.
- Databricks impact: external-location mapping, IO concentration, request latency/throttling, egress, and small-file indicators.
- Forecasting: robust trend and exponential-smoothing candidates selected by backtesting; confidence intervals are retained.
- Risk score: transparent weighted dimensions for growth, cost, capacity runway, data freshness, throttling, concentration, and Databricks impact.

Gold aggregates, finding state, chat authorization metadata, and evidence pointers are stored in Cosmos DB. Detailed inventory remains in ADLS Gen2.

---

## 5. Agent Design

The pilot uses one Microsoft Foundry orchestration agent with deterministic domain tools rather than five independent LLM agents. This lowers cost and latency, avoids conflicting answers, and preserves an easy path to future specialist agents.

### Tool families

| Tool family | Responsibilities |
|-------------|------------------|
| Capacity | Growth outliers, tier mix, capacity runway, forecasts |
| Cost | Cost decomposition, savings simulation, waste ranking |
| Databricks | Workspace/external-location impact and IO optimization |
| Risk | Composite growth/cost/operations plus Security, Governance, resilience, stale data, and lifecycle/configuration concerns |
| Portfolio | Tenant, management-group, subsidiary/business-unit, subscription, environment, region, and estate comparisons |

Tools are exposed as private Azure Functions/OpenAPI operations with strict schemas. They return structured values and evidence; GPT-5.4-mini summarizes and guides follow-up questions.

### Model

| Attribute | Selection |
|-----------|-----------|
| Model | `gpt-5.4-mini` |
| Version | `2026-03-17` |
| SKU | `DataZoneStandard` |
| Initial capacity | 10K TPM |
| Sweden Central subscription quota | 1,000K TPM available |
| Subscription quota available | 1,000K TPM |

---

## 6. Application Stack

| Component | Technology | Path |
|-----------|------------|------|
| Web UI | React with pinned, vendored browser assets; no npm/Node build | `src/web/static` |
| Web API | Python 3.13, FastAPI, Pydantic | `src/web` |
| Collection/orchestration | Python Azure Functions Flex Consumption + Durable Functions | `src/functions` |
| Durable backend | Durable Task Scheduler Consumption + private endpoint | Azure managed |
| Agent | Microsoft Foundry Standard Agent Service, prompt agent + private OpenAPI/Functions tools | `src/agent` |
| Analytics | Python, Polars/PyArrow, statsmodels/scikit-learn where justified | `src/analytics` |
| Primary data | ADLS Gen2 Parquet + Cosmos DB gold/findings | Azure managed |
| Observability | OpenTelemetry, Application Insights, Log Analytics | Shared |
| IaC/deployment | Azure Developer CLI + Bicep | `azure.yaml`, `infra/` |

---

## 7. Azure Architecture

### Selected implementation path

**AZD with Bicep**, adapting official Microsoft templates:

1. Foundry sample **19 – Private Network Standard Agent Setup with Tools behind VNet** for end-to-end private Agent Service, BYO Storage/Cosmos/Search, VNet injection, private Functions/OpenAPI tools, DNS, and capability hosts.
2. Official Python Functions Flex Consumption AZD base plus the Durable recipe and Durable Task Scheduler.
3. Container Apps for the FastAPI/React web application.

No infrastructure will be synthesized from memory where an official module/template exists.

### Service mapping

| Component | Azure service | SKU/configuration |
|-----------|---------------|-------------------|
| Web app | Azure Container Apps | Consumption profile, 1 vCPU/2 GiB, external HTTPS ingress on target port 8000, Entra auth, fixed 1 replica while A2A task state is process-local |
| Image registry | Azure Container Registry | Premium, admin disabled, private endpoint |
| Collection and tools | Azure Functions | Flex Consumption FC1, Python 3.13, VNet integration, 0 always-ready instances |
| Orchestration state | Durable Task Scheduler | Consumption, private endpoint, managed-identity auth |
| Central lake | Storage account / ADLS Gen2 | Standard ZRS, HNS, shared keys disabled, blob+dfs private endpoints |
| Function deployment storage | Storage account | Standard LRS, shared keys disabled, private endpoint |
| Foundry agent state | Storage account | Official template default, shared keys disabled, private endpoint |
| Gold/findings and agent state | Cosmos DB for NoSQL | Single-region, lowest template-supported throughput, local auth disabled, private endpoint |
| Agent vector/thread support | Azure AI Search | Standard, 1 replica × 1 partition, private endpoint |
| Foundry | Microsoft Foundry account + project | Standard private setup, public network disabled |
| Model | Foundry model deployment | GPT-5.4-mini DataZoneStandard, 10K TPM |
| Secrets/config | Azure Key Vault | Standard, RBAC authorization, private endpoint |
| Network | Azure VNet | Dedicated agent, private endpoint, tools/Functions, and Container Apps subnets |
| Monitoring | Log Analytics + Application Insights | Pay-as-you-go, 30-day retention, sampling enabled |

### Access model

- The web endpoint is internet-reachable but requires Entra authentication.
- Foundry, storage, Cosmos DB, Search, Key Vault, ACR, Functions tools, and Durable Task Scheduler use private connectivity.
- Managed identities and least-privilege RBAC replace account keys and connection secrets.
- Production connectors require Resource Graph Reader, Monitoring Reader, Cost Management Reader/export access, and scoped Storage Blob Data Reader. The pilot does not grant estate-wide roles.
- Network-isolated source estates can use a future federated collector per connectivity zone; the central pull connector handles reachable accounts.

---

## 8. Provisioning Limit Checklist

Azure quota CLI was attempted first per provider. When a provider returned `BadRequest` or no quota records, current usage came from Azure Resource Graph and limits came from current Microsoft service-limit documentation.

| Resource / quota | Deploy | Total after deployment | Limit | Evidence |
|------------------|-------:|-----------------------:|------:|----------|
| Container Apps managed environments | 1 | 4 | 50 | Quota CLI `ManagedEnvironmentCount`; current 3 |
| Storage accounts in Sweden Central | 3 | 3 | 250 | Region/provider support confirmed |
| Virtual networks | 1 | 2 | 1,000 | Quota CLI; current 1 |
| Private endpoints | 12 | 14 | 65,536 | Quota CLI; current 2 |
| Azure Functions Flex Consumption apps | 1 | 1 | 1,000 max scale-out instances per app | Sweden Central availability confirmed |
| Durable Task schedulers | 1 | 1 | Service-managed; no published scheduler-count quota | Sweden Central provider support confirmed |
| Cosmos DB accounts | 1 | 3 | 250 default per subscription | Resource Graph current 2; official Cosmos limit |
| Azure AI Search Standard services | 1 | 1 | 16 per subscription per region | Sweden Central provider support confirmed |
| Foundry/AIServices accounts | 1 | 1 | 30 S0 accounts | Cognitive Services usage `OpenAI.S0.AccountCount`; current 0 |
| GPT-5.4-mini DataZoneStandard | 10K TPM | 10K TPM | 1,000K TPM | Model-capacity API and Cognitive Services usage; current 0 |
| Container registries | 1 | 3 | 100 per subscription | Resource Graph current 2; official ACR limit |
| Key vaults | 1 | 3 | 5,000 per subscription | Resource Graph current 2; official Key Vault limit |
| Log Analytics workspaces | 1 | 3 | 1,000 per subscription | Resource Graph current 2; official Azure Monitor limit |
| Application Insights components | 1 | 1 in new resource group | 100 per resource group | Resource Graph current 2 elsewhere; official Azure Monitor limit |

**Status:** All planned resources and model capacity are within available limits.

---

## 9. Cost Controls

- One warm Container Apps replica preserves process-local A2A task and cancellation state; Flex Consumption Functions still scale to zero.
- Consumption Durable Task Scheduler.
- One small DataZoneStandard model deployment with strict token/output limits.
- Standard AI Search at one search unit; selected after repeated Sweden Central Basic
  capacity exhaustion. This is the largest fixed-cost pilot resource.
- Partition pruning and precomputed gold aggregates to avoid scanning raw inventory during chat.
- Daily ingestion with bounded concurrency and incremental watermarks.
- Log sampling, 30-day retention, and redaction.
- Synthetic pilot data prevents estate-wide Azure Monitor, Storage, Cost Management, and Databricks query charges.

---

## 10. Verification and Acceptance

- Synthetic dataset represents at least 2,500 accounts and produces deterministic expected findings.
- All supplied questions and at least ten additional query-catalog questions return scoped, cited answers.
- Saved questions survive future sessions, reject normalized duplicates, and never execute
  as part of the save operation.
- Every UI view displays and filters by tenant ID, management group,
  subsidiary/business unit, all 339 subscriptions, environment, region, and tier.
- English and Spanish rendering covers all six views, controls, statuses, dynamic counts,
  risk/evidence phrases, and built-in questions; locale preference persists in the browser.
- Savings simulation reconciles against fixture calculations.
- Re-running ingestion is idempotent and does not duplicate records/findings.
- Connector failures and stale data are visible.
- Security factors are deterministic and evidence-backed for SAS/shared keys, public
  access, private endpoint gaps, non-GRS/GZRS replication, NSG/ASG links, missing
  service-principal access, and project-governance tags.
- The eleven Data Health posture/quality tiles, including Stale accounts, Missing
  lifecycle, SFTP Enabled, and AppInsights Data, are
  actionable; each returns every matching account in
  the active scope through an allowlisted API and displays the risk-sorted result directly
  below in a scrollable panel.
- The seven Data Health source cards appear first after filters/reset; the redundant
  standalone stale-account details panel is removed.
- In Data Health, an administrator can click **Disabled** to transition a connector to
  **Enabled**, reveal **Run**, and observe **Healthy** plus last-run data after completion.
- Unauthenticated requests receive 401/redirect; tenant and authorization boundaries are enforced.
- Public network access is disabled for all data-plane services and Foundry.
- Health/readiness endpoints verify dependencies without exposing secrets.
- Manual onboarding refreshes portfolio metrics and rejects duplicate account names.
- XLSX/CSV onboarding validates all required fields and imports atomically without
  partial writes or Azure resource mutations.
- Tenant/management-group/subscription/environment/subsidiary/region catalog additions refresh all dependent selectors;
  region dropdowns include the complete supported Azure public-region list.
- Admin discovery is role-gated, read-only, idempotent, and rejects inaccessible tenants;
  scheduled discovery uses the documented cron expression and atomic output file.
- Admin cron updates persist atomically and schedule only one discovery at a time.
- Synthetic hierarchy fixtures remain deterministic and preserve
  `business_unit == subsidiary`; Cosmos documents and evidence retain the complete
  hierarchy.
- Databricks, Fabric Lakehouse, SAP, Azure Data Factory, SFTP, and Application Insights
  relationships render the correct compact marks.
- Risk concentration renders all eight risk types in an eye-friendly pie chart with
  matching counts and percentages.
- Pie-segment hover and keyboard focus display the corresponding risk description.
- Priority findings labels Growth/Operations components and overall `/100` scores.
- Agent Investigation keeps scoped tool results and an eight-item session history.
- Savings Simulator supports 1–100% adoption plus 10/25/50% comparisons and ranked candidates.
- Findings combines and filters risks, anomalies, freshness issues, and savings actions by severity.
- Data Health reports connector/source state, freshness, quality gaps, and stale-account actions.
- Admins can enable/run Data Health connectors; record counts distinguish synced from eligible.
- Navigation shows PepsiCo copyright and accessible Microsoft/Azure marks at bottom-left.
- Risk concentration returns and displays every account meeting the score-20 at-risk
  threshold; the chart remains usable through a vertical scrollbar.
- Container App resources use the supported 1 vCPU/2 GiB Consumption pairing with one
  warm replica while A2A task state remains process-local; application version remains `0.1.0`.
- Web startup is independent from private Function deployment and Foundry smoke tests;
  ingress, probes, Docker, and Uvicorn consistently use port `8000`.
- Container probes use a 10-second timeout to avoid intermittent one-second timeout failures.
- Unit, API, analytics, agent-tool contract, browser smoke, Bicep lint/build, what-if, and live smoke checks pass.

---

## 11. Execution Checklist

### Planning

- [x] Analyze workspace and choose New Project
- [x] Gather requirements and confirm architecture intake
- [x] Confirm subscription, tenant, location, and permissions
- [x] Inspect policies
- [x] Select official Foundry/private-network and Functions templates
- [x] Validate service quotas and model capacity
- [x] Finalize product spec, stack, architecture, and acceptance criteria
- [x] User approved this plan

### Build and preparation

- [x] Scaffold from official templates and compose approved modules
- [x] Build synthetic data generator and connector contracts
- [x] Implement analytics, tools, agent, API, and React UI
- [x] Add documentation, threat boundaries, and phase-2 Teams/Copilot design
- [x] Verify locally: 28 tests, browser smoke, SDK imports, and Bicep build
- [x] Set plan status to `Ready for Validation`

### Validation and deployment

- [x] Re-run `azure-validate` for Sweden Central
- [x] Resolve all validation failures and record evidence
- [x] Set status to `Validated`
- [x] Invoke `azure-deploy`
- [x] Verify network isolation, RBAC, live UI, Function health, MCP, and A2A
- [x] Set status to `Deployed`

---

## 12. Files to Generate

| File/path | Purpose | Status |
|-----------|---------|--------|
| `.azure/deployment-plan.md` | Source-of-truth plan | Complete |
| `docs/PRODUCT_SPEC.md` | Quick feature, query, UX, and stack specification | Complete |
| `docs/ARCHITECTURE.md` | Data flow, connectors, security, scale, and phase 2 | Complete |
| `src/web/` | FastAPI and no-npm React UI | Complete |
| `src/function_app.py` | Durable collection and private analytic tools | Complete |
| `src/storage_intelligence/` | Deterministic analytics and forecasting | Complete |
| `src/agent/` | Foundry agent instructions, tools, and evals | Complete |
| `infra/` | Composed official Bicep modules | Complete |
| `azure.yaml` | AZD configuration | Complete |
| `README.md` | Local, validation, deployment, and operations guide | Complete |

---

## 13. Next Step

> Current: Deployment completed in `rg-storage-intel-mcpa2a`.

The Entra-protected web application, private Function tools, MCP server, and A2A
interfaces are deployed and healthy in Sweden Central.

---

## 14. Validation Proof

### Validation checks

- [x] AZD installation and schema/configuration
- [x] AZD environment, authentication, subscription, and location
- [x] Bicep compilation and lint
- [x] Subscription deployment validation and what-if (`azd provision --preview`)
- [x] Python 3.13 build and 2,500-account acceptance suite
- [x] Function package validation
- [x] Docker build-context review (no Node/npm step)
- [x] Azure Policy review
- [x] Static managed-identity and RBAC role verification

### Commands and results

- 2026-08-20 `az login --use-device-code` -> authenticated to tenant
  `MngEnvMCAP585394` and subscription `c82406dd-f84c-42df-9586-c6f02abda6df`.
- 2026-08-20 `azd env new mcpa2a --no-prompt` and `azd env set` -> configured
  the new `mcpa2a` environment for Sweden Central; target resource group
  `rg-storage-intel-mcpa2a` did not exist.
- 2026-08-20 `az bicep build --file infra/main.bicep --stdout` -> passed.
- 2026-08-20 `.venv/Scripts/python -m pytest` -> 85 passed.
- 2026-08-20 `azd provision --preview --no-prompt` -> passed in 1 minute
  25 seconds and confirmed a create-only plan for the new resource group and
  31 workload resources.
- 2026-08-20 `azd provision --no-prompt` -> provisioned
  `rg-storage-intel-mcpa2a` in Sweden Central.
- 2026-08-20 private Function publication -> HTTP 202; deployment completed and
  `/api/healthz` returned HTTP 200.
- 2026-08-20 live protocol checks -> web `/healthz` and Agent Card returned HTTP
  200; MCP `initialize` and `tools/list` returned HTTP 200 with both registered
  tools; A2A `SendMessage` completed with `TASK_STATE_COMPLETED`.
- 2026-08-20 unauthenticated public app request -> HTTP 302 to the tenant's
  Microsoft Entra sign-in endpoint.
- 2026-08-20 security verification -> ACR public access remained disabled with
  firewall default `Deny`; Container App revision `0000006` was healthy.
- `azd version` -> 1.30.0.
- `azd auth login --check-status` -> authenticated as `admin@MngEnvMCAP585394.onmicrosoft.com`.
- `azd env get-values` -> `storage-intel-pilot`, target subscription/tenant, `eastus2`, and both Entra app IDs present.
- `az bicep lint --file infra/main.bicep` -> passed.
- `azd provision --preview --no-prompt` -> passed in 52 seconds; validated 31 planned Azure resources with no deletes.
- Initial preview caught and resolved an overlength generated storage-account name before deployment.
- `.venv/Scripts/python -m pytest` -> 28 passed, including the complete query catalog and 2,500-account fingerprint.
- Browser smoke -> dashboard rendered 2,500 accounts and returned cited tier-savings output with scope/data-as-of/confidence.
- `azd package --no-prompt` -> Function deployment package created successfully.
- Docker context -> no Node/npm instruction or dependency; deployment intentionally uses ACR remote build because Docker is unavailable locally.
- `az policy assignment list --disable-scope-strict-match` -> assignments reviewed; live what-if reported no policy denial.
- Reliable public UI fix: Bicep lint, 40 tests, and live `azd provision --preview`
  passed for the 2 vCPU/4 GiB Consumption pairing, `minReplicas: 1`, port `8000`,
  and startup dependency decoupling.
- Three-replica reliability update: Bicep lint, 40 tests, and live
  `azd provision --preview` passed for fixed 3/3 scaling, 1 vCPU/2 GiB per replica,
  and 10-second startup/liveness/readiness probe timeouts.
- Cosmos inventory persistence update (2026-08-12): `az bicep build --file
  infra/main.bicep --stdout`, 42 acceptance tests, Python/JavaScript syntax checks, and
  `azd provision --preview --no-prompt` against `storage-intel-se` passed. Static RBAC
  review confirms the web UAMI receives Cosmos DB Built-in Data Contributor scoped only
  to `/dbs/storage-intelligence`; local auth and public Cosmos access remain disabled.
- Live Cosmos verification (2026-08-12): provisioned the 400 RU/s
  `storage-intelligence/storage-accounts` store with `/subscription_id` partitioning,
  confirmed the web UAMI's database-scoped data role, deployed revision `0000007`, and
  completed a managed-identity upsert plus cross-partition count query from inside the
  private Container Apps environment (`upserted: 1`, `documents: 1`).

### Region capacity recovery

- East US 2 created the Foundry account/model and supporting Storage, Cosmos DB,
  Application Insights, and Log Analytics, then stopped before capability-host creation
  because Basic AI Search capacity was unavailable on three attempts.
- UK South exposes GPT-5.4-mini `2026-03-17` but has no DataZoneStandard quota for this
  subscription, so it does not satisfy the approved model requirement.
- Sweden Central exposes GPT-5.4-mini `2026-03-17` with 1,000K TPM of
  DataZoneStandard quota available and supports Search, Durable Task Scheduler,
  Container Apps, Flex Functions, and template 19 private Foundry.
- South Central US was explicitly excluded by the user and no Azure resources were
  provisioned there.
- A fresh AZD environment/resource group/VNet is used for Sweden Central. The partial
  East US 2 resources are intentionally retained pending separate destructive cleanup approval.
- `azd env get-values` -> `storage-intel-se`, target subscription/tenant,
  `swedencentral`, and fresh Entra app IDs present.
- Sweden Central `azd provision --preview --no-prompt` -> passed in 62 seconds;
  31 creates, no modifies or deletes.
- Sweden Central `.venv/Scripts/python -m pytest` -> 28 passed.
- Sweden Central `azd package --no-prompt` -> Function package created successfully.
- Sweden Central Search Basic provisioned successfully after a transient-capacity retry.
- Foundry account and project capability hosts reached `Succeeded`.
- The workload deployment then rejected an overlength Key Vault name and the legacy
  `FUNCTIONS_WORKER_RUNTIME` Flex setting. Both were corrected.
- Because capability-host creation had started, retry environment `storage-intel-se2`
  uses a new resource group, VNet, and agent subnet as required by template 19 guidance.
- `storage-intel-se2` validation: Bicep lint passed; provision preview passed with
  31 creates and no modifies/deletes; 28 tests passed; Function packaging passed.
- `storage-intel-se2` Basic Search provisioning failed before capability-host creation.
  The user authorized a higher Search SKU; AI Search Standard is now selected in Sweden
  Central and the same untouched agent subnet is safe to retry.
- AI Search Standard retry validation passed: Bicep lint and live provision preview
  completed successfully with no deletes.
- Full Sweden Central infrastructure provisioning succeeded. Agent creation was moved
  into the VNet-integrated web startup path with a project-scoped Foundry User assignment
  so private Foundry remains inaccessible from the deployment workstation.
- VNet agent startup update validation passed: Bicep lint, 28 tests, Function package,
  and live provision preview completed with no deletes.
- The first agent-startup update exposed subnet ownership drift: template 19's inline
  VNet definition omitted the Flex subnet and attempted to remove its service-linked
  child. The fourth subnet is now composed into the baseline itself. Because the
  capability host existed, retry environment `storage-intel-se3` uses another fresh VNet.
- Final `storage-intel-se3` validation passed: Bicep lint, 28 tests, Function package,
  and a 31-create/no-delete provision preview.
- Workstation Function publication was correctly rejected by private SCM. Function zip
  deployment now runs inside the VNet-integrated web startup with managed identity and
  resource-scoped Website Contributor.
- Private Function publisher validation passed: Bicep lint, tests, package, and live
  provision preview completed without deletes.
- Function remote build exceeded the initial liveness window. Startup liveness is now
  delayed eight minutes while readiness remains gated on authenticated Function health
  and the live agent smoke result.
- Startup tolerance update validation passed: Bicep lint, 29 tests, and live preview
  completed without deletes.

### Deployment result

- Environment: `mcpa2a`; resource group: `rg-storage-intel-mcpa2a`; region:
  Sweden Central.
- Public web endpoint:
  `https://ca-storage-intel-kxlgam3w.wittyforest-55ec85c1.swedencentral.azurecontainerapps.io`.
- Private Function endpoint:
  `https://func-storage-intel-kxlgam3w.azurewebsites.net/api`.
- Function deployment storage has Blob, Queue, and Table private endpoints and
  identity-based service URIs.
- Durable Functions uses extension bundle `[4.32.0, 5.0.0)` and the
  `azureManaged` Durable Task Scheduler provider.
- Container App revision `ca-storage-intel-kxlgam3w--0000006` and Function
  `/api/healthz` are healthy.
- ACR was restored to `publicNetworkAccess=Disabled`, firewall default `Deny`,
  and admin credentials disabled after each bounded remote-build window.

### Role Assignment Verification

- Status: Verified
- Identities checked: Function UAMI, web UAMI, and deploying user
- Roles confirmed: Function Storage Blob Data Owner, Storage Queue Data
  Contributor, and Storage Table Data Contributor on Function storage; central
  lake Storage Blob Data Contributor; Durable Task Data Contributor; Key Vault
  Secrets User; Monitoring Metrics Publisher; web AcrPull, Foundry User, and
  Function-scoped Website Contributor.
- Scope: Service roles are scoped to their individual resources. No workload identity receives subscription-wide data-plane access.
- Issues: None. The temporary diagnostic Storage Blob Data Reader assignment was
  removed from the web identity after verification.
