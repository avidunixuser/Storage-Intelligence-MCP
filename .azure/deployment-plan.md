# Azure Deployment Plan

> **Status:** Deployed

Generated: 2026-08-11

## Pending Change: Persist AIRGAP Spreadsheet Imports

- **Mode:** Modify the existing authenticated spreadsheet import and redeploy the existing
  Container App.
- **Goal:** Persist successfully imported AIRGAP storage-account records in the existing
  Cosmos DB storage-account inventory container using the Container App managed identity.
- **Atomicity:** Validate the complete workbook before changing the application inventory.
  Upsert validated records to Cosmos before publishing them to the in-memory inventory, and
  return an explicit server error rather than a success response when persistence fails.
  Deterministic IDs make a retry idempotent across the container's `/subscription_id`
  partitions.
- **Schema:** Extend spreadsheet parsing beyond the eight required onboarding fields so the
  optional storage-account attributes supplied by `Sample.xlsx` are type-checked, normalized,
  incorporated into each account record, and persisted with deterministic document metadata
  and spreadsheet-source provenance.
- **Persistence service:** Generalize the existing managed-identity Cosmos inventory writer so
  Azure discovery retains `azure-cli-discovery-v1` provenance while spreadsheet imports use
  `spreadsheet-pilot-v1` and an `airgap-spreadsheet` trigger.
- **API contract:** Return Cosmos persistence status, upsert count, database, and container in
  the successful import response. Keep whole-workbook validation and duplicate/conflict
  rejection ahead of any write.
- **Verification:** Add focused tests for full attribute mapping, managed-identity Cosmos
  upserts, persistence metadata, disabled local-mode behavior, and explicit persistence
  failures that do not mutate the in-memory account inventory. Run the complete existing test
  suite, JavaScript checks, Bicep build, AZD package, and deployment preview.
- **Infrastructure:** Reuse the existing Cosmos account, database, container, private endpoint,
  managed identity, and database-scoped Cosmos DB Built-in Data Contributor role; no new Azure
  resources and no subscription-wide role.
- **Azure context:** Reuse AZD environment `mcpa2a`, subscription
  `ME-MngEnvMCAP585394-nrp-at-microsoft-dot-com`
  (`c82406dd-f84c-42df-9586-c6f02abda6df`), resource group
  `rg-storage-intel-mcpa2a`, and Sweden Central after user confirmation.
- **Deployment:** AZD recipe; after implementation, hand off through `azure-validate` and
  `azure-deploy`, build a fresh ACR image in the established bounded access window, restore
  ACR to private/default-deny, deploy and verify a healthy revision with 100% traffic, then
  commit, push, create a pull request, merge it, and verify the commit on `origin/main`.
- **Preparation proof:** User approved the plan and reuse of the existing Azure context.
  The implementation preserves all 36 template attributes, derives and validates the
  `/subscription_id` Cosmos partition from supplied resource IDs, uses deterministic
  document IDs for idempotent retry, persists before in-memory publication, and reports
  persistence details in the API response. The complete 97-test suite, Python compilation,
  JavaScript syntax checks, Bicep build, `azd package --no-prompt`, and `git diff --check`
  pass. No new Azure resource or quota is required.

## Pending Change: AIRGAP Import Heading

- **Mode:** Modify the existing Overview UI and redeploy the existing Container App.
- **Requested wording:** `Import account spreadsheet` followed by
  `(for AIRGAP Accounts ONLY, if applicable)` on the same heading.
- **Presentation:** Render only the parenthetical qualifier in semantic italic text.
- **Localization:** Update the Spanish heading while preserving the same emphasis structure.
- **Security and infrastructure:** No API, authentication, RBAC, networking, workbook, data,
  or Azure infrastructure changes.
- **Deployment:** Validate the static UI, build a fresh image through the bounded ACR build
  window, restore ACR to private/default-deny, deploy a healthy revision, then commit, push,
  create a pull request, and merge it.
- **Preparation proof:** The heading uses an `<em>` qualifier, English and Spanish strings
  preserve the split emphasis, cache keys are refreshed, 93 tests pass, JavaScript syntax
  checks pass, and the unchanged Bicep deployment builds cleanly.

