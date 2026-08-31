(function () {
  "use strict";
  const rawCreateElement = React.createElement;
  const { useEffect, useMemo, useState } = React;
  let activeLanguage = localStorage.getItem("storage-intelligence-language") === "es" ? "es" : "en";

  function translateText(value, language) {
    return window.StorageI18n.translate(value, language || activeLanguage);
  }

  function translatedChild(value) {
    if (typeof value === "string") return translateText(value);
    if (Array.isArray(value)) return value.map(translatedChild);
    return value;
  }

  function e(type, props) {
    const children = Array.prototype.slice.call(arguments, 2).map(translatedChild);
    let translatedProps = props;
    if (props) {
      translatedProps = Object.assign({}, props);
      ["aria-label", "title", "placeholder", "alt"].forEach((name) => {
        if (typeof translatedProps[name] === "string") {
          translatedProps[name] = translateText(translatedProps[name]);
        }
      });
    }
    return rawCreateElement.apply(null, [type, translatedProps].concat(children));
  }

  const riskTypes = [
    { key: "growth", label: "Growth", description: "Rapid capacity expansion", color: "#6ea8fe", colorName: "Cornflower blue" },
    { key: "cost", label: "Cost", description: "Rising monthly storage spend", color: "#e8a87c", colorName: "Soft terracotta" },
    { key: "freshness", label: "Freshness", description: "Stale or missing telemetry", color: "#8ed1c6", colorName: "Seafoam" },
    { key: "operations", label: "Operations", description: "Latency and throttling pressure", color: "#b7a1e5", colorName: "Lavender" },
    { key: "databricks", label: "Databricks", description: "IO and small-file impact", color: "#f08a7e", colorName: "Soft coral" },
    { key: "configuration", label: "Configuration", description: "Lifecycle, retention, or replication resilience", color: "#d7bd7a", colorName: "Muted gold" },
    { key: "security", label: "Security", description: "SAS/shared keys, public access, private endpoint, network group, and service-principal posture", color: "#c98f8f", colorName: "Dusty rose" },
    { key: "governance", label: "Governance", description: "Project ownership, business-unit tags, last access, and defunct status", color: "#9ea77d", colorName: "Sage olive" }
  ];
  const riskTypeColors = Object.fromEntries(riskTypes.map((riskType) => [riskType.key, riskType.color]));
  const applicationViews = [
    { id: "overview", label: "Overview", icon: "/static/assets/nav-overview.svg", eyebrow: "Estate command center", title: "Overview", subtitle: "Capacity, Cost, Risk, Impact, And Defensible Savings." },
    { id: "health", label: "Data Health", icon: "/static/assets/nav-health.svg", eyebrow: "Connector observability", title: "Data Health", subtitle: "Inspect Source Status, Freshness Coverage, Stale Accounts, And Quality Gaps." },
    { id: "findings", label: "Findings", icon: "/static/assets/nav-findings.svg", eyebrow: "Actionable inbox", title: "Findings", subtitle: "Review Prioritized Risks, Anomalies, Freshness Issues, And Savings Actions." },
    { id: "savings", label: "Savings Simulator", icon: "/static/assets/nav-savings.svg", eyebrow: "FinOps modeling", title: "Savings Simulator", subtitle: "Compare tiering adoption scenarios with retrieval and early-deletion caveats." },
    { id: "agent", label: "Agent Investigation", icon: "/static/assets/nav-agent.svg", eyebrow: "Evidence-first analysis", title: "Agent Investigation", subtitle: "Ask scoped operational and financial questions backed by deterministic tools." },
    { id: "admin", label: "Admin", icon: "/static/assets/nav-admin.svg", eyebrow: "Estate administration", title: "Admin", subtitle: "Schedule read-only tenant-wide storage inventory retrieval through Azure CLI." }
  ];

  function NavIcon(props) {
    return e("img", {
      className: "nav-icon",
      src: props.view.icon,
      alt: "",
      "aria-hidden": "true"
    });
  }

  function dominantRisk(row) {
    return riskTypes.reduce((current, candidate) =>
      row.components[candidate.key] > row.components[current.key] ? candidate : current
    , riskTypes[0]);
  }

  function formatNumber(value, kind) {
    const locale = activeLanguage === "es" ? "es-ES" : "en-US";
    if (kind === "money") return "$" + Math.round(value).toLocaleString(locale);
    if (kind === "tb") return Math.round(value).toLocaleString(locale) + " TB";
    if (kind === "pct") return Number(value).toLocaleString(locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "%";
    return Number(value).toLocaleString(locale);
  }

  function apiError(body, fallback) {
    if (typeof body.detail === "string") return body.detail;
    if (body.detail && body.detail.message) {
      const rows = body.detail.errors ? " " + body.detail.errors.slice(0, 3).join(" ") : "";
      return body.detail.message + rows;
    }
    return fallback;
  }

  function Metric(props) {
    return e("div", { className: "metric" },
      e("div", { className: "metric-label" }, props.label),
      e("div", { className: "metric-value" }, props.value),
      e("div", { className: "metric-delta" }, props.note)
    );
  }

  function PostureMetric(props) {
    return e("button", {
      type: "button",
      className: "metric metric-action" + (props.active ? " active" : ""),
      onClick: props.onClick,
      "aria-pressed": props.active,
      "aria-label": props.label + ": " + props.value + ". Show matching accounts."
    },
      e("div", { className: "metric-label" }, props.label),
      e("div", { className: "metric-value" }, props.value),
      e("div", { className: "metric-delta" }, props.note),
      e("div", { className: "metric-action-hint" }, props.active ? "Showing accounts below" : "Click to list accounts")
    );
  }

  function AccountCheckbox(props) {
    return e("label", {
      className: "account-select-control",
      title: "Select account for owner notification: " + props.name
    },
      e("input", {
        type: "checkbox",
        checked: props.checked,
        onChange: (event) => props.onChange(event.target.checked),
        "aria-label": "Select account for owner notification: " + props.name
      }),
      e("span", { className: "account-select-box", "aria-hidden": "true" })
    );
  }

  function NotificationToolbar(props) {
    const status = props.status;
    return e("div", { className: "notification-toolbar-wrap" },
      e("div", { className: "notification-toolbar" },
        e("span", { className: "notification-selection-count" }, props.selectedIds.length + " selected"),
        e("button", {
          type: "button",
          className: "notify-owners-button",
          disabled: props.busy || props.selectedIds.length === 0,
          onClick: () => props.onNotify(props.selectedIds),
          "aria-label": "Notify project owners for selected storage accounts"
        }, props.busy ? "Sending notification…" : "Notify project owners")
      ),
      status && e("div", {
        className: "notification-status " + status.tone,
        role: status.tone === "error" ? "alert" : "status",
        "aria-live": "polite"
      }, status.message)
    );
  }

  function PostureDrilldown(props) {
    const accounts = props.data ? props.data.accounts : [];
    const selectedIds = props.selectedIds(accounts.map((account) => account.account_id));
    return e("section", { className: "panel posture-drilldown" },
      e("div", { className: "panel-head" },
        e("div", { className: "panel-title" }, props.data ? props.data.label + " accounts" : "Loading posture accounts"),
        e("div", { className: "notification-panel-meta" },
          e("div", { className: "panel-meta" }, props.data ? props.data.count + " matches · scrollable" : "Loading…"),
          e(NotificationToolbar, {
            selectedIds: selectedIds,
            busy: props.notificationBusy,
            status: props.notificationStatus,
            onNotify: props.onNotify
          })
        )
      ),
      props.busy
        ? e("div", { className: "loading posture-loading" }, "Loading matching accounts…")
        : props.data && e("div", { className: "posture-account-list risk-scroll" },
            accounts.map((account) =>
              e("div", { className: "posture-account-row" + (selectedIds.includes(account.account_id) ? " selected" : ""), key: account.account_id },
                e(AccountCheckbox, {
                  name: account.name,
                  checked: selectedIds.includes(account.account_id),
                  onChange: (checked) => props.onToggle(account.account_id, checked)
                }),
                e("div", { className: "posture-account-identity" },
                  e("strong", null, account.name),
                  e("span", null, account.management_group + " · " + account.subsidiary + " · " + account.subscription + " · " + account.environment)
                ),
                e("div", { className: "posture-account-detail" },
                  e("span", null, account.detail),
                  e("small", null, (account.project_name || "Project unassigned") + " · " + account.region + " · " + account.tier)
                ),
                e("div", { className: "posture-account-score", title: "Overall weighted risk score" }, account.score + "/100")
              )
            ),
            props.data.accounts.length === 0 && e("div", { className: "empty-state" }, "No accounts match this posture factor in the current scope.")
          )
    );
  }

  function FindingMetric(props) {
    return e("button", {
      type: "button",
      className: "metric metric-action" + (props.active ? " active" : ""),
      onClick: props.onClick,
      "aria-pressed": props.active,
      "aria-label": props.label + ": " + props.value + ". Show matching findings."
    },
      e("div", { className: "metric-label" }, props.label),
      e("div", { className: "metric-value" }, props.value),
      e("div", { className: "metric-delta" }, props.note),
      e("div", { className: "metric-action-hint" }, props.active ? "Showing findings below" : "Click to list findings")
    );
  }

  function Filter(props) {
    return e("select", {
      value: props.value,
      onChange: (event) => props.onChange(event.target.value),
      "aria-label": props.label
    },
      e("option", { value: "" }, "All " + props.label),
      props.items.map((item) => e("option", { value: item, key: item }, props.labels && props.labels[item] ? props.labels[item] + " (" + item + ")" : item))
    );
  }

  function ChoiceSelect(props) {
    return e("label", { className: "account-field" },
      e("span", { className: "field-label" }, props.label),
      e("select", {
        value: props.value,
        required: true,
        onChange: (event) => props.onChange(event.target.value),
        "aria-label": props.label
      },
        e("option", { value: "" }, "Select " + props.label.toLowerCase()),
        props.items.map((item) => e("option", { value: item, key: item }, props.labels && props.labels[item] ? props.labels[item] + " (" + item + ")" : item))
      )
    );
  }

  function AvidunixuserLogo() {
    return e("img", {
      className: "avidunixuser-logo",
      src: "/static/assets/avidunixuser-logo.png?v=20260831",
      alt: "Avidunixuser"
    });
  }

  function MicrosoftMiniLogo() {
    return e("span", { className: "microsoft-mini-logo", role: "img", "aria-label": "Microsoft", title: "Microsoft" },
      e("span", { className: "microsoft-mini-tile mini-red" }),
      e("span", { className: "microsoft-mini-tile mini-green" }),
      e("span", { className: "microsoft-mini-tile mini-blue" }),
      e("span", { className: "microsoft-mini-tile mini-yellow" })
    );
  }

  function AzureMiniLogo() {
    return e("span", { className: "azure-mini-logo", role: "img", "aria-label": "Microsoft Azure", title: "Microsoft Azure" });
  }

  function FoundryMiniLogo() {
    return e("img", {
      className: "foundry-mini-logo",
      src: "/static/assets/azure-ai-foundry.png",
      alt: "Azure AI Foundry",
      title: "Azure AI Foundry"
    });
  }

  function EntraAuthenticatedMark() {
    return e("span", {
      className: "entra-authenticated-mark",
      role: "img",
      "aria-label": "Microsoft Entra authenticated",
      title: "Microsoft Entra authenticated"
    },
      e("img", {
        className: "entra-id-logo",
        src: "/static/assets/microsoft-entra-id.png",
        alt: "",
        "aria-hidden": "true"
      })
    );
  }

  function DatabricksLogo() {
    return e("span", { className: "databricks-logo", role: "img", "aria-label": "Databricks", title: "Databricks" },
      e("span", { className: "databricks-layer layer-one" }),
      e("span", { className: "databricks-layer layer-two" })
    );
  }

  function LakehouseLogo() {
    return e("span", { className: "lakehouse-logo", role: "img", "aria-label": "Fabric Lakehouse", title: "Fabric Lakehouse" });
  }

  function SapLogo() {
    return e("span", { className: "sap-logo", role: "img", "aria-label": "SAP", title: "SAP" }, "SAP");
  }

  function DataFactoryLogo() {
    return e("span", { className: "data-factory-logo", role: "img", "aria-label": "Azure Data Factory", title: "Azure Data Factory" }, "ADF");
  }

  function SftpLogo() {
    return e("span", { className: "sftp-logo", role: "img", "aria-label": "SFTP enabled", title: "SFTP enabled" }, "⇄");
  }

  function AppInsightsLogo() {
    return e("span", { className: "app-insights-logo", role: "img", "aria-label": "Application Insights data", title: "Application Insights data" },
      e("span", { className: "app-insights-bulb" })
    );
  }

  function FunctionAppLogo() {
    return e("span", { className: "function-app-logo", role: "img", "aria-label": "Azure Function App", title: "Azure Function App" }, "ƒ");
  }

  function LogAnalyticsLogo() {
    return e("span", { className: "log-analytics-logo", role: "img", "aria-label": "Log Analytics", title: "Log Analytics" },
      e("span", { className: "log-analytics-bar bar-one" }),
      e("span", { className: "log-analytics-bar bar-two" }),
      e("span", { className: "log-analytics-bar bar-three" })
    );
  }

  function hasPlatformClassification(account) {
    return Boolean(
      account.databricks_workspace ||
      account.fabric_lakehouse ||
      account.sap_system ||
      account.azure_data_factory ||
      account.sftp_enabled ||
      account.application_insights_resource ||
      account.azure_function_app ||
      account.log_analytics_workspace
    );
  }

  function accountClassification(account) {
    const tags = [
      account.management_group,
      account.project_name,
      account.business_unit,
      account.tag_business_unit,
      account.subscription
    ].filter(Boolean).join(" ").toLowerCase();

    if (account.project_defunct) return { key: "archive", label: "Retired project archive" };
    if (account.hns_enabled || /data|analytics|lake/.test(tags)) {
      return { key: "data", label: "Azure data and analytics workload" };
    }
    if (account.environment === "Prod" || account.business_criticality === "high") {
      return { key: "production", label: "Production application workload" };
    }
    return { key: "nonproduction", label: (account.environment || "Non-production") + " application workload" };
  }

  function AccountClassificationLogo(props) {
    const classification = accountClassification(props.account);
    return e("span", {
      className: "classification-logo classification-" + classification.key,
      role: "img",
      "aria-label": classification.label,
      title: classification.label
    }, e("span", { className: "classification-glyph", "aria-hidden": "true" }));
  }

  function App() {
    const [language, setLanguage] = useState(activeLanguage);
    activeLanguage = language;
    const [activeView, setActiveView] = useState("overview");
    const [portfolio, setPortfolio] = useState(null);
    const [filters, setFilters] = useState({
      tenant_id: "",
      management_group: "",
      subsidiary: "",
      subscription: "",
      environment: "",
      region: "",
      tier: ""
    });
    const [question, setQuestion] = useState("");
    const [questionOptions, setQuestionOptions] = useState([]);
    const [savingQuestion, setSavingQuestion] = useState(false);
    const [questionStatus, setQuestionStatus] = useState("");
    const [response, setResponse] = useState(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [refreshKey, setRefreshKey] = useState(0);
    const [addingAccount, setAddingAccount] = useState(false);
    const [accountStatus, setAccountStatus] = useState("");
    const [importingAccounts, setImportingAccounts] = useState(false);
    const [importStatus, setImportStatus] = useState("");
    const [catalogStatus, setCatalogStatus] = useState("");
    const [pullingTenantDetails, setPullingTenantDetails] = useState(false);
    const [discoveryStatus, setDiscoveryStatus] = useState(null);
    const [cronDraft, setCronDraft] = useState("0 */6 * * *");
    const [savingSchedule, setSavingSchedule] = useState(false);
    const [hoveredRisk, setHoveredRisk] = useState(null);
    const [investigationHistory, setInvestigationHistory] = useState([]);
    const [savingsAdoption, setSavingsAdoption] = useState(25);
    const [savingsResult, setSavingsResult] = useState(null);
    const [savingsBusy, setSavingsBusy] = useState(false);
    const [findingsData, setFindingsData] = useState(null);
    const [findingCategory, setFindingCategory] = useState("All");
    const [dataHealth, setDataHealth] = useState(null);
    const [connectorAction, setConnectorAction] = useState("");
    const [postureSelection, setPostureSelection] = useState("");
    const [postureData, setPostureData] = useState(null);
    const [postureBusy, setPostureBusy] = useState(false);
    const [accountSelections, setAccountSelections] = useState({});
    const [notificationBusy, setNotificationBusy] = useState({});
    const [notificationStatuses, setNotificationStatuses] = useState({});
    const [accountDraft, setAccountDraft] = useState({
      name: "",
      tenant_id: "",
      management_group: "",
      subscription: "",
      environment: "",
      subsidiary: "",
      region: "",
      tier: ""
    });

    const queryString = useMemo(() => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => value && params.set(key, value));
      return params.toString();
    }, [filters]);

    useEffect(() => {
      activeLanguage = language;
      localStorage.setItem("storage-intelligence-language", language);
      document.documentElement.lang = language;
      document.title = translateText("Storage Atlas", language);
      setQuestion((current) =>
        current ? translateText(window.StorageI18n.canonicalize(current), language) : current
      );
    }, [language]);

    useEffect(() => {
      fetch("/api/questions")
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Question library could not be loaded"));
          return body;
        }))
        .then((body) => {
          setQuestionOptions(body.questions);
          setQuestion((current) => current || (body.questions[0] ? translateText(body.questions[0].question) : ""));
        })
        .catch((err) => setError(err.message));
    }, []);

    useEffect(() => {
      if (!postureSelection) {
        setPostureData(null);
        return;
      }
      setPostureBusy(true);
      setError("");
      fetch("/api/posture/" + postureSelection + "?" + queryString)
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Posture accounts could not be loaded"));
          return body;
        }))
        .then(setPostureData)
        .catch((err) => setError(err.message))
        .finally(() => setPostureBusy(false));
    }, [postureSelection, queryString, refreshKey]);

    useEffect(() => {
      setError("");
      fetch("/api/portfolio?" + queryString)
        .then((result) => {
          if (!result.ok) throw new Error("Portfolio request failed (" + result.status + ")");
          return result.json();
        })
        .then(setPortfolio)
        .catch((err) => setError(err.message));
    }, [queryString, refreshKey]);

    useEffect(() => {
      if (!portfolio || !portfolio.permissions.admin) return;
      fetch("/api/admin/discovery/status")
        .then((result) => result.json())
        .then((body) => {
          setDiscoveryStatus(body);
          if (body.schedule) setCronDraft(body.schedule);
        })
        .catch(() => {});
    }, [portfolio && portfolio.permissions.admin]);

    useEffect(() => {
      if (activeView !== "findings") return;
      fetch("/api/findings?" + queryString)
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Findings could not be loaded"));
          return body;
        }))
        .then(setFindingsData)
        .catch((err) => setError(err.message));
    }, [activeView, queryString, refreshKey]);

    useEffect(() => {
      if (activeView !== "health") return;
      loadDataHealth();
    }, [activeView, queryString, refreshKey]);

    useEffect(() => {
      if (activeView === "savings") runSavingsSimulation();
    }, [activeView, queryString]);

    function updateFilter(key, value) {
      setFilters(Object.assign({}, filters, { [key]: value }));
    }

    function updateAccountDraft(key, value) {
      setAccountDraft(Object.assign({}, accountDraft, { [key]: value }));
    }

    function selectedIds(surface, visibleIds) {
      const selected = accountSelections[surface] || [];
      if (!visibleIds) return selected;
      const visible = new Set(visibleIds);
      return selected.filter((accountId) => visible.has(accountId));
    }

    function setNotificationStatus(surface, tone, message) {
      setNotificationStatuses((current) => Object.assign({}, current, {
        [surface]: { tone: tone, message: message }
      }));
    }

    function toggleAccountSelection(surface, accountId, checked) {
      setAccountSelections((current) => {
        const next = new Set(current[surface] || []);
        if (checked && next.size >= 100 && !next.has(accountId)) {
          setNotificationStatus(surface, "error", "Select no more than 100 accounts per notification.");
          return current;
        }
        if (checked) next.add(accountId);
        else next.delete(accountId);
        setNotificationStatuses((statuses) => Object.assign({}, statuses, { [surface]: null }));
        return Object.assign({}, current, { [surface]: Array.from(next) });
      });
    }

    function notifyProjectOwners(surface, accountIds) {
      if (!accountIds.length || notificationBusy[surface]) return;
      setNotificationBusy((current) => Object.assign({}, current, { [surface]: true }));
      setNotificationStatuses((current) => Object.assign({}, current, { [surface]: null }));
      fetch("/api/notifications/project-owners", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_ids: accountIds })
      })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Project-owner notification could not be sent"));
          return body;
        }))
        .then((body) => {
          setAccountSelections((current) => Object.assign({}, current, { [surface]: [] }));
          setNotificationStatus(
            surface,
            "success",
            "Notification accepted for " + body.account_count + " account(s) to " + body.recipient + ". Operation " + body.operation_id + "."
          );
        })
        .catch((err) => setNotificationStatus(surface, "error", err.message))
        .finally(() => setNotificationBusy((current) => Object.assign({}, current, { [surface]: false })));
    }

    function addAccount(event) {
      event.preventDefault();
      setAddingAccount(true);
      setAccountStatus("");
      setError("");
      fetch("/api/accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(accountDraft)
      })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Storage account could not be added"));
          return body;
        }))
        .then((body) => {
          setAccountStatus("Added " + body.account.name + " to the pilot inventory.");
          setAccountDraft(Object.assign({}, accountDraft, { name: "" }));
          setRefreshKey((value) => value + 1);
        })
        .catch((err) => setError(err.message))
        .finally(() => setAddingAccount(false));
    }

    function importSpreadsheet(event) {
      event.preventDefault();
      const form = event.currentTarget;
      setImportingAccounts(true);
      setImportStatus("");
      setError("");
      fetch("/api/accounts/import", {
        method: "POST",
        body: new FormData(form)
      })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Spreadsheet could not be imported"));
          return body;
        }))
        .then((body) => {
          setImportStatus("Imported " + body.imported + " storage accounts into the pilot inventory.");
          form.reset();
          setRefreshKey((value) => value + 1);
        })
        .catch((err) => setError(err.message))
        .finally(() => setImportingAccounts(false));
    }

    function addCatalogValue(event, dimension) {
      event.preventDefault();
      const form = event.currentTarget;
      const value = new FormData(form).get("value");
      setCatalogStatus("");
      setError("");
      fetch("/api/catalog/" + dimension, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: value })
      })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Selection value could not be added"));
          return body;
        }))
        .then((body) => {
          setCatalogStatus("Added " + body.value + " to " + body.dimension + ".");
          form.reset();
          setRefreshKey((value) => value + 1);
        })
        .catch((err) => setError(err.message));
    }

    function pollDiscoveryStatus() {
      fetch("/api/admin/discovery/status")
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Discovery status could not be loaded"));
          return body;
        }))
        .then((body) => {
          setDiscoveryStatus(body);
          if (body.status === "running") {
            setTimeout(pollDiscoveryStatus, 2500);
          } else {
            setPullingTenantDetails(false);
            if (body.status === "completed") setRefreshKey((value) => value + 1);
          }
        })
        .catch((err) => {
          setPullingTenantDetails(false);
          setError(err.message);
        });
    }

    function pullTenantStorageDetails() {
      setPullingTenantDetails(true);
      setDiscoveryStatus({ status: "starting" });
      setError("");
      fetch("/api/admin/discovery/pull", { method: "POST" })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Tenant-wide discovery could not be started"));
          return body;
        }))
        .then((body) => {
          setDiscoveryStatus(body);
          setTimeout(pollDiscoveryStatus, 1000);
        })
        .catch((err) => {
          setPullingTenantDetails(false);
          setError(err.message);
        });
    }

    function saveDiscoverySchedule(event) {
      event.preventDefault();
      setSavingSchedule(true);
      setError("");
      fetch("/api/admin/discovery/schedule", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cron: cronDraft })
      })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Discovery schedule could not be saved"));
          return body;
        }))
        .then((body) => {
          setDiscoveryStatus(body);
          setCronDraft(body.schedule);
        })
        .catch((err) => setError(err.message))
        .finally(() => setSavingSchedule(false));
    }

    function runSavingsSimulation() {
      setSavingsBusy(true);
      setError("");
      const activeFilters = {};
      Object.entries(filters).forEach(([key, value]) => value && (activeFilters[key] = value));
      fetch("/api/savings/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ adoption_pct: savingsAdoption, filters: activeFilters })
      })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Savings simulation failed"));
          return body;
        }))
        .then(setSavingsResult)
        .catch((err) => setError(err.message))
        .finally(() => setSavingsBusy(false));
    }

    function loadDataHealth() {
      return fetch("/api/data-health?" + queryString)
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Data health could not be loaded"));
          return body;
        }))
        .then(setDataHealth)
        .catch((err) => setError(err.message));
    }

    function enableConnector(connectorKey) {
      setConnectorAction(connectorKey);
      setError("");
      fetch("/api/admin/connectors/" + connectorKey + "/enable", { method: "POST" })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Connector could not be enabled"));
          return body;
        }))
        .then(loadDataHealth)
        .catch((err) => setError(err.message))
        .finally(() => setConnectorAction(""));
    }

    function runConnector(source) {
      if (source.key === "azure-cli") {
        pullTenantStorageDetails();
        return;
      }
      setConnectorAction(source.key);
      setError("");
      fetch("/api/admin/connectors/" + source.key + "/run", { method: "POST" })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Connector run failed"));
          return body;
        }))
        .then(loadDataHealth)
        .catch((err) => setError(err.message))
        .finally(() => setConnectorAction(""));
    }

    function ask(event) {
      event.preventDefault();
      setBusy(true);
      setError("");
      const activeFilters = {};
      Object.entries(filters).forEach(([key, value]) => value && (activeFilters[key] = value));
      fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: window.StorageI18n.canonicalize(question), filters: activeFilters })
      })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(body.detail || "Query failed");
          return body;
        }))
        .then((body) => {
          setResponse(body);
          setInvestigationHistory((history) => [
            {
              question: question,
              tool: body.tool,
              confidence: body.confidence.level,
              timestamp: body.timestamp
            },
            ...history
          ].slice(0, 8));
        })
        .catch((err) => setError(err.message))
        .finally(() => setBusy(false));
    }

    function saveInvestigationQuestion() {
      setSavingQuestion(true);
      setQuestionStatus("");
      setError("");
      fetch("/api/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question })
      })
        .then((result) => result.json().then((body) => {
          if (!result.ok) throw new Error(apiError(body, "Question could not be saved"));
          return body;
        }))
        .then((body) => {
          setQuestionOptions(body.questions);
          setQuestion(translateText(body.saved.question));
          setQuestionStatus("Saved to the investigation question library.");
        })
        .catch((err) => setError(err.message))
        .finally(() => setSavingQuestion(false));
    }

    if (!portfolio && !error) return e("div", { className: "loading" }, "Loading the synthetic estate...");
    const summary = portfolio ? portfolio.summary : {};
    const bars = portfolio ? portfolio.risks : [];
    const regionLabels = portfolio ? portfolio.catalog.region_labels : {};
    const tenantLabels = portfolio ? portfolio.catalog.tenant_labels : {};
    const managementGroupLabels = portfolio ? portfolio.catalog.management_group_labels : {};
    const availableRegions = portfolio ? portfolio.filters.regions.filter((region) => !portfolio.catalog.tracked_regions.includes(region)) : [];
    const visibleViews = applicationViews.filter((view) => view.id !== "admin" || (portfolio && portfolio.permissions.admin));
    const currentView = applicationViews.find((view) => view.id === activeView) || applicationViews[0];
    const filteredFindings = findingsData
      ? findingsData.findings.filter((finding) => findingCategory === "All" || finding.category === findingCategory)
      : [];
    const findingCategoryOptions = [
      { key: "All", label: "Total Findings" },
      { key: "Data freshness", label: "Data Freshness" },
      { key: "Growth anomaly", label: "Growth Anomaly" },
      { key: "Risk", label: "Risk" },
      { key: "Savings action", label: "Savings Action" }
    ];
    const selectedFindingLabel = findingCategoryOptions.find((item) => item.key === findingCategory).label;
    const riskDistribution = riskTypes.map((riskType) => ({
      riskType: riskType,
      count: bars.filter((row) => dominantRisk(row).key === riskType.key).length
    }));
    let pieCursor = 0;
    const pieStops = riskDistribution.filter((item) => item.count > 0).map((item) => {
      const start = pieCursor;
      pieCursor += item.count / Math.max(1, bars.length) * 100;
      return item.riskType.color + " " + start + "% " + pieCursor + "%";
    });
    const pieBackground = pieStops.length ? "conic-gradient(" + pieStops.join(",") + ")" : "var(--panel-2)";
    const largestRisk = riskDistribution.reduce(
      (largest, item) => item.count > largest.count ? item : largest,
      riskDistribution[0]
    );

    function updateHoveredRisk(event) {
      const bounds = event.currentTarget.getBoundingClientRect();
      const x = event.clientX - bounds.left - bounds.width / 2;
      const y = event.clientY - bounds.top - bounds.height / 2;
      const distance = Math.sqrt(x * x + y * y);
      if (distance < bounds.width * .27 || distance > bounds.width / 2) {
        setHoveredRisk(null);
        return;
      }
      const angle = (Math.atan2(y, x) * 180 / Math.PI + 450) % 360;
      let cursor = 0;
      const match = riskDistribution.find((item) => {
        cursor += item.count / Math.max(1, bars.length) * 360;
        return angle <= cursor;
      });
      setHoveredRisk(match || null);
    }

    return e("div", { className: "shell" },
      e("aside", { className: "sidebar" },
        e("div", { className: "brand" },
          e(AvidunixuserLogo),
          e("div", { className: "brand-copy" },
            e("div", { className: "product-name" }, "Storage Atlas")
          )
        ),
        e("div", { className: "environment" }, "Synthetic pilot · Read only"),
        e("nav", { className: "nav" },
          visibleViews.map((view) =>
            e("button", {
              className: "nav-item" + (activeView === view.id ? " active" : ""),
              key: view.id,
              onClick: () => setActiveView(view.id)
            }, e(NavIcon, { view: view }), e("span", null, view.label))
          )
        ),
        e("div", { className: "sidebar-footer" },
          e("div", { className: "sidebar-note" }, "Evidence-first recommendations", e("br"), "No estate mutations · Entra protected"),
          e("div", { className: "copyright" }, "© 2026 Avidunixuser. All rights reserved."),
          e("div", { className: "authored" }, "Authored by nrp"),
          e("div", { className: "powered-logos", "aria-label": "Powered by Microsoft Azure and Azure AI Foundry" },
            e("span", { className: "powered-label" }, "Powered by"),
            e(MicrosoftMiniLogo),
            e(AzureMiniLogo),
            e(FoundryMiniLogo)
          ),
          e("div", {
            className: "protocol-enabled",
            role: "status",
            "aria-label": "MCP and A2A protocols enabled"
          }, "MCP & A2A Enabled")
        )
      ),
      e("main", { className: "main" },
        e("header", { className: "topbar" },
          e("div", null,
            e("div", { className: "mobile-brand" }, e(AvidunixuserLogo), e("span", { className: "product-name" }, "Storage Atlas")),
            e("div", { className: "eyebrow" }, currentView.eyebrow),
            e("h1", null, currentView.title),
            e("p", { className: "subtitle" }, currentView.subtitle)
          ),
          e("div", { className: "topbar-actions" },
            e("label", { className: "language-switch" },
              e("span", null, "Language"),
              e("select", {
                value: language,
                onChange: (event) => setLanguage(event.target.value),
                "aria-label": "Select language"
              },
                e("option", { value: "en" }, "English"),
                e("option", { value: "es" }, "Spanish")
              )
            ),
            e(EntraAuthenticatedMark)
          )
        ),
        e("nav", { className: "mobile-view-nav", "aria-label": "Application views" },
          visibleViews.map((view) =>
            e("button", {
              className: "chip" + (activeView === view.id ? " selected" : ""),
              key: view.id,
              onClick: () => setActiveView(view.id)
            }, e(NavIcon, { view: view }), e("span", null, view.label))
          )
        ),
        portfolio && e("section", { className: "hierarchy-context", "aria-label": "Current enterprise hierarchy scope" },
          e("span", null, portfolio.hierarchy.tenant_count + " tenants"),
          e("span", null, portfolio.hierarchy.management_group_count + " management groups"),
          e("span", null, portfolio.hierarchy.subsidiary_count + " subsidiaries"),
          e("span", null, portfolio.hierarchy.subscription_count + " subscriptions"),
          e("span", null, portfolio.hierarchy.environment_count + " environments")
        ),
        e("section", { className: "filters" },
          e(Filter, { label: "tenant IDs", items: portfolio ? portfolio.filters.tenant_ids : [], labels: tenantLabels, value: filters.tenant_id, onChange: (v) => updateFilter("tenant_id", v) }),
          e(Filter, { label: "management groups", items: portfolio ? portfolio.filters.management_groups : [], labels: managementGroupLabels, value: filters.management_group, onChange: (v) => updateFilter("management_group", v) }),
          e(Filter, { label: "environments", items: portfolio ? portfolio.filters.environments : [], value: filters.environment, onChange: (v) => updateFilter("environment", v) }),
          e(Filter, { label: "subsidiaries / business units", items: portfolio ? portfolio.filters.subsidiaries : [], value: filters.subsidiary, onChange: (v) => updateFilter("subsidiary", v) }),
          e(Filter, { label: "subscriptions", items: portfolio ? portfolio.filters.subscriptions : [], value: filters.subscription, onChange: (v) => updateFilter("subscription", v) }),
          e(Filter, { label: "regions", items: portfolio ? portfolio.filters.regions : [], labels: regionLabels, value: filters.region, onChange: (v) => updateFilter("region", v) }),
          e(Filter, { label: "tiers", items: portfolio ? portfolio.filters.tiers : [], value: filters.tier, onChange: (v) => updateFilter("tier", v) }),
          e("button", { className: "ghost", onClick: () => setFilters({ tenant_id: "", management_group: "", subsidiary: "", subscription: "", environment: "", region: "", tier: "" }) }, "Reset")
        ),
        error && e("div", { className: "error" }, error),
        portfolio && e(React.Fragment, null,
          activeView === "overview" && e(React.Fragment, null,
            e("section", { className: "metrics" },
            e(Metric, { label: "Storage accounts", value: formatNumber(summary.account_count), note: "Scoped estate" }),
            e(Metric, { label: "Capacity", value: formatNumber(summary.capacity_tb, "tb"), note: formatNumber(summary.weighted_growth_30d_pct, "pct") + " weighted growth" }),
            e(Metric, { label: "Monthly cost", value: formatNumber(summary.monthly_cost_usd, "money"), note: "Modeled synthetic spend" }),
            e(Metric, { label: "Savings opportunity", value: formatNumber(summary.potential_monthly_savings_usd, "money"), note: "25% eligible adoption" }),
            e(Metric, {
              label: "At-risk accounts",
              value: formatNumber(summary.at_risk_accounts),
              note: "Score ≥ " + portfolio.risk_threshold + " · " + summary.stale_accounts + " stale records"
            })
          ),
          e("section", { className: "panel catalog-management" },
            e("div", { className: "panel-head" },
              e("div", { className: "panel-title" }, "Manage selection lists"),
              e("div", { className: "panel-meta" }, "Pilot catalog only")
            ),
            e("div", { className: "catalog-grid" },
              e("form", { className: "catalog-form", onSubmit: (event) => addCatalogValue(event, "tenants") },
                e("label", { className: "account-field" },
                  e("span", { className: "field-label" }, "New tenant ID"),
                  e("input", { name: "value", required: true, maxLength: 36, placeholder: "00000000-0000-4000-8000-000000000000", "aria-label": "New tenant ID" })
                ),
                e("button", { className: "ghost catalog-button" }, "Add tenant")
              ),
              e("form", { className: "catalog-form", onSubmit: (event) => addCatalogValue(event, "management-groups") },
                e("label", { className: "account-field" },
                  e("span", { className: "field-label" }, "New management group"),
                  e("input", { name: "value", required: true, maxLength: 100, placeholder: "mg-global-data", "aria-label": "New management group" })
                ),
                e("button", { className: "ghost catalog-button" }, "Add management group")
              ),
              e("form", { className: "catalog-form", onSubmit: (event) => addCatalogValue(event, "subscriptions") },
                e("label", { className: "account-field" },
                  e("span", { className: "field-label" }, "New subscription"),
                  e("input", { name: "value", required: true, maxLength: 100, placeholder: "new-subscription", "aria-label": "New subscription" })
                ),
                e("button", { className: "ghost catalog-button" }, "Add subscription")
              ),
              e("form", { className: "catalog-form", onSubmit: (event) => addCatalogValue(event, "subsidiaries") },
                e("label", { className: "account-field" },
                  e("span", { className: "field-label" }, "New subsidiary / business unit"),
                  e("input", { name: "value", required: true, maxLength: 100, placeholder: "Avidunixuser Labs", "aria-label": "New subsidiary or business unit" })
                ),
                e("button", { className: "ghost catalog-button" }, "Add subsidiary")
              ),
              e("form", { className: "catalog-form", onSubmit: (event) => addCatalogValue(event, "regions") },
                e("label", { className: "account-field" },
                  e("span", { className: "field-label" }, "Azure region"),
                  e("select", { name: "value", required: true, "aria-label": "New Azure region" },
                    e("option", { value: "" }, "Select an Azure region"),
                    availableRegions.map((region) => e("option", { value: region, key: region }, regionLabels[region] + " (" + region + ")"))
                  )
                ),
                e("button", { className: "ghost catalog-button" }, "Add region")
              )
            ),
            e("div", { className: "account-note" }, "Selection-list changes are in-memory pilot metadata and never create Azure resources."),
            catalogStatus && e("div", { className: "success" }, catalogStatus)
          ),
          portfolio.platform_accounts.length > 0 && e("section", { className: "panel platform-panel" },
            e("div", { className: "panel-head" },
              e("div", { className: "panel-title" }, "Platform-linked storage accounts"),
              e("div", { className: "notification-panel-meta" },
                e("div", { className: "panel-meta" },
                  portfolio.platform_accounts.length.toLocaleString() + " scoped accounts · Databricks · Fabric · SAP · ADF · SFTP · App Insights · Functions · Log Analytics"
                ),
                e(NotificationToolbar, {
                  selectedIds: selectedIds("platform", portfolio.platform_accounts.map((account) => account.account_id)),
                  busy: notificationBusy.platform,
                  status: notificationStatuses.platform,
                  onNotify: (ids) => notifyProjectOwners("platform", ids)
                })
              )
            ),
            e("div", {
              className: "platform-account-grid platform-account-scroll",
              role: "region",
              tabIndex: 0,
              "aria-label": "Platform-linked storage accounts"
            },
              portfolio.platform_accounts.map((account) =>
                e("div", {
                  className: "platform-account" + (selectedIds("platform").includes(account.account_id) ? " selected" : ""),
                  key: account.account_id
                },
                  e(AccountCheckbox, {
                    name: account.name,
                    checked: selectedIds("platform").includes(account.account_id),
                    onChange: (checked) => toggleAccountSelection("platform", account.account_id, checked)
                  }),
                  e("div", { className: "platform-account-title" },
                    e("span", { className: "platform-logos" },
                      account.databricks_workspace && e(DatabricksLogo),
                      account.fabric_lakehouse && e(LakehouseLogo),
                      account.sap_system && e(SapLogo),
                      account.azure_data_factory && e(DataFactoryLogo),
                      account.sftp_enabled && e(SftpLogo),
                      account.application_insights_resource && e(AppInsightsLogo),
                      account.azure_function_app && e(FunctionAppLogo),
                      account.log_analytics_workspace && e(LogAnalyticsLogo),
                      !hasPlatformClassification(account) && e(AccountClassificationLogo, { account: account })
                    ),
                    e("span", null, account.name)
                  ),
                  e("div", { className: "risk-sub" }, tenantLabels[account.tenant_id] + " · " + (managementGroupLabels[account.management_group] || account.management_group)),
                  e("div", { className: "risk-sub" }, account.subsidiary + " · " + account.subscription + " · " + account.environment + " · " + account.region + " · " + account.tier),
                  e("div", { className: "platform-links" },
                    account.databricks_workspace && e("span", { className: "platform-link databricks-link" }, account.databricks_workspace),
                    account.fabric_lakehouse && e("span", { className: "platform-link lakehouse-link" }, account.fabric_lakehouse),
                    account.sap_system && e("span", { className: "platform-link sap-link" }, account.sap_system),
                    account.azure_data_factory && e("span", { className: "platform-link data-factory-link" }, account.azure_data_factory),
                    account.sftp_enabled && e("span", { className: "platform-link sftp-link" }, "SFTP enabled"),
                    account.application_insights_resource && e("span", { className: "platform-link app-insights-link" }, account.application_insights_resource),
                    account.azure_function_app && e("span", { className: "platform-link function-app-link" },
                      e(FunctionAppLogo),
                      e("span", null, account.azure_function_app)
                    ),
                    account.log_analytics_workspace && e("span", { className: "platform-link log-analytics-link" },
                      e(LogAnalyticsLogo),
                      e("span", null, account.log_analytics_workspace)
                    ),
                    account.managed_identity_enabled === true && e("span", { className: "platform-link managed-identity-link enabled" }, "Managed identity enabled"),
                    account.managed_identity_enabled === false && e("span", { className: "platform-link managed-identity-link disabled" }, "Managed identity disabled")
                  )
                )
              )
            )
          ),
          e("section", { className: "panel account-onboarding" },
            e("div", { className: "panel-head" },
              e("div", { className: "panel-title" }, "Add storage account"),
              e("div", { className: "panel-meta" }, "Pilot inventory only")
            ),
            e("form", { className: "account-form", onSubmit: addAccount },
              e("label", { className: "account-field account-name" },
                e("span", { className: "field-label" }, "Account name"),
                e("input", {
                  value: accountDraft.name,
                  required: true,
                  minLength: 3,
                  maxLength: 24,
                  pattern: "[a-z0-9]+",
                  placeholder: "stnewaccount01",
                  onChange: (event) => updateAccountDraft("name", event.target.value.toLowerCase().replace(/[^a-z0-9]/g, "")),
                  "aria-label": "Account name"
                })
              ),
              e(ChoiceSelect, { label: "Tenant ID", items: portfolio.filters.tenant_ids, labels: tenantLabels, value: accountDraft.tenant_id, onChange: (value) => updateAccountDraft("tenant_id", value) }),
              e(ChoiceSelect, { label: "Management group", items: portfolio.filters.management_groups, labels: managementGroupLabels, value: accountDraft.management_group, onChange: (value) => updateAccountDraft("management_group", value) }),
              e(ChoiceSelect, { label: "Subscription", items: portfolio.filters.subscriptions, value: accountDraft.subscription, onChange: (value) => updateAccountDraft("subscription", value) }),
              e(ChoiceSelect, { label: "Environment", items: portfolio.filters.environments, value: accountDraft.environment, onChange: (value) => updateAccountDraft("environment", value) }),
              e(ChoiceSelect, { label: "Subsidiary / business unit", items: portfolio.filters.subsidiaries, value: accountDraft.subsidiary, onChange: (value) => updateAccountDraft("subsidiary", value) }),
              e(ChoiceSelect, { label: "Region", items: portfolio.filters.regions, labels: regionLabels, value: accountDraft.region, onChange: (value) => updateAccountDraft("region", value) }),
              e(ChoiceSelect, { label: "Tier", items: portfolio.filters.tiers, value: accountDraft.tier, onChange: (value) => updateAccountDraft("tier", value) }),
              e("button", { className: "ask add-account-button", disabled: addingAccount }, addingAccount ? "Adding…" : "Add account")
            ),
            e("div", { className: "account-note" }, "This tracks an account in the synthetic pilot. It never provisions or changes an Azure resource."),
            accountStatus && e("div", { className: "success" }, accountStatus),
            e("div", { className: "bulk-import" },
              e("div", { className: "bulk-import-copy" },
                e("div", { className: "panel-title" },
                  "Import account spreadsheet",
                  " ",
                  e("em", { className: "airgap-import-qualifier" }, "(for AIRGAP Accounts ONLY, if applicable)")
                ),
                e("a", {
                  className: "sample-spreadsheet-link",
                  href: "/static/Sample.xlsx",
                  download: "Sample.xlsx"
                }, "Sample.xlsx")
              ),
              e("form", { className: "import-form", onSubmit: importSpreadsheet },
                e("input", {
                  className: "file-input",
                  type: "file",
                  name: "spreadsheet",
                  accept: ".xlsx,.csv",
                  required: true,
                  "aria-label": "AIRGAP account spreadsheet"
                }),
                e("button", { className: "ghost import-button", disabled: importingAccounts }, importingAccounts ? "Importing…" : "Import spreadsheet")
              )
            ),
            importStatus && e("div", { className: "success" }, importStatus)
          ),
            e("section", { className: "panel risk-overview-panel" },
              e("div", { className: "panel-head" },
                e("div", { className: "panel-title" }, "Risk concentration and account findings"),
                e("div", { className: "notification-panel-meta" },
                  e("div", { className: "panel-meta" }, bars.length + " accounts · score ≥ " + portfolio.risk_threshold),
                  e(NotificationToolbar, {
                    selectedIds: selectedIds("risk", bars.map((row) => row.account_id)),
                    busy: notificationBusy.risk,
                    status: notificationStatuses.risk,
                    onNotify: (ids) => notifyProjectOwners("risk", ids)
                  })
                )
              ),
              e("div", { className: "risk-pie-layout" },
                e("div", {
                  className: "risk-pie",
                  style: { background: pieBackground },
                  role: "img",
                  tabIndex: 0,
                  "aria-label": "At-risk account distribution by dominant risk type. Hover a segment for details.",
                  onMouseMove: updateHoveredRisk,
                  onMouseLeave: () => setHoveredRisk(null),
                  onFocus: () => setHoveredRisk(largestRisk),
                  onBlur: () => setHoveredRisk(null)
                },
                  e("div", { className: "risk-pie-center" },
                    e("strong", null, bars.length),
                    e("span", null, "at risk")
                  )
                ),
                e("div", { className: "risk-pie-side" },
                  e("div", { className: "risk-pie-legend" },
                    riskDistribution.map((item) =>
                      e("div", {
                        className: "risk-pie-legend-row" + (hoveredRisk && hoveredRisk.riskType.key === item.riskType.key ? " active" : ""),
                        key: item.riskType.key,
                        title: item.riskType.description + " · " + item.riskType.colorName
                      },
                        e("span", { className: "risk-type-dot", style: { background: riskTypeColors[item.riskType.key] } }),
                        e("span", { className: "risk-legend-label" }, item.riskType.label),
                        e("span", { className: "risk-legend-value" },
                          item.count + " · " + Math.round(item.count / Math.max(1, bars.length) * 100) + "%"
                        )
                      )
                    )
                  ),
                  e("div", { className: "risk-hover-description", role: "status", "aria-live": "polite" },
                    hoveredRisk
                      ? e(React.Fragment, null,
                          e("div", { className: "risk-hover-title" },
                            e("span", { className: "risk-type-dot", style: { background: hoveredRisk.riskType.color } }),
                            e("strong", null, hoveredRisk.riskType.label)
                          ),
                          e("p", null, hoveredRisk.riskType.description),
                          e("span", null,
                            hoveredRisk.count + " accounts · " +
                            Math.round(hoveredRisk.count / Math.max(1, bars.length) * 100) + "%"
                          )
                        )
                      : e("span", { className: "risk-hover-hint" }, "Hover over a pie segment to view its risk description.")
                  )
                )
              ),
              e("div", { className: "risk-account-heading" },
                e("span", null, "All at-risk accounts"),
                e("span", { className: "panel-meta" }, "Select an account to inspect its findings")
              ),
              e("div", { className: "risk-account-list risk-scroll" }, bars.map((row) => {
                const riskType = dominantRisk(row);
                return e("div", {
                  className: "risk-account-selectable" + (selectedIds("risk").includes(row.account_id) ? " selected" : ""),
                  key: row.account_id
                },
                  e(AccountCheckbox, {
                    name: row.name,
                    checked: selectedIds("risk").includes(row.account_id),
                    onChange: (checked) => toggleAccountSelection("risk", row.account_id, checked)
                  }),
                  e("details", { className: "risk-account-row" },
                    e("summary", { className: "risk-account-summary" },
                      e("div", { className: "risk-account-name" },
                        e("span", { className: "risk-type-dot", style: { background: riskTypeColors[riskType.key] } }),
                        e("div", null,
                          e("span", null, row.name),
                          e("div", { className: "row-hierarchy" }, row.management_group + " · " + row.subsidiary + " · " + row.subscription + " · " + row.environment)
                        )
                      ),
                      e("span", { className: "risk-account-type" }, riskType.label),
                      e("span", {
                        className: "risk-account-score" + (row.score >= 70 ? " high" : ""),
                        "aria-label": "Overall weighted risk score " + row.score + " out of 100"
                      }, row.score + "/100"),
                      e("span", { className: "risk-account-toggle", "aria-hidden": "true" }, "›")
                    ),
                    e("div", { className: "risk-account-details" },
                      e("div", { className: "risk-account-detail-title" }, "Risk component scores"),
                      e("div", { className: "risk-component-grid" },
                        riskTypes.map((component) =>
                          e("div", { className: "risk-component", key: component.key },
                            e("span", { className: "risk-type-dot", style: { background: component.color } }),
                            e("span", null, component.label),
                            e("strong", null, row.components[component.key])
                          )
                        )
                      ),
                      e("div", { className: "risk-account-detail-title" }, "Account findings"),
                      row.risk_factors && row.risk_factors.length
                        ? e("ul", { className: "risk-factor-list" },
                            row.risk_factors.map((factor, index) =>
                              e("li", { key: row.account_id + "-factor-" + index }, factor)
                            )
                          )
                        : e("p", { className: "risk-factor-empty" }, row.reason || "No explicit configuration findings were recorded.")
                    )
                  )
                );
              })),
              bars.length === 0 && e("div", { className: "empty-state" }, "No accounts meet the at-risk threshold in this scope.")
            )
          ),
          activeView === "admin" && portfolio.permissions.admin && e("div", { className: "view-stack" },
            e("section", { className: "panel admin-panel" },
              e("div", { className: "panel-head" },
                e("div", null,
                  e("div", { className: "panel-title" }, "Tenant-wide storage account discovery & Retrieval"),
                  e("div", { className: "account-note" }, "Runs fixed, read-only Azure CLI commands behind the scenes. It enumerates authorized tenants, management-group tags, subsidiaries/business units, subscriptions, storage accounts, regions, tiers, SKUs, and platform relationships without changing Azure resources.")
                ),
                e("span", { className: "admin-badge" }, "Administrator")
              ),
              e("div", { className: "admin-actions" },
                e("button", {
                  className: "ask tenant-pull-button",
                  disabled: pullingTenantDetails,
                  onClick: pullTenantStorageDetails
                }, pullingTenantDetails ? "Retrieving Storage Inventory…" : "Retrieve Storage Inventory"),
                e("form", { className: "schedule-form", onSubmit: saveDiscoverySchedule },
                  e("label", { className: "account-field" },
                    e("span", { className: "field-label" }, "Discovery cron"),
                    e("input", {
                      value: cronDraft,
                      required: true,
                      maxLength: 100,
                      placeholder: "0 */6 * * *",
                      onChange: (event) => setCronDraft(event.target.value),
                      "aria-label": "Discovery cron schedule"
                    })
                  ),
                  e("button", { className: "ghost schedule-button", disabled: savingSchedule }, savingSchedule ? "Saving…" : "Save schedule")
                )
              ),
              e("div", { className: "schedule-copy" },
                "Five-field cron in UTC. Next scheduled run: ",
                e("code", null, discoveryStatus && discoveryStatus.next_run ? discoveryStatus.next_run : "not calculated")
              ),
              e("div", { className: "schedule-copy" },
                "Cosmos DB persistence: ",
                e("code", null,
                  discoveryStatus
                    ? discoveryStatus.persistence + " · " + discoveryStatus.cosmos_database + "/" + discoveryStatus.cosmos_container
                    : "loading"
                )
              ),
              discoveryStatus && e("div", { className: "discovery-status" },
                discoveryStatus.status === "completed"
                  ? "Completed across " + discoveryStatus.tenants + " tenants, " + (discoveryStatus.management_groups || 0) + " management groups, " + (discoveryStatus.subsidiaries || 0) + " subsidiaries, and " + (discoveryStatus.environments || 0) + " environments: " + discoveryStatus.discovered + " discovered, " + discoveryStatus.added + " added, " + discoveryStatus.updated + " refreshed, " + (discoveryStatus.persisted || 0) + " persisted."
                  : discoveryStatus.status === "failed"
                    ? "Failed: " + discoveryStatus.error
                    : "Status: " + discoveryStatus.status
              ),
              discoveryStatus && discoveryStatus.warnings && discoveryStatus.warnings.length > 0 &&
                e("div", { className: "account-note" }, "Discovery warnings: " + discoveryStatus.warnings.join(" "))
            ),
            e("section", { className: "panel" },
              e("div", { className: "panel-head" },
                e("div", { className: "panel-title" }, "Schedule examples"),
                e("div", { className: "panel-meta" }, "UTC")
              ),
              e("div", { className: "schedule-examples", role: "table", "aria-label": "Discovery schedule examples" },
                e("div", { className: "schedule-example-header", role: "row" },
                  e("span", { role: "columnheader" }, "Cron expression"),
                  e("span", { role: "columnheader" }, "Runs")
                ),
                [
                  ["0 */6 * * *", "Every six hours"],
                  ["0 2 * * *", "Daily at 02:00"],
                  ["30 1 * * 1", "Mondays at 01:30"]
                ].map((example) =>
                  e("div", { className: "schedule-example-row", role: "row", key: example[0] },
                    e("code", { className: "schedule-expression", role: "cell" }, example[0]),
                    e("span", { className: "schedule-description", role: "cell" }, example[1])
                  )
                )
              )
            )
          ),
          activeView === "agent" && e("section", { className: "panel assistant" },
            e("div", { className: "panel-head" }, e("div", { className: "panel-title" }, "Ask the read-only intelligence agent"), e("div", { className: "panel-meta" }, "Deterministic tools · cited evidence")),
            e("div", { className: "query-presets" }, questionOptions.map((option) =>
              e("button", {
                className: "chip" + (option.custom ? " custom-question" : ""),
                key: option.question,
                onClick: () => setQuestion(translateText(option.question)),
                title: option.custom ? "Saved question" : "Built-in question"
              }, option.question)
            )),
            e("form", { className: "chat-form", onSubmit: ask },
              e("input", { value: question, onChange: (event) => setQuestion(event.target.value), "aria-label": "Question" }),
              e("button", {
                type: "button",
                className: "ghost save-question",
                disabled: savingQuestion || question.trim().length < 3,
                onClick: saveInvestigationQuestion
              }, savingQuestion ? "Saving…" : "Save question"),
              e("button", { className: "ask", disabled: busy || question.trim().length < 3 }, busy ? "Analyzing…" : "Ask")
            ),
            e("div", { className: "account-note" }, "Type any new storage question, save it once, and it becomes a reusable option for future investigations."),
            questionStatus && e("div", { className: "success" }, questionStatus),
            response && e("div", { className: "response" },
              e("div", { className: "response-answer" }, response.answer),
              response.account_reasons && response.account_reasons.length > 0 && e("div", { className: "response-reasons" },
                e("div", { className: "response-reasons-head" },
                  e("div", { className: "response-reasons-title" }, "Why these accounts were flagged"),
                  e(NotificationToolbar, {
                    selectedIds: selectedIds("agent", response.account_reasons.map((item) => item.account_id)),
                    busy: notificationBusy.agent,
                    status: notificationStatuses.agent,
                    onNotify: (ids) => notifyProjectOwners("agent", ids)
                  })
                ),
                response.account_reasons.map((item) =>
                  e("div", {
                    className: "response-reason-row" + (selectedIds("agent").includes(item.account_id) ? " selected" : ""),
                    key: item.account_id
                  },
                    e(AccountCheckbox, {
                      name: item.name,
                      checked: selectedIds("agent").includes(item.account_id),
                      onChange: (checked) => toggleAccountSelection("agent", item.account_id, checked)
                    }),
                    e("div", null,
                      e("div", { className: "response-reason-account" }, item.name),
                      e("div", { className: "response-reason-hierarchy" }, item.management_group + " · " + item.subsidiary + " · " + item.subscription + " · " + item.environment),
                      e("div", { className: "response-reason-hierarchy" }, (item.project_name || "Project unassigned") + " · last accessed " + (item.last_accessed_date || "unknown") + (item.project_defunct ? " · defunct" : "")),
                      (item.sftp_enabled || item.application_insights_resource) && e("div", { className: "response-reason-hierarchy" }, (item.sftp_enabled ? "SFTP enabled" : "") + (item.sftp_enabled && item.application_insights_resource ? " · " : "") + (item.application_insights_resource || ""))
                    ),
                    e("div", { className: "response-reason-copy" }, item.reason)
                  )
                )
              ),
              e("div", { className: "trust" },
                e("div", { className: "trust-item" },
                  e("div", { className: "trust-label" }, "Scope"),
                  e("div", { className: "trust-value" },
                    response.scope.account_count + " scoped" +
                    (response.scope.analyzed_account_count !== response.scope.account_count ? " · " + response.scope.analyzed_account_count + " analyzed" : "") +
                    " · " + response.scope.tenant_count + " tenants · " + response.scope.management_group_count + " MGs"
                  )
                ),
                e("div", { className: "trust-item" }, e("div", { className: "trust-label" }, "Data as of"), e("div", { className: "trust-value" }, response.data_as_of)),
                e("div", { className: "trust-item" }, e("div", { className: "trust-label" }, "Confidence"), e("div", { className: "trust-value" }, response.confidence.level + " · " + response.confidence.score)),
                e("div", { className: "trust-item" }, e("div", { className: "trust-label" }, "Evidence"), e("div", { className: "trust-value" }, response.evidence.length + " cited accounts"))
              ),
              e("pre", null, JSON.stringify(response.data, null, 2))
            ),
            e("div", { className: "investigation-history" },
              e("div", { className: "panel-head" },
                e("div", { className: "panel-title" }, "Investigation history"),
                e("div", { className: "panel-meta" }, "Latest eight in this session")
              ),
              investigationHistory.length
                ? investigationHistory.map((item, index) =>
                    e("div", { className: "history-row", key: item.timestamp + index },
                      e("div", null,
                        e("div", { className: "history-question" }, item.question),
                        e("div", { className: "risk-sub" }, item.tool + " · " + item.timestamp)
                      ),
                      e("span", { className: "confidence-badge" }, item.confidence)
                    )
                  )
                : e("div", { className: "empty-state" }, "Ask a question to begin an investigation history.")
            )
          ),
          activeView === "savings" && e("div", { className: "view-stack" },
            e("section", { className: "panel savings-controls" },
              e("div", { className: "panel-head" },
                e("div", { className: "panel-title" }, "Tiering adoption"),
                e("div", { className: "panel-meta" }, savingsAdoption + "% of eligible cold data")
              ),
              e("input", {
                className: "savings-slider",
                type: "range",
                min: 1,
                max: 100,
                value: savingsAdoption,
                onChange: (event) => setSavingsAdoption(Number(event.target.value)),
                "aria-label": "Tiering adoption percentage"
              }),
              e("div", { className: "savings-scale" }, e("span", null, "1%"), e("span", null, "50%"), e("span", null, "100%")),
              e("button", { className: "ask simulate-button", disabled: savingsBusy, onClick: runSavingsSimulation },
                savingsBusy ? "Simulating…" : "Run simulation"
              ),
              e("div", { className: "account-note" }, "Savings include modeled retrieval and operation charges. Archive recommendations retain early-deletion and rehydration warnings.")
            ),
            savingsResult && e(React.Fragment, null,
              e("section", { className: "metrics savings-metrics" },
                e(Metric, { label: "Adoption", value: savingsResult.simulation.adoption_pct + "%", note: "Eligible cold data moved" }),
                e(Metric, { label: "Eligible capacity", value: formatNumber(savingsResult.simulation.eligible_tb, "tb"), note: "Modeled for selected scope" }),
                e(Metric, { label: "Monthly savings", value: formatNumber(savingsResult.simulation.net_monthly_savings_usd, "money"), note: "Net of retrieval and operations" }),
                e(Metric, { label: "Confidence", value: savingsResult.confidence.level, note: savingsResult.confidence.reason })
              ),
              e("section", { className: "scenario-grid" },
                savingsResult.scenarios.map((scenario) =>
                  e("div", { className: "panel scenario-card", key: scenario.adoption_pct },
                    e("div", { className: "scenario-adoption" }, scenario.adoption_pct + "% adoption"),
                    e("div", { className: "scenario-value" }, formatNumber(scenario.net_monthly_savings_usd, "money")),
                    e("div", { className: "risk-sub" }, formatNumber(scenario.eligible_tb, "tb") + " eligible")
                  )
                )
              ),
              e("section", { className: "panel" },
                e("div", { className: "panel-head" },
                  e("div", { className: "panel-title" }, "Top savings recommendations"),
                  e("div", { className: "notification-panel-meta" },
                    e("div", { className: "panel-meta" }, "Current state compared with recommended target"),
                    e(NotificationToolbar, {
                      selectedIds: selectedIds("savings", savingsResult.simulation.top_accounts.map((account) => account.account_id)),
                      busy: notificationBusy.savings,
                      status: notificationStatuses.savings,
                      onNotify: (ids) => notifyProjectOwners("savings", ids)
                    })
                  )
                ),
                e("div", { className: "data-table savings-table", role: "table", "aria-label": "Top savings recommendations" },
                  e("div", { className: "savings-table-header", role: "row" },
                    e("span", { "aria-hidden": "true" }),
                    e("span", { role: "columnheader" }, "Account name"),
                    e("span", { role: "columnheader" }, "Current tier"),
                    e("span", { role: "columnheader" }, "Recommended target tier"),
                    e("span", { role: "columnheader" }, "Current size"),
                    e("span", { role: "columnheader" }, "Estimated monthly savings"),
                    e("span", { role: "columnheader" }, "Recommendation risk")
                  ),
                  savingsResult.simulation.top_accounts.map((account) =>
                    e("div", {
                      className: "data-row savings-row" + (selectedIds("savings").includes(account.account_id) ? " selected" : ""),
                      key: account.account_id,
                      role: "row"
                    },
                      e(AccountCheckbox, {
                        name: account.account_id.split("/").pop(),
                        checked: selectedIds("savings").includes(account.account_id),
                        onChange: (checked) => toggleAccountSelection("savings", account.account_id, checked)
                      }),
                      e("span", { className: "data-primary", role: "cell" },
                        e("span", null, account.account_id.split("/").pop()),
                        e("small", { className: "row-hierarchy" }, account.management_group + " · " + account.subsidiary + " · " + account.environment)
                      ),
                      e("span", { role: "cell" }, account.current_tier),
                      e("span", { className: "recommended-tier", role: "cell" }, account.target_tier),
                      e("span", { role: "cell" }, formatNumber(account.current_size_tb, "tb")),
                      e("span", { className: "data-value", role: "cell" }, formatNumber(account.net_monthly_savings_usd, "money")),
                      e("span", { className: account.early_deletion_risk ? "severity high" : "severity low", role: "cell" },
                        account.early_deletion_risk ? "Retention risk" : "Lower risk"
                      )
                    )
                  )
                )
              )
            )
          ),
          activeView === "findings" && e("div", { className: "view-stack" },
            findingsData
              ? e(React.Fragment, null,
                  e("section", { className: "finding-summary-grid" },
                    findingCategoryOptions.map((category) =>
                      e(FindingMetric, {
                        key: category.key,
                        label: category.label,
                        value: category.key === "All" ? findingsData.total : (findingsData.counts[category.key] || 0),
                        note: category.key === "All" ? findingsData.scope.account_count + " scoped accounts" : "Actionable records",
                        active: findingCategory === category.key,
                        onClick: () => setFindingCategory(category.key)
                      })
                    )
                  ),
                  e("section", { className: "panel" },
                    e("div", { className: "panel-head" },
                      e("div", { className: "panel-title" }, selectedFindingLabel),
                      e("div", { className: "notification-panel-meta" },
                        e("div", { className: "panel-meta" }, filteredFindings.length + " findings · scrollable"),
                        e(NotificationToolbar, {
                          selectedIds: selectedIds("findings", filteredFindings.map((finding) => finding.account_id)),
                          busy: notificationBusy.findings,
                          status: notificationStatuses.findings,
                          onNotify: (ids) => notifyProjectOwners("findings", ids)
                        })
                      )
                    ),
                    e("div", { className: "finding-inbox" },
                      filteredFindings.map((finding) =>
                        e("div", {
                          className: "finding-card" + (selectedIds("findings").includes(finding.account_id) ? " selected" : ""),
                          key: finding.id
                        },
                          e("div", { className: "finding-card-head" },
                            e("span", { className: "finding-card-select" },
                              e(AccountCheckbox, {
                                name: finding.title,
                                checked: selectedIds("findings").includes(finding.account_id),
                                onChange: (checked) => toggleAccountSelection("findings", finding.account_id, checked)
                              }),
                              e("span", { className: "finding-category" }, finding.category)
                            ),
                            e("span", { className: "severity " + finding.severity }, finding.severity)
                          ),
                          e("div", { className: "finding-title" }, finding.title),
                          e("div", { className: "finding-summary" }, finding.summary),
                          e("div", { className: "row-hierarchy" }, finding.management_group + " · " + finding.subsidiary + " · " + finding.subscription + " · " + finding.environment),
                          finding.project_name && e("div", { className: "row-hierarchy" }, finding.project_name + " · last accessed " + (finding.last_accessed_date || "unknown")),
                          e("div", { className: "risk-sub" }, finding.account_id)
                        )
                      )
                    )
                  )
                )
              : e("div", { className: "loading" }, "Loading findings…")
          ),
          activeView === "health" && e("div", { className: "view-stack" },
            dataHealth
              ? e(React.Fragment, null,
                  e("section", { className: "source-grid" },
                    dataHealth.sources.map((source) =>
                      e("div", { className: "panel source-card", key: source.name },
                        e("div", { className: "source-card-head" },
                          e("div", { className: "panel-title" }, source.name),
                          e("span", { className: "source-badges" },
                            source.can_enable
                              ? e("button", {
                                  className: "source-status source-status-button disabled",
                                  disabled: connectorAction === source.key,
                                  onClick: () => enableConnector(source.key),
                                  title: "Enable this connector so it can be run"
                                }, connectorAction === source.key ? "Enabling…" : "Disabled")
                              : e("span", { className: "source-status " + source.status.replace(" ", "-") }, source.status),
                            source.mode && e("span", { className: "source-mode" }, source.mode.replace("-", " "))
                          )
                        ),
                        e("div", { className: "source-records" },
                          source.records > 0 ? source.records + " synced" : source.eligible_records + " eligible"
                        ),
                        e("div", { className: "risk-sub" },
                          source.records > 0
                            ? source.eligible_records + " eligible · " + source.detail
                            : "No records synced yet · " + source.detail
                        ),
                        source.can_run && e("div", { className: "source-actions" },
                          e("button", {
                            className: "ask source-action",
                            disabled: connectorAction === source.key || pullingTenantDetails,
                            onClick: () => runConnector(source)
                          }, connectorAction === source.key ? "Running…" : "Run")
                        ),
                        source.last_run && e("div", { className: "source-last-run" }, "Last run: " + source.last_run)
                      )
                    )
                  ),
                  e("section", { className: "metrics health-metrics" },
                    e(Metric, { label: "Freshness", value: dataHealth.summary.freshness_pct + "%", note: dataHealth.summary.fresh_accounts + " fresh accounts" }),
                    e(PostureMetric, { label: "Stale accounts", value: dataHealth.summary.stale_accounts, note: "Inventory >48h or metrics >24h", active: postureSelection === "stale-accounts", onClick: () => setPostureSelection("stale-accounts") }),
                    e(PostureMetric, { label: "Missing lifecycle", value: dataHealth.summary.missing_lifecycle_policy, note: "Configuration quality gap", active: postureSelection === "missing-lifecycle", onClick: () => setPostureSelection("missing-lifecycle") }),
                    e(Metric, { label: "Assumed tier", value: dataHealth.summary.assumed_tier, note: "Access tier unavailable at discovery" })
                  ),
                  e("section", { className: "metrics posture-metrics" },
                    e(PostureMetric, { label: "SAS Key", value: dataHealth.summary.sas_key_accounts, note: "Observed SAS usage", active: postureSelection === "sas-key", onClick: () => setPostureSelection("sas-key") }),
                    e(PostureMetric, { label: "Public Access", value: dataHealth.summary.public_access_accounts, note: "Network or blob public", active: postureSelection === "public-access", onClick: () => setPostureSelection("public-access") }),
                    e(PostureMetric, { label: "No Private Endpoint", value: dataHealth.summary.missing_private_endpoint_accounts, note: "Approved link absent", active: postureSelection === "no-private-endpoint", onClick: () => setPostureSelection("no-private-endpoint") }),
                    e(PostureMetric, { label: "No Service Principal", value: dataHealth.summary.missing_service_principal_access_accounts, note: "Access marker absent", active: postureSelection === "no-service-principal", onClick: () => setPostureSelection("no-service-principal") }),
                    e(PostureMetric, { label: "Managed Identity", value: dataHealth.summary.managed_identity_accounts, note: "Identity-enabled accounts", active: postureSelection === "managed-identity", onClick: () => setPostureSelection("managed-identity") }),
                    e(PostureMetric, { label: "No GRS/GZRS", value: dataHealth.summary.non_geo_redundant_accounts, note: "Resilience exposure", active: postureSelection === "no-grs-gzrs", onClick: () => setPostureSelection("no-grs-gzrs") }),
                    e(PostureMetric, { label: "NSG/ASG linked", value: dataHealth.summary.nsg_asg_linked_accounts, note: "Network group association", active: postureSelection === "nsg-asg-linked", onClick: () => setPostureSelection("nsg-asg-linked") }),
                    e(PostureMetric, { label: "Defunct Projects", value: dataHealth.summary.defunct_project_accounts, note: "Governance cleanup", active: postureSelection === "defunct-projects", onClick: () => setPostureSelection("defunct-projects") }),
                    e(Metric, { label: "No last-access tag", value: dataHealth.summary.missing_last_access_tag, note: "Governance metadata gap" }),
                    e(PostureMetric, { label: "SFTP Enabled", value: dataHealth.summary.sftp_enabled_accounts, note: "File transfer endpoint", active: postureSelection === "sftp-enabled", onClick: () => setPostureSelection("sftp-enabled") }),
                    e(PostureMetric, { label: "AppInsights Data", value: dataHealth.summary.application_insights_accounts, note: "Telemetry-linked storage", active: postureSelection === "app-insights-data", onClick: () => setPostureSelection("app-insights-data") })
                  ),
                  postureSelection && e(PostureDrilldown, {
                    data: postureData,
                    busy: postureBusy,
                    selectedIds: (visibleIds) => selectedIds("posture", visibleIds),
                    notificationBusy: notificationBusy.posture,
                    notificationStatus: notificationStatuses.posture,
                    onToggle: (accountId, checked) => toggleAccountSelection("posture", accountId, checked),
                    onNotify: (ids) => notifyProjectOwners("posture", ids)
                  })
                )
              : e("div", { className: "loading" }, "Loading data health…")
          )
        )
      )
    );
  }

  ReactDOM.createRoot(document.getElementById("root")).render(e(App));
}());
