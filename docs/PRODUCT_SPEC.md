# Storage Intelligence Agent Product Spec

## Pilot outcome

The Storage Intelligence Agent gives StorageOps, FinOps, DataOps, Databricks, and
business stakeholders one read-only view of capacity, cost, growth, freshness, risk,
forecast, and tiering opportunity. The pilot runs against a deterministic synthetic
estate of 2,500 Azure Storage accounts while retaining production connector contracts.

## Experience

- **Overview:** account count, capacity, cost, weighted growth, savings, freshness, and risk.
- **Global language:** a top-right English/Spanish selector persists per browser and
  localizes all six views, navigation, controls, statuses, accessibility labels, dynamic
  count text, risk explanations, and built-in investigation prompts. Data identifiers,
  filters, resource names, and API contracts remain locale-neutral.
- **Agent Investigation:** natural-language questions route to bounded deterministic
  tools, return the complete trust envelope, explain every returned account with the
  query-specific metrics that caused its ranking, cite every unique returned account, and
  build an eight-item session history. A broad built-in catalog covers anomaly, cost,
  capacity, lifecycle, replication, hierarchy, SAP, ADF, Databricks, and freshness
  investigations. Authenticated users can save a new question as a reusable future option.
- **Portfolio comparison:** tenant ID, management group, subsidiary/business unit,
  subscription, environment (Dev/QA/Perf/Prod), region, tier, and Databricks filters
  appear consistently on every view.
- **Selection catalogs:** authenticated users can add pilot tenants, management groups,
  subscriptions, subsidiaries/business units, add tracked regions, and choose from the complete customer-facing Azure public
  region catalog in filters, manual onboarding, and spreadsheet imports.
- **Admin discovery:** a dedicated left-navigation item is visible only to users with the
  `StorageIntelligence.Admin` app role. It triggers tenant-wide read-only Azure CLI
  discovery, enumerates every authorized tenant, management group, subscription, and
  storage account, captures region/access tier/SKU/subsidiary tags, and refreshes the pilot inventory
  idempotently.
- **Scheduled discovery:** administrators can validate and persist a configurable
  five-field cron expression, see its next run, and persist every manual or scheduled
  discovery result idempotently in private Cosmos DB. The committed six-hour external
  fallback cron can also write an atomic JSON snapshot.
- **Platform highlights:** storage accounts linked to Databricks, Fabric Lakehouse, SAP,
  Azure Data Factory, SFTP, or Application Insights appear in a dedicated panel with small
  accessible marks and linked system/factory/telemetry names. These relationships are
  deterministically randomized in the synthetic fixture.
- **Risk concentration:** the chart names all eight transparent risk dimensions (Growth,
  Cost, Freshness, Operations, Databricks, Configuration, Security, and Governance), labels each account with
  its dominant dimension, and uses a consistent low-saturation palette optimized for the
  light theme. A donut-style pie chart shows counts and percentages by dominant risk type,
  followed by every scoped account at or above the transparent score-20 at-risk threshold
  in a vertically scrollable list. Pointer hover reveals a segment's description, count,
  and percentage, with keyboard focus and live-region support for accessibility.
- **Security and governance posture:** account-level factors identify SAS/shared-key use,
  public network/blob access, missing private endpoints, non-GRS/GZRS replication,
  NSG/ASG association, missing service-principal access, project/business-unit tags,
  last-access age, and defunct projects. The same factors appear in Overview, Findings,
  Data Health, and Agent Investigation. SFTP enablement contributes an explicit Security
  factor; Application Insights-linked storage is separately counted and queryable.
- **Posture drilldown:** eleven Data Health tiles, including Stale accounts, Missing
  lifecycle, SFTP Enabled, and AppInsights Data, are keyboard-accessible buttons. The
  shared drilldown replaces the redundant standalone stale-account list.
  Clicking a tile lists all matching scoped accounts directly below, ordered by overall
  risk in a scrollable panel with factor detail, project, hierarchy, region, tier, and score.
- **Priority findings:** the top eight accounts show labeled Growth and Operations
  component scores. Operations is derived from throttling and request latency; the
  right-hand value is explicitly displayed as the weighted overall score out of 100.