## Pending Change: AIRGAP Sample Spreadsheet

- **Mode:** Modify the existing Overview UI and redeploy the existing Container App.
- **Requested capability:** Place a downloadable `Sample.xlsx` link directly below the
  `Upload account spreadsheet (AIRGAP Accounts if any)` heading.
- **Workbook contract:** The workbook contains one header row with the 36 requested
  storage-account attributes, in the supplied order, and no sample account data.
- **Import compatibility:** The existing authenticated XLSX/CSV upload endpoint remains
  unchanged. The template uses normalized field names already accepted by the server.
- **UI cleanup:** Remove the legacy abbreviated column-guidance sentence from the upload tile.
- **Security and infrastructure:** No authentication, RBAC, networking, data-plane, or Azure
  infrastructure changes. The workbook is a static, non-sensitive application asset.
- **Deployment:** Build a fresh image in the existing bounded ACR build window, restore ACR
  to private/default-deny, deploy a new healthy Container App revision, then commit, push,
  create a pull request, and merge it.
- **Preparation proof:** `Sample.xlsx` contains exactly one header row with all 36 requested
  columns; the static download and completed-template upload path pass automated coverage.
  The complete suite passes with 93 tests, Python/JavaScript compilation succeeds, and the
  unchanged Bicep deployment builds cleanly.

## Pending Change: Project Owner Email Notifications

- **Mode:** Modify the existing application and Azure deployment.
- **Requested capability:** Select displayed storage accounts from any account list and notify project owners by email.
- **Temporary recipient:** `nrp@microsoft.com`.
- **Classification and scale:** Production-like stakeholder pilot, 2,500 synthetic accounts,
  interactive low-volume sends, and a maximum of 100 unique accounts per notification.
- **Budget posture:** Cost-optimized pay-as-you-go email delivery with no dedicated mail
  infrastructure or additional always-on compute.
- **Planned Azure services:** Azure Communication Services, Email Communication Service,
  and an Azure-managed email domain in the Europe data geography. All three ARM resources
  use the required `global` control-plane location.
- **Sender:** The generated `DoNotReply@<azure-managed-domain>` address. The exact address
  is resolved from the deployed domain and injected into the Container App.
- **Authentication:** `DefaultAzureCredential` selects the existing web user-assigned
  managed identity. ACS does not provide a send-only built-in role for Entra-authenticated
  email. With explicit user approval, that identity receives the required
  `Communication and Email Service Owner`
  (`09976791-48a7-449e-bb21-39d1a415f350`) assignment scoped only to the new
  Communication Services resource. No ACS connection string, access key, or secret is stored.
- **Network posture:** Existing application/data private-link boundaries remain unchanged.
  The Container App reaches the ACS email data-plane endpoint over outbound HTTPS; the
  service is protected by Entra token authentication, resource-scoped RBAC, and disabled
  local/key authentication. No inbound route is added.
- **API:** Add authenticated `POST /api/notifications/project-owners` with a bounded list
  of unique account IDs. The server resolves trusted account details from `ACCOUNTS`,
  rejects empty, unknown, duplicate, or oversized selections, and never accepts recipient
  addresses or account fields from the browser.
- **Email behavior:** One send operation per button activation, addressed only to
  `nrp@microsoft.com` for this pilot. The message includes escaped HTML and plain-text
  tables with account, subscription, management group, business unit, environment,
  region, tier, project, risk score, findings, and recommended action. The API returns the
  ACS operation ID/status and account count; UI wording distinguishes accepted-for-delivery
  from final mailbox delivery.
- **UI behavior:** Reuse one accessible notification toolbar and checkbox pattern across
  every rendered account surface: Overview platform-linked accounts, Overview at-risk
  accounts, Agent Investigation account reasons, Savings candidates, Findings cards, and
  Data Health drilldowns. Selection is scoped to each tile, the tile's button is disabled
  until at least one account is selected, duplicate submits are blocked while sending,
  and success/error status is announced accessibly.
