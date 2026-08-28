from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from . import analytics

REQUIRED_ASSUMPTIONS = [
    "Pilot uses deterministic synthetic records; production connectors are disabled.",
    "Savings include modeled retrieval and operation charges but not negotiated discounts.",
    "Recommendations are read-only and require owner validation before action.",
]


def _account_items(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get("account_id"):
            found.append(value)
        for nested in value.values():
            found.extend(_account_items(nested))
    elif isinstance(value, list):
        for nested in value:
            found.extend(_account_items(nested))
    return found


class IntelligenceEngine:
    def __init__(self, accounts: list[dict[str, Any]]):
        self.accounts = accounts

    def filter(self, filters: dict[str, str] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        allowed = {
            "tenant_id",
            "management_group",
            "subsidiary",
            "business_unit",
            "subscription",
            "environment",
            "region",
            "tier",
            "databricks",
        }
        invalid = set(filters) - allowed
        if invalid:
            raise ValueError(f"Unsupported filters: {', '.join(sorted(invalid))}")
        rows = self.accounts
        for key, value in filters.items():
            if key == "databricks":
                wanted = value.lower() in {"1", "true", "yes"}
                rows = [row for row in rows if bool(row["databricks_workspace"]) is wanted]
            else:
                field = "subsidiary" if key == "business_unit" else key
                rows = [row for row in rows if str(row[field]).lower() == value.lower()]
        return rows

    def answer(self, question: str, filters: dict[str, str] | None = None) -> dict[str, Any]:
        rows = self.filter(filters)
        scope_rows = rows
        normalized = question.lower().strip()
        if not normalized:
            raise ValueError("Question is required")
        spanish_intents = {
            "crecimiento anómalo": " abnormally grew ",
            "crecieron de forma anómala": " abnormally grew ",
            "cuentas en riesgo": " accounts at risk ",
            "deberían preocuparme": " worry risk ",
            "ahorrar": " save tiering ",
            "datos fríos": " cold data tiering ",
            "aumentaron los costos": " cost increase why ",
            "más capacidad": " capacity forecast ",
            "unidad de negocio": " business unit ",
            "subsidiaria": " subsidiary ",
            "grupo de administración": " management group ",
            "inquilino": " tenant ",
            "datos incompletos": " incomplete data stale ",
            "cuentas obsoletas": " stale accounts ",
            "vigencia": " freshness ",
            "ciclo de vida": " lifecycle ",
            "archivo": " archive ",
            "rehidratación": " rehydration ",
            "eliminación anticipada": " early deletion ",
            "transacciones": " transaction ",
            "versiones": " versioning ",
            "instantáneas": " snapshot ",
            "eliminación temporal": " soft delete ",
            "replicación": " replication ",
            "acciones principales": " top five actions ",
            "acceso público": " public access ",
            "punto de conexión privado": " private endpoint ",
            "entidad de servicio": " service principal ",
            "clave compartida": " shared key ",
            "proyecto obsoleto": " defunct project ",
            "último acceso": " last accessed ",
            "entorno": " environment ",
        }
        for spanish, english_terms in spanish_intents.items():
            if spanish in normalized:
                normalized += english_terms
        padded = f" {normalized} "

        tool = "portfolio.summary"
        data: Any = analytics.portfolio_summary(rows)
        answer = "Portfolio summary calculated from the selected account records."

        if "sftp" in normalized:
            rows = [row for row in rows if row.get("sftp_enabled")]
            tool, data, answer = (
                "risk.sftp",
                analytics.security_findings(rows),
                "SFTP-enabled accounts are ranked using transparent access, network, identity, and overall risk factors.",
            )
        elif "application insights" in normalized or "app insights" in normalized:
            rows = [row for row in rows if row.get("application_insights_resource")]
            tool, data, answer = (
                "risk.application_insights_storage",
                analytics.risks(rows),
                "Accounts storing Application Insights data are ranked by transparent security, resilience, and overall risk.",
            )
        elif any(
            term in normalized
            for term in (
                "sas",
                "shared key",
                "public access",
                "publicly accessible",
                "private endpoint",
                "private link",
                "service principal",
                "nsg",
                "asg",
                "security group",
            )
        ):
            tool, data, answer = (
                "risk.security_posture",
                analytics.security_findings(rows),
                "Security posture is ranked from explicit SAS/shared-key, public access, private endpoint, NSG/ASG, and service-principal factors.",
            )
        elif any(
            term in normalized
            for term in ("defunct", "last accessed", "last access", "project tag")
        ):
            tool, data, answer = (
                "risk.project_governance",
                analytics.governance_findings(rows),
                "Project governance risk combines defunct status, project/business-unit tags, and last-accessed age.",
            )
        elif any(term in normalized for term in ("grs", "gzrs", "geo-redund", "geo redund")):
            tool, data, answer = (
                "risk.resilience",
                analytics.resilience_findings(rows),
                "Accounts without GRS/GZRS are ranked by transparent configuration and overall risk.",
            )
        elif "sap" in normalized:
            rows = [row for row in rows if row.get("sap_system")]
            tool, data, answer = (
                "risk.sap",
                analytics.risks(rows),
                "SAP-linked accounts are ranked using the same transparent weighted risk dimensions.",
            )
        elif "data factory" in normalized or "adf" in normalized:
            rows = [row for row in rows if row.get("azure_data_factory")]
            tool, data, answer = (
                "risk.data_factory",
                analytics.risks(rows),
                "Azure Data Factory-linked accounts are ranked by transparent operational and portfolio risk.",
            )
        elif any(term in normalized for term in ("stale", "freshness")) and any(
            term in normalized for term in ("risk", "cost")
        ):
            rows = [
                row
                for row in rows
                if row["inventory_age_hours"] > 48 or row["metrics_age_hours"] > 24
            ]
            tool, data, answer = (
                "risk.stale_accounts",
                analytics.risks(rows),
                "Stale accounts are ranked by transparent weighted risk to prioritize evidence refresh.",
            )
        elif "growth" in normalized and "lifecycle" in normalized:
            rows = [row for row in rows if not row["lifecycle_policy"] and row["growth_30d_pct"] > 0]
            tool, data, answer = (
                "risk.growth_without_lifecycle",
                analytics.risks(rows),
                "Growing accounts without lifecycle coverage are ranked by transparent weighted risk.",
            )
        elif any(term in normalized for term in ("abnormally", "anomal", "grew")):
            tool, data, answer = (
                "capacity.growth_anomalies",
                analytics.growth_anomalies(rows),
                "Accounts are ranked by robust median-absolute-deviation growth score.",
            )
        elif any(term in normalized for term in ("worry", "risk", "at risk")) and "archive" not in normalized:
            tool, data, answer = "risk.rank", analytics.risks(rows), "Risk is ranked using transparent weighted dimensions."
        elif any(term in normalized for term in ("databricks", "small-file", "small file", "external location")):
            tool, data, answer = (
                "databricks.impact",
                analytics.databricks_impact(rows),
                "Databricks impact combines IO, small-file concentration, throttling, and latency.",
            )
        elif any(term in normalized for term in ("tiering", "move to cool", "move to cold", "save")):
            tool, data, answer = (
                "cost.tier_savings",
                analytics.savings_scenarios(rows) if "10%" in normalized or "what-if" in normalized else analytics.tier_savings(rows),
                "Tier savings are net of modeled retrieval and transaction charges.",
            )
        elif "cost" in normalized and any(term in normalized for term in ("increase", "why", "change")):
            tool, data, answer = (
                "cost.explain_change",
                analytics.cost_explanation(rows),
                "Cost movement is decomposed into capacity and operations components.",
            )
        elif any(term in normalized for term in ("capacity", "forecast", "when will")):
            tool, data, answer = (
                "capacity.forecast",
                analytics.capacity_forecasts(rows),
                "Capacity forecasts use bounded compound trends with explicit ranges.",
            )
        elif "management group" in normalized and (
            "business unit" in normalized or "subsidiary" in normalized
        ):
            tool, data, answer = (
                "portfolio.compare_hierarchy",
                {
                    "management_groups": analytics.compare(rows, "management_group"),
                    "subsidiaries": analytics.compare(rows, "subsidiary"),
                },
                "Management groups and subsidiaries are compared using the same deterministic portfolio metrics.",
            )
        elif "environment" in normalized or any(
            f" {term} " in padded for term in ("dev", "qa", "perf", "prod")
        ):
            tool, data, answer = (
                "portfolio.compare_environment",
                analytics.compare(rows, "environment"),
                "Dev, QA, Perf, and Prod environments are compared using the same deterministic portfolio metrics.",
            )
        elif "management group" in normalized:
            tool, data, answer = (
                "portfolio.compare_management_group",
                analytics.compare(rows, "management_group"),
                "Management groups are compared using the same deterministic portfolio metrics.",
            )
        elif "business unit" in normalized or "subsidiary" in normalized:
            tool, data, answer = (
                "portfolio.compare_subsidiary",
                analytics.compare(rows, "subsidiary"),
                "Subsidiaries and business units are compared using the same deterministic portfolio metrics.",
            )
        elif "tenant" in normalized:
            tool, data, answer = (
                "portfolio.compare_tenant",
                analytics.compare(rows, "tenant_id"),
                "Synthetic Avidunixuser tenants are compared using the same deterministic portfolio metrics.",
            )
        elif "subscription" in normalized:
            tool, data, answer = (
                "portfolio.compare_subscription",
                analytics.compare(rows, "subscription"),
                "Subscriptions are compared using the same deterministic portfolio metrics.",
            )
        elif any(term in normalized for term in ("stale", "fresh", "missing inventory", "incomplete data")):
            tool, data, answer = (
                "evidence.freshness",
                analytics.freshness(rows),
                "Stale records are identified from inventory and metrics timestamps.",
            )
        elif "lifecycle" in normalized:
            tool, data, answer = (
                "risk.lifecycle",
                analytics.configuration_findings(rows, "lifecycle"),
                "Accounts without lifecycle policies are ranked by capacity.",
            )
        elif any(term in normalized for term in ("archive", "rehydration", "early-deletion", "early deletion")):
            tool, data, answer = (
                "risk.archive",
                analytics.configuration_findings(rows, "archive"),
                "Archive candidates with access recency risk are surfaced for review.",
            )
        elif "transaction" in normalized:
            tool, data, answer = (
                "cost.transaction_intensity",
                analytics.configuration_findings(rows, "transactions"),
                "Transaction intensity is normalized by stored TB.",
            )
        elif any(term in normalized for term in ("versioning", "snapshot", "soft-delete", "soft delete")):
            tool, data, answer = (
                "capacity.overhead",
                analytics.configuration_findings(rows, "overhead"),
                "Version, snapshot, and soft-delete overhead is combined and ranked.",
            )
        elif "replication" in normalized:
            tool, data, answer = (
                "cost.replication",
                analytics.configuration_findings(rows, "replication"),
                "Low-criticality accounts using geo-redundancy are highlighted.",
            )
        elif any(term in normalized for term in ("top five action", "top 5 action", "where are we wasting")):
            tool, data, answer = (
                "portfolio.top_actions",
                analytics.top_actions(rows),
                "Actions balance modeled savings, risk reduction, and implementation effort.",
            )
        elif "changed since" in normalized:
            tool, data, answer = (
                "portfolio.weekly_delta",
                {
                    "growth_anomalies": analytics.growth_anomalies(rows, 5),
                    "cost_movers": analytics.cost_explanation(rows, 5)["drivers"],
                    "new_stale_accounts": analytics.freshness(rows, 5)["accounts"],
                },
                "Weekly review combines growth, cost, and freshness changes.",
            )

        rows_by_id = {row["account_id"]: row for row in rows}
        returned_accounts: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for item in _account_items(data):
            account_id = str(item["account_id"])
            if account_id in seen_ids:
                continue
            seen_ids.add(account_id)
            source_row = rows_by_id.get(account_id, {})
            returned_accounts.append(
                {
                    "account_id": account_id,
                    "name": item.get("name") or source_row.get("name") or account_id.rsplit("/", 1)[-1],
                    "tenant_id": source_row.get("tenant_id"),
                    "management_group": source_row.get("management_group"),
                    "subsidiary": source_row.get("subsidiary"),
                    "subscription": source_row.get("subscription"),
                    "environment": source_row.get("environment"),
                    "project_name": item.get("project_name") or source_row.get("project_name"),
                    "last_accessed_date": item.get("last_accessed_date")
                    or source_row.get("last_accessed_date"),
                    "project_defunct": item.get("project_defunct")
                    if item.get("project_defunct") is not None
                    else source_row.get("project_defunct"),
                    "risk_factors": item.get("risk_factors") or [],
                    "sftp_enabled": item.get("sftp_enabled")
                    if item.get("sftp_enabled") is not None
                    else source_row.get("sftp_enabled"),
                    "application_insights_resource": item.get("application_insights_resource")
                    or source_row.get("application_insights_resource"),
                    "reason": item.get("reason") or f"Returned by the deterministic {tool} ranking.",
                }
            )

        if returned_accounts:
            evidence = [
                {
                    "id": item["account_id"],
                    "source": rows_by_id[item["account_id"]]["source"],
                    "data_as_of": rows_by_id[item["account_id"]]["data_as_of"],
                    "reason": item["reason"],
                }
                for item in returned_accounts
                if item["account_id"] in rows_by_id
            ]
        else:
            evidence = [
                {
                    "id": row["account_id"],
                    "source": row["source"],
                    "data_as_of": row["data_as_of"],
                }
                for row in rows[:3]
            ]
        confidence = self._confidence(rows)
        return {
            "answer": answer,
            "tool": tool,
            "scope": {
                "filters": filters or {},
                "account_count": len(scope_rows),
                "analyzed_account_count": len(rows),
                "tenant_count": len({row["tenant_id"] for row in scope_rows}),
                "management_group_count": len({row["management_group"] for row in scope_rows}),
                "subsidiary_count": len({row["subsidiary"] for row in scope_rows}),
                "subscription_count": len({row["subscription"] for row in scope_rows}),
                "environment_count": len({row["environment"] for row in scope_rows}),
            },
            "timestamp": datetime.now(UTC).isoformat(),
            "data_as_of": max((row["data_as_of"] for row in rows), default=None),
            "evidence": evidence,
            "account_reasons": returned_accounts,
            "assumptions": REQUIRED_ASSUMPTIONS,
            "confidence": confidence,
            "data": data,
        }

    @staticmethod
    def _confidence(rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not rows:
            return {"level": "low", "score": 0.0, "reason": "No records matched the requested scope."}
        stale_fraction = sum(
            row["inventory_age_hours"] > 48 or row["metrics_age_hours"] > 24 for row in rows
        ) / len(rows)
        score = max(0.35, 0.97 - stale_fraction * 1.8)
        level = "high" if score >= 0.85 else "medium" if score >= 0.65 else "low"
        return {
            "level": level,
            "score": round(score, 2),
            "reason": f"{round(stale_fraction * 100, 1)}% of scoped records are stale.",
        }