- **Savings Simulator:** a 1-100% adoption control runs deterministic tier savings,
  compares 10/25/50% scenarios, and ranks candidates with retention warnings.
- **Findings:** five clickable summary tiles (Total Findings, Data Freshness, Growth
  Anomaly, Risk, and Savings Action) filter a severity-sorted, vertically scrollable inbox
  for the active portfolio scope. No duplicate filter-button row is rendered.
- **Data Health:** freshness coverage, connector/source states, configuration-quality
  gaps, and stale-account actions are visible in a dedicated operational view. For admins,
  **Disabled** is the enable control. After activation it becomes **Enabled** and exposes
  **Run**; a successful pilot-fixture run becomes **Healthy**, with synced versus eligible
  records and last-run timestamps shown explicitly.
  The seven source cards render first, immediately after the global filters/reset row.
- **Forecast and anomaly:** bounded 30/90/180-day forecasts and median-absolute-deviation outliers.
- **Trust envelope:** every answer includes scope, timestamp, evidence, assumptions, and
  confidence. Account-ranking answers include a reason per account, and their evidence IDs
  exactly match the unique account IDs in the result.
- **Saved question library:** custom questions are normalized, deduplicated, capped at 100,
  and stored globally in private Cosmos DB in Azure or an atomic local JSON file during
  localhost development. Saving does not execute the question.
- **Pilot onboarding:** authenticated users can add a tracked storage account by selecting
  its tenant ID, management group, subscription, environment, subsidiary/business unit,
  region, and access tier. This updates only the
  synthetic pilot inventory and never provisions an Azure resource.
- **Bulk onboarding:** users can upload an XLSX or UTF-8 CSV inventory with account name,
  tenant ID, management group, subscription, environment, subsidiary/business unit,
  region, and tier.
  The import is atomic, capped at 10,000
  rows/5 MB, normalizes friendly headers, and rejects invalid or duplicate records.
- **Subscription topology:** the synthetic fixture exposes exactly 339 mapped subscriptions
  across Dev, QA, Perf, and Prod; all are selectable and validated against their hierarchy.
- **PepsiCo branding:** the responsive shell presents a PepsiCo globe and wordmark in
  desktop and compact mobile layouts without external asset requests.
- **Footer attribution:** desktop navigation carries the PepsiCo copyright notice and
  compact accessible Microsoft, Azure, and the user-supplied Azure AI Foundry PNG served
  from the repository without external image requests.

The locale dictionary is committed as `src/web/static/translations.js` and loaded before
the application script; no runtime translation service or external request is used.

The browser uses React 18.3.1 UMD assets committed under `src/web/static/vendor`; it
requires no Node.js, npm, CDN, or browser-time package download.

The Azure UI and protocol endpoint uses one warm Container Apps replica at 1 vCPU/2 GiB,
HTTPS ingress to target port `8000`, 10-second probe timeouts, and Entra authentication.
Web availability is independent of private Function deployment and Foundry smoke-test
lifecycle.

## Safety contract

The system does not mutate Azure resources, tiers, lifecycle rules, or Databricks
configuration. Model-generated SQL/KQL is not accepted. Numerical answers come from the
versioned Python tool catalog. Empty or stale evidence lowers confidence and is surfaced
instead of replaced by a fallback.

## Production connector contracts

| Connector | Production input | Pilot state |
|---|---|---|
| Azure Resource Graph | Storage account resource/configuration snapshots | Disabled |
| Blob Inventory | Latest manifest and Parquet inventory files | Disabled |
| Azure Monitor Metrics | Batched capacity, transaction, latency, and availability metrics | Disabled |
| Cost Management | Scheduled exports delivered to central ADLS Gen2 | Disabled |
| Databricks | System-table exports for IO, jobs, queries, and external locations | Disabled |

Each production connector requires an explicit runtime flag and managed identity. The
pilot grants no estate-wide reader roles.

## Acceptance

The automated query catalog exercises all approved stakeholder questions. It verifies
the 2,500-account estate, deterministic fingerprint, filters, connector disablement,
authentication boundary, and answer trust fields.