- **Implementation files:** `infra/app/workload.bicep`, `infra/main.bicep`,
  `pyproject.toml`, `src/web/app.py`, a focused notification service under `src/web/`,
  `src/web/static/app.js`, `styles.css`, `translations.js`, `index.html`, tests, and
  directly related documentation.
- **Verification:** Unit-test account resolution, escaping, plain-text/HTML templates,
  SDK request shape, errors, and request bounds; acceptance-test every UI surface, disabled
  and enabled states, translations, dependency pin, managed-identity settings, RBAC,
  resources, and cache key. Then run Python/JavaScript/Bicep validation, Azure what-if,
  provision the email resources, send a live test to `nrp@microsoft.com`, build a fresh
  image, deploy a new healthy Container App revision, and restore ACR to private/default-deny.
- **Implementation status:** Plan complete; explicit approval is required before execution.

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
19. **Project-owner notifications:** Every tile that renders storage accounts provides
    accessible per-account checkboxes and a **Notify project owners** action. The action
    remains disabled until that tile has a selection and sends one actionable summary
    email through Azure Communication Services. During the pilot, the server-controlled
    recipient is `nrp@microsoft.com`; browser-supplied recipient addresses are not accepted.

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
| Owner email delivery | Azure Communication Services + Email Communication Service | Global ARM resources, Europe data geography, Azure-managed domain, pay-as-you-go |

### Access model

- The web endpoint is internet-reachable but requires Entra authentication.
- Foundry, storage, Cosmos DB, Search, Key Vault, ACR, Functions tools, and Durable Task Scheduler use private connectivity.
- Managed identities and least-privilege RBAC replace account keys and connection secrets.
- The web UAMI receives Communication and Email Service Owner only on the new Communication
  Services resource because ACS has no send-only managed-identity role; the email SDK uses
  `DefaultAzureCredential` and the resource endpoint.
- Email delivery adds outbound HTTPS only. It does not expose an inbound service, weaken
  existing private endpoints, or permit client-selected recipients.
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
| Communication Services resources | 1 | Existing usage + 1 | 10 per subscription by default | Confirm during validation before provisioning |
| Email Communication Services resources | 1 | Existing usage + 1 | 10 per subscription by default | Confirm during validation before provisioning |

**Status:** Existing resources and model capacity are within available limits. Communication
Services and Email Communication Services counts/availability remain a blocking validation
check before provisioning.

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
- Azure Communication Services Email remains pay-as-you-go; the UI batches up to 100
  selected accounts into one message instead of sending one message per account.

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
- Public network access remains disabled for all private-link-capable data-plane services
  and Foundry. ACS Email is the documented outbound-only exception and accepts only
  Entra-authenticated, RBAC-authorized sends from the application identity.
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
- All six account-rendering surfaces expose labeled checkboxes and a tile-level
  **Notify project owners** button that is disabled with no selection and enabled with one
  or more selected accounts.
- Account selections are isolated per tile and duplicate submissions are blocked while an
  email operation is running.
- The notification API requires the existing authenticated principal, accepts only 1-100
  unique account IDs, resolves records server-side, and rejects unknown IDs, duplicates,
  browser-supplied recipient data, and malformed requests.
- Notification messages contain escaped HTML plus plain text and include the complete
  actionable account context, risk findings, and recommended next action.
- The Container App authenticates to Azure Communication Services with its existing UAMI;
  no ACS keys, connection strings, or secrets appear in code, configuration, deployment
  outputs, Container App secrets, or logs.
- A live send to `nrp@microsoft.com` returns an ACS succeeded operation ID/status, and the
  UI reports accepted-for-delivery without claiming final mailbox delivery.
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
- [x] Analyze the project-owner notification change and applicable account surfaces
- [x] Select Azure Communication Services Email, Azure-managed domain, and managed identity
- [x] Finalize notification API, UI, security, cost, and verification decisions
- [x] User approved the project-owner notification change
- [x] User approved the required resource-scoped Communication and Email Service Owner role

### Build and preparation

- [x] Scaffold from official templates and compose approved modules
- [x] Build synthetic data generator and connector contracts
- [x] Implement analytics, tools, agent, API, and React UI
- [x] Add documentation, threat boundaries, and phase-2 Teams/Copilot design
- [x] Verify locally: 28 tests, browser smoke, SDK imports, and Bicep build
- [x] Set plan status to `Ready for Validation`
- [x] Add Azure Communication Services Email resources, domain link, role, and app settings
- [x] Add the pinned email SDK, notification service, authenticated API, and templates
- [x] Add reusable account selection/notification controls to all six account surfaces
- [x] Add translations, responsive/accessibility styles, documentation, and cache busting
- [x] Add and pass targeted plus full application tests
- [x] Set plan status to `Ready for Validation`

### Validation and deployment

- [x] Re-run `azure-validate` for Sweden Central
- [x] Resolve all validation failures and record evidence
- [x] Set status to `Validated`
- [x] Invoke `azure-deploy`
- [x] Verify network isolation, RBAC, live UI, Function health, MCP, and A2A
- [x] Set status to `Deployed`
- [x] Invoke `azure-validate` for the approved notification change
- [x] Confirm ACS/Email resource availability, provider registration, limits, and Europe data geography
- [x] Review what-if and verify there are no deletes or unintended replacements
- [x] Invoke `azure-deploy` to provision email resources and role assignment
- [x] Send and verify the live pilot notification to `nrp@microsoft.com`
- [x] Build and deploy a fresh Container App image and verify the new revision/assets
- [x] Restore ACR public access disabled, firewall default deny, and admin credentials disabled
- [ ] Commit, push, create a pull request, merge it, and verify `origin/main`

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

> Current: AIRGAP spreadsheet Cosmos persistence is deployed and ready for source-control publication.

Commit the validated change, push it, create a pull request, and merge it.

---

## 14. Validation Proof

### Validation checks

- [x] All validation checks pass
  - [x] AZD installation
  - [x] Azure YAML schema and environment setup
  - [x] Authentication, subscription, and location
  - [x] Provision preview and Bicep build
  - [x] Python/JavaScript build verification
  - [x] Docker build-context and package validation
  - [x] Azure Policy validation
  - [x] Static RBAC role verification
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

- 2026-08-21 AIRGAP spreadsheet Cosmos-persistence deployment: `azd provision
  --no-prompt` confirmed no infrastructure changes. ACR run `dtg` published
  `storage-intelligence:airgap-cosmos-20260821` with digest
  `sha256:fc09dbca8635737326b8ef6f1d034c586064e1c496f75dbc70ae30f4117a77c2`.
  Container App revision `ca-storage-intel-kxlgam3w--0000017` is Healthy,
  Provisioned, running at maximum scale, and receives 100% of traffic. The live
  application remains protected by Microsoft Entra (unauthenticated HTTP 401).
  ACR was restored to public access disabled, firewall default `Deny`, and admin
  credentials disabled. Cosmos DB remains private with local authentication
  disabled and `/subscription_id` partitioning. Live role verification confirmed
  the web UAMI retains resource-scoped `AcrPull` and Cosmos DB Built-in Data
  Contributor scoped to the `storage-intelligence` database.
- 2026-08-21 AIRGAP spreadsheet Cosmos-persistence validation: confirmed AZD 1.30.0,
  authenticated environment `mcpa2a`, approved subscription
  `c82406dd-f84c-42df-9586-c6f02abda6df`, and Sweden Central. The complete
  97-test suite and Python compilation passed; JavaScript syntax checks, Bicep
  build, `azd package --no-prompt`, and `git diff --check` passed. `azd
  provision --preview --no-prompt` completed successfully with no resource
  deletes. Subscription policies do not conflict with this application-only
  update. Static RBAC review confirmed the web UAMI retains Cosmos DB Built-in
  Data Contributor scoped to the existing `storage-intelligence` database; no
  infrastructure, role, or quota change is required.
- 2026-08-21 AIRGAP import-heading deployment: `azd provision --no-prompt`
  confirmed no infrastructure changes. ACR run `dtf` published
  `storage-intelligence:airgap-heading-20260821` with digest
  `sha256:b590da2eb79e1b63fe2390a47f0bb30e576d069ad29911f9fcfc17585cf193bc`.
  Container App revision `ca-storage-intel-kxlgam3w--0000016` is Healthy,
  Provisioned, running at maximum scale, and receives 100% of traffic. The live
  application remains protected by Microsoft Entra (unauthenticated HTTP 401).
  ACR was restored to public access disabled, firewall default `Deny`, and admin
  credentials disabled; the web UAMI retains resource-scoped `AcrPull`.
- 2026-08-21 AIRGAP import-heading validation: confirmed the approved `mcpa2a`
  Sweden Central environment and authentication; 93 tests passed; JavaScript
  syntax checks, Bicep build, and `azd package --no-prompt` passed. `azd
  provision --preview --no-prompt` completed without resource deletes.
  Applicable policies and the existing resource-scoped web-UAMI `AcrPull`
  assignment were reviewed; no infrastructure or RBAC change is required.
- 2026-08-21 AIRGAP sample workbook deployment: `azd provision --no-prompt`
  confirmed no infrastructure changes. ACR run `dte` published
  `storage-intelligence:airgap-sample-20260821` with digest
  `sha256:e553eda8fa4c694a5ddb4150636853c26eca4c4d9f03e8b78f204ac2493a9476`.
  Container App revision `ca-storage-intel-kxlgam3w--0000015` is Healthy,
  Provisioned, running one replica, and receives 100% of traffic. The live
  `Sample.xlsx` route is protected by Microsoft Entra (unauthenticated HTTP
  401). ACR was restored to public access disabled, firewall default `Deny`,
  and admin credentials disabled; the web UAMI retains resource-scoped
  `AcrPull`.
- 2026-08-21 AIRGAP sample workbook validation: confirmed the approved
  `mcpa2a` Sweden Central environment and Azure authentication; 93 tests passed;
  Python compilation, JavaScript syntax checks, Bicep build, and
  `azd package --no-prompt` passed. The workbook contains exactly the requested
  36-column header, downloads as a valid XLSX, and imports successfully after an
  account row is populated. `azd provision --preview --no-prompt` completed
  without resource deletes. Applicable policies and the existing
  resource-scoped web-UAMI `AcrPull` assignment were reviewed; no infrastructure
  or RBAC change is required.
- 2026-08-21 project-owner notification deployment: `azd provision
  --no-prompt` provisioned Azure Communication Services, the Email Service,
  Azure-managed domain, domain link, app settings, and resource-scoped web-UAMI
  role. ACR run `dtd` published
  `storage-intelligence:owner-notifications-20260821` with digest
  `sha256:afdff74c019d9a17ea1554fed4bc214bd7894435176f42dd3377665106b286a3`.
  Container App revision `ca-storage-intel-kxlgam3w--0000014` is Healthy,
  Provisioned, running one replica, and receives 100% of traffic. ACS has local
  auth disabled and the Azure-managed sender domain is linked and succeeded.
  Live role checks confirmed `AcrPull` on ACR and `Communication and Email
  Service Owner` only on the Communication Service for the web UAMI. A live
  one-account message to `nrp@microsoft.com` completed with ACS operation
  `67b87a74-0b16-477e-aa3c-dea592736e9a` and status `Succeeded`. ACR was restored
  to public access disabled, firewall default `Deny`, and admin credentials
  disabled. The unchanged private Function SCM endpoint rejected the redundant
  AZD package upload with a TLS timeout; its existing deployment was not
  modified and the independently deployed Container App remains healthy.
- 2026-08-21 project-owner notification validation: registered the required
  `Microsoft.Communication` provider; `azd provision --preview --no-prompt`
  passed against the existing `mcpa2a` Sweden Central environment; expanded
  subscription what-if confirmed four Communication/Email creates and no
  deletes. `az bicep build --file infra/main.bicep --stdout`, Python
  compilation, JavaScript syntax checks, and `azd package --no-prompt` passed.
  The complete suite passed with 92 tests. Subscription policy assignments do
  not restrict the planned resources. Static RBAC review confirmed the web UAMI
  receives `Communication and Email Service Owner`
  (`09976791-48a7-449e-bb21-39d1a415f350`) scoped only to the new Communication
  Service. The Container App trusts only server-resolved account data and uses
  managed identity without ACS keys or connection strings.
- 2026-08-21 centered risk-description hint deployment: `azd provision
  --no-prompt` confirmed no infrastructure changes. ACR run `dtc` published
  `storage-intelligence:risk-hint-20260821` with digest
  `sha256:57a6839295e990987ce75d84b1d24fb0ca9b6686a7eca2b4114bc2787944ddc0`.
  Container App revision `ca-storage-intel-kxlgam3w--0000012` is Healthy,
  Provisioned, and receives 100% of traffic. Internal readiness passed with all
  2,500 accounts, and the running image contains the centered hint CSS and new
  cache key. Public access redirects to Microsoft Entra. ACR public access was
  restored to Disabled, firewall default `Deny`, and admin credentials
  disabled; live managed-identity role checks remained resource scoped.
- 2026-08-21 centered risk-description hint validation: 88 tests passed;
  JavaScript syntax and Python compilation passed; Bicep build and lint passed;
  `azd package --no-prompt` completed; and `azd provision --preview
  --no-prompt` completed against the confirmed `mcpa2a` Sweden Central
  environment without resource deletion or replacement. Assigned policies and
  the unchanged resource-scoped managed-identity roles were reviewed.
- 2026-08-21 consolidated Overview risk deployment: `azd provision
  --no-prompt` confirmed no infrastructure changes. ACR run `dtb` published
  `storage-intelligence:risk-consolidation-20260821` with digest
  `sha256:f33f98d7cc7b193df64109e2d1227f811310d47171aa9c5195267513ad2fe2dc`.
  Container App revision `ca-storage-intel-kxlgam3w--0000011` is Healthy,
  Provisioned, and receives 100% of traffic. Internal `/healthz` and `/readyz`
  checks passed with all 2,500 accounts available, and the running image
  contains the consolidated account-details UI and cache key. Public access
  redirects to Microsoft Entra. ACR public access was restored to Disabled,
  firewall default `Deny`, and admin credentials disabled. Live role review
  confirmed the web and Function managed identities retain their expected
  resource-scoped assignments.
- 2026-08-21 consolidated Overview risk validation: 88 tests passed;
  JavaScript syntax and Python compilation passed; Bicep build and lint passed;
  `azd package --no-prompt` produced the Function package; and `azd provision
  --preview --no-prompt` completed against the confirmed `mcpa2a` Sweden
  Central environment without resource deletion or replacement. Subscription
  and management-group policies were reviewed. Static RBAC review confirmed
  that the unchanged web and Function managed identities retain their
  resource-scoped data-plane and deployment roles.
- 2026-08-21 Overview UI deployment: the first ACR run (`dt9`) exposed a
  Debian Trixie/Bookworm package mismatch while installing Azure CLI. The web
  image now uses the pinned `python:3.13-slim-bookworm` manifest. Replacement
  ACR run `dta` succeeded and published
  `storage-intelligence:overview-refresh-20260821` with digest
  `sha256:5bbf8b61690cb11cf8675a3760aa4561f3a7166245a59efe541b352488320e52`.
  Container App revision `ca-storage-intel-kxlgam3w--0000010` is Healthy,
  Provisioned, and receives 100% of traffic. Internal `/healthz` and `/readyz`
  checks passed, with readiness reporting all 2,500 accounts. The running
  container contains the Overview cache key, AIRGAP upload label, persistent
  account scrollbar, and reduced Entra icon assets. Public routes redirect to
  Microsoft Entra as designed. ACR public access was restored to Disabled,
  firewall default `Deny`, and admin credentials disabled; the web UAMI retains
  its resource-scoped `AcrPull` assignment.
- 2026-08-21 Overview UI deployment validation: 88 tests passed;
  `node --check src/web/static/app.js`, Python compilation, and `az bicep build
  --file infra/main.bicep --stdout` passed. `azd package --no-prompt` produced
  the Function package, and `azd provision --preview --no-prompt` completed
  against the existing `mcpa2a` Sweden Central environment without resource
  deletion or replacement. Assigned subscription and management-group policies
  were reviewed. Static and live role review confirmed the web UAMI retains
  resource-scoped `AcrPull`, Foundry User, Website Contributor, and
  database-scoped Cosmos data access; Function UAMI data-plane roles remain
  resource scoped.
- 2026-08-21 Priority Findings UI redeployment validation: 88 tests passed,
  `node --check src/web/static/app.js` and `az bicep build --file
  infra/main.bicep --stdout` passed, and `azd provision --preview --no-prompt`
  completed against the existing `mcpa2a` Sweden Central environment with no
  resource deletion. Static managed-identity RBAC assignments remain unchanged.
- 2026-08-21 Priority Findings UI redeployment: `azd provision --no-prompt`
  confirmed no infrastructure changes; ACR build `dt8` produced
  `storage-intelligence:priority-scroll-20260821` with digest
  `sha256:a4c375adfbe22d90c3d1c2b9209db704ddc7397c327d1273ddcdc6d0bc0ff57f`.
  Container App revision `ca-storage-intel-kxlgam3w--0000009` reached
  `Healthy`/`Provisioned` with 100% traffic and sustained HTTP 200 health and
  readiness probes. In-revision inspection confirmed the
  `priority-findings-panel`, `priority-findings-scroll`, persistent horizontal
  overflow styling, responsive height rule, and `20260821-priority-scroll`
  browser cache key. ACR was restored to public access disabled, firewall
  default `Deny`, and admin credentials disabled; the web identity retained
  resource-scoped `AcrPull`.
- 2026-08-21 managed-identity UI redeployment validation: 88 tests passed,
  `node --check src/web/static/app.js` passed, `az bicep build --file
  infra/main.bicep --stdout` passed, `azd package --no-prompt` completed, and
  `azd provision --preview --no-prompt` completed successfully against the
  existing `mcpa2a` Sweden Central environment with no resource deletion.
  Static RBAC review confirmed resource-scoped managed-identity assignments;
  applicable subscription and management-group policies were reviewed.
- 2026-08-21 managed-identity UI redeployment: `azd provision --no-prompt`
  confirmed no infrastructure changes; ACR build `dt7` produced
  `storage-intelligence:miui-20260821` with digest
  `sha256:e0bf7a335ade5add751fddf8e7d344cd1d5128b7ec632878f8ba638588c21f9b`.
  Container App revision `ca-storage-intel-kxlgam3w--0000008` reached
  `Healthy`/`Provisioned`, received 100% of traffic, and sustained HTTP 200
  responses on `/healthz` and `/readyz`. In-revision inspection confirmed the
  Managed Identity Data Health tile and enabled/disabled storage-account tags;
  the image also contains the Function App and Log Analytics account tags from
  the preceding change. Entra continues to protect public UI/API/protocol
  routes. ACR was restored to public access disabled, firewall default `Deny`,
  and admin credentials disabled.
- 2026-08-20 UI visibility redeployment validation: 87 tests passed,
  `node --check src/web/static/app.js` passed, `az bicep build --file
  infra/main.bicep --stdout` passed, managed-identity `AcrPull` was present, and
  `azd provision --preview --no-prompt` completed successfully against the
  existing `mcpa2a` Sweden Central environment with no resource deletions.
- 2026-08-20 UI visibility redeployment: ACR build `dt6` produced image digest
  `sha256:e9f6b4f2d038fe40f36e8310c82d9c42cf5fa6013daa089f9ae9dbe66179e3a0`;
  Container App revision `ca-storage-intel-kxlgam3w--0000007` reached healthy
  status; live assets contained the `20260820-protocols` cache key, visible
  `MCP & A2A Enabled` label, accessibility status, and badge styling. ACR was
  restored to private/default-deny with admin credentials disabled.
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
- Container App revision `ca-storage-intel-kxlgam3w--0000009` and Function
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
- 2026-08-21 live re-verification confirmed the web identity's AcrPull,
  Foundry User, and Function-scoped Website Contributor roles and the Function
  identity's seven resource-scoped storage, lake, scheduler, Key Vault, and
  monitoring roles.
- Scope: Service roles are scoped to their individual resources. No workload identity receives subscription-wide data-plane access.
- Issues: None. The temporary diagnostic Storage Blob Data Reader assignment was
  removed from the web identity after verification.
