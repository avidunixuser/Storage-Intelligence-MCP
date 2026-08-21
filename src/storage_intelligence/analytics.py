from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Iterable

AT_RISK_THRESHOLD = 20.0


def _round(value: float) -> float:
    return round(value, 2)


def _top(rows: Iterable[dict[str, Any]], key: str, limit: int = 10) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: row[key], reverse=True)[:limit]


def _hierarchy(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "account_id": row["account_id"],
        "tenant_id": row.get("tenant_id"),
        "management_group": row.get("management_group"),
        "subsidiary": row.get("subsidiary") or row.get("business_unit"),
        "subscription": row.get("subscription"),
        "environment": row.get("environment"),
        "databricks_workspace": row.get("databricks_workspace"),
        "fabric_lakehouse": row.get("fabric_lakehouse"),
        "sap_system": row.get("sap_system"),
        "azure_data_factory": row.get("azure_data_factory"),
        "hns_enabled": row.get("hns_enabled"),
        "sftp_enabled": row.get("sftp_enabled"),
        "application_insights_resource": row.get("application_insights_resource"),
        "azure_function_app": row.get("azure_function_app"),
        "log_analytics_workspace": row.get("log_analytics_workspace"),
        "uses_sas_keys": row.get("uses_sas_keys"),
        "shared_key_access_enabled": row.get("shared_key_access_enabled"),
        "public_network_access": row.get("public_network_access"),
        "blob_public_access_enabled": row.get("blob_public_access_enabled"),
        "private_endpoint_enabled": row.get("private_endpoint_enabled"),
        "service_principal_access_enabled": row.get("service_principal_access_enabled"),
        "managed_identity_enabled": row.get("managed_identity_enabled"),
        "network_security_group": row.get("network_security_group"),
        "application_security_group": row.get("application_security_group"),
        "project_name": row.get("project_name"),
        "tag_business_unit": row.get("tag_business_unit"),
        "last_accessed_date": row.get("last_accessed_date"),
        "project_defunct": row.get("project_defunct"),
    }


def portfolio_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    capacity = sum(row["capacity_tb"] for row in rows)
    cost = sum(row["monthly_cost_usd"] for row in rows)
    savings = sum(_account_savings(row, 0.25)["net_monthly_savings_usd"] for row in rows)
    return {
        "account_count": len(rows),
        "capacity_tb": _round(capacity),
        "monthly_cost_usd": _round(cost),
        "weighted_growth_30d_pct": _round(
            sum(row["capacity_tb"] * row["growth_30d_pct"] for row in rows) / capacity
            if capacity
            else 0
        ),
        "potential_monthly_savings_usd": _round(savings),
        "stale_accounts": sum(row["inventory_age_hours"] > 48 for row in rows),
        "at_risk_accounts": sum(risk_score(row)["score"] >= AT_RISK_THRESHOLD for row in rows),
        "high_risk_accounts": sum(risk_score(row)["score"] >= 70 for row in rows),
        "sas_key_accounts": sum(bool(row.get("uses_sas_keys")) for row in rows),
        "public_access_accounts": sum(
            bool(row.get("public_network_access") or row.get("blob_public_access_enabled"))
            for row in rows
        ),
        "missing_private_endpoint_accounts": sum(
            row.get("private_endpoint_enabled") is False for row in rows
        ),
        "missing_service_principal_access_accounts": sum(
            row.get("service_principal_access_enabled") is False for row in rows
        ),
        "managed_identity_accounts": sum(
            row.get("managed_identity_enabled") is True for row in rows
        ),
        "non_geo_redundant_accounts": sum(
            row.get("replication") not in {"GRS", "GZRS"} for row in rows
        ),
        "nsg_asg_linked_accounts": sum(
            bool(row.get("network_security_group") or row.get("application_security_group"))
            for row in rows
        ),
        "defunct_project_accounts": sum(row.get("project_defunct") is True for row in rows),
        "sftp_enabled_accounts": sum(row.get("sftp_enabled") is True for row in rows),
        "application_insights_accounts": sum(
            bool(row.get("application_insights_resource")) for row in rows
        ),
    }


def _last_access_age_days(row: dict[str, Any]) -> int | None:
    value = row.get("last_accessed_date")
    if not value:
        return None
    try:
        last_accessed = date.fromisoformat(str(value)[:10])
        data_as_of = datetime.fromisoformat(str(row["data_as_of"]).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return None
    return max(0, (data_as_of - last_accessed).days)


def growth_anomalies(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    values = [row["growth_30d_pct"] for row in rows]
    median = statistics.median(values) if values else 0
    mad = statistics.median(abs(value - median) for value in values) if values else 0
    denominator = max(1.0, 1.4826 * mad)
    findings = []
    for row in rows:
        score = (row["growth_30d_pct"] - median) / denominator
        if abs(score) >= 3:
            findings.append(
                {
                    **_hierarchy(row),
                    "name": row["name"],
                    "growth_30d_pct": row["growth_30d_pct"],
                    "robust_z_score": _round(score),
                    "capacity_tb": row["capacity_tb"],
                    "reason": (
                        f"30-day growth of {row['growth_30d_pct']}% is {_round(score)} robust "
                        f"deviations from the portfolio median of {_round(median)}%."
                    ),
                }
            )
    return _top(findings, "robust_z_score", limit)


def forecast(row: dict[str, Any]) -> dict[str, Any]:
    daily_rate = row["growth_30d_pct"] / 3000
    projections = {}
    for days in (30, 90, 180):
        expected = row["capacity_tb"] * ((1 + daily_rate) ** days)
        spread = expected * min(0.35, 0.04 + abs(row["growth_30d_pct"]) / 300)
        projections[str(days)] = {
            "capacity_tb": _round(expected),
            "lower_tb": _round(max(0, expected - spread)),
            "upper_tb": _round(expected + spread),
        }
    return {
        **_hierarchy(row),
        "name": row["name"],
        "projections": projections,
        "method": "bounded compound trend",
        "reason": (
            f"Selected because its 30-day growth is {row['growth_30d_pct']}% on "
            f"{row['capacity_tb']} TB of current capacity."
        ),
    }


def capacity_forecasts(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    candidates = _top(rows, "growth_30d_pct", limit)
    return [forecast(row) for row in candidates]


def _account_savings(row: dict[str, Any], adoption: float) -> dict[str, Any]:
    eligible_tb = row["capacity_tb"] * row["cold_fraction"] * adoption
    current_rate = {"Hot": 19.0, "Cool": 11.0, "Cold": 5.8, "Archive": 1.4}[row["tier"]]
    target_rate = 5.8 if row["last_access_p90_days"] < 120 else 1.4
    storage_savings = max(0, eligible_tb * (current_rate - target_rate))
    retrieval_and_ops = eligible_tb * (0.75 + row["transactions_m"] / max(row["capacity_tb"], 1) * 0.12)
    early_deletion_risk = target_rate == 1.4 and row["last_access_p90_days"] < 180
    net = max(0, storage_savings - retrieval_and_ops)
    return {
        **_hierarchy(row),
        "eligible_tb": _round(eligible_tb),
        "net_monthly_savings_usd": _round(net),
        "target_tier": "Archive" if target_rate == 1.4 else "Cold",
        "early_deletion_risk": early_deletion_risk,
        "retrieval_and_ops_usd": _round(retrieval_and_ops),
        "reason": (
            f"{_round(eligible_tb)} TB is eligible for "
            f"{'Archive' if target_rate == 1.4 else 'Cold'}, producing ${_round(net)} "
            f"net monthly savings after ${_round(retrieval_and_ops)} retrieval and operation costs"
            f"{'; validate early-deletion exposure' if early_deletion_risk else ''}."
        ),
    }


def tier_savings(rows: list[dict[str, Any]], adoption: float = 0.25, limit: int = 10) -> dict[str, Any]:
    details = [_account_savings(row, adoption) for row in rows]
    ranked = _top(details, "net_monthly_savings_usd", limit)
    return {
        "adoption_pct": int(adoption * 100),
        "net_monthly_savings_usd": _round(sum(item["net_monthly_savings_usd"] for item in details)),
        "eligible_tb": _round(sum(item["eligible_tb"] for item in details)),
        "top_accounts": ranked,
    }


def savings_scenarios(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [tier_savings(rows, adoption, 5) for adoption in (0.10, 0.25, 0.50)]


def cost_explanation(rows: list[dict[str, Any]], limit: int = 10) -> dict[str, Any]:
    movers = _top(rows, "cost_change_pct", limit)
    return {
        "portfolio_change_pct": _round(
            sum(row["monthly_cost_usd"] * row["cost_change_pct"] for row in rows)
            / max(1, sum(row["monthly_cost_usd"] for row in rows))
        ),
        "drivers": [
            {
                **_hierarchy(row),
                "cost_change_pct": row["cost_change_pct"],
                "capacity_component_pct": _round(row["growth_30d_pct"] * 0.72),
                "operations_component_pct": _round(row["cost_change_pct"] - row["growth_30d_pct"] * 0.72),
                "monthly_cost_usd": row["monthly_cost_usd"],
                "reason": (
                    f"Monthly cost changed {row['cost_change_pct']}%; "
                    f"{_round(row['growth_30d_pct'] * 0.72)} points are attributed to capacity "
                    f"and {_round(row['cost_change_pct'] - row['growth_30d_pct'] * 0.72)} to operations."
                ),
            }
            for row in movers
        ],
    }


def risk_score(row: dict[str, Any]) -> dict[str, Any]:
    growth = min(100, max(0, row["growth_30d_pct"] * 2.0))
    cost = min(100, max(0, row["cost_change_pct"] * 2.2))
    freshness = min(100, max(row["inventory_age_hours"] / 1.2, row["metrics_age_hours"] * 2.0))
    operations = min(100, row["throttling_pct"] * 14 + max(0, row["latency_ms"] - 40) * 0.45)
    data = min(100, row["small_file_ratio"] * 100 if row["databricks_workspace"] else 0)
    configuration = (
        (35 if not row["lifecycle_policy"] else 0)
        + min(35, row["version_overhead_pct"])
        + (25 if row["replication"] in {"GRS", "GZRS"} and row["business_criticality"] == "low" else 0)
        + (25 if row.get("replication") not in {"GRS", "GZRS"} else 0)
    )
    security = (
        (20 if row.get("uses_sas_keys") is True else 0)
        + (10 if row.get("shared_key_access_enabled") is True else 0)
        + (20 if row.get("public_network_access") is True else 0)
        + (10 if row.get("blob_public_access_enabled") is True else 0)
        + (20 if row.get("private_endpoint_enabled") is False else 0)
        + (
            10
            if row.get("network_security_group") or row.get("application_security_group")
            else 0
        )
        + (10 if row.get("service_principal_access_enabled") is False else 0)
        + (10 if row.get("sftp_enabled") is True else 0)
    )
    last_access_age_days = _last_access_age_days(row)
    governance = (
        (60 if row.get("project_defunct") is True else 0)
        + (15 if not row.get("project_name") else 0)
        + (
            10
            if row.get("tag_business_unit")
            and row.get("tag_business_unit") != row.get("subsidiary")
            else 0
        )
        + (
            30
            if last_access_age_days is not None and last_access_age_days > 365
            else 15
            if last_access_age_days is not None and last_access_age_days > 180
            else 10
            if last_access_age_days is None
            else 0
        )
    )
    components = {
        "growth": _round(growth),
        "cost": _round(cost),
        "freshness": _round(freshness),
        "operations": _round(operations),
        "databricks": _round(data),
        "configuration": _round(min(100, configuration)),
        "security": _round(min(100, security)),
        "governance": _round(min(100, governance)),
    }
    risk_factors = []
    if row.get("uses_sas_keys") is True:
        risk_factors.append("SAS token usage is tagged or observed")
    if row.get("shared_key_access_enabled") is True:
        risk_factors.append("Shared-key access remains enabled")
    if row.get("public_network_access") is True:
        risk_factors.append("Public network access remains enabled")
    if row.get("blob_public_access_enabled") is True:
        risk_factors.append("Blob public access is enabled")
    if row.get("private_endpoint_enabled") is False:
        risk_factors.append("No approved private endpoint is enabled")
    if row.get("replication") not in {"GRS", "GZRS"}:
        risk_factors.append(f"{row.get('replication')} replication does not provide GRS/GZRS")
    if row.get("network_security_group") or row.get("application_security_group"):
        groups = "/".join(
            value
            for value in (
                row.get("network_security_group"),
                row.get("application_security_group"),
            )
            if value
        )
        risk_factors.append(f"Associated with network/application security group {groups}")
    if row.get("service_principal_access_enabled") is False:
        risk_factors.append("No service-principal-based access marker is enabled")
    if row.get("sftp_enabled") is True:
        risk_factors.append("SFTP endpoint is enabled")
    if row.get("project_defunct") is True:
        risk_factors.append(f"Project {row.get('project_name') or 'Unassigned'} is marked defunct")
    if last_access_age_days is None:
        risk_factors.append("LastAccessedDate tag is missing or invalid")
    elif last_access_age_days > 180:
        risk_factors.append(f"Project was last accessed {last_access_age_days} days ago")
    score = _round(sum(
        components[name] * weight
        for name, weight in {
            "growth": 0.18,
            "cost": 0.14,
            "freshness": 0.12,
            "operations": 0.14,
            "databricks": 0.09,
            "configuration": 0.11,
            "security": 0.15,
            "governance": 0.07,
        }.items()
    ))
    leading = sorted(components.items(), key=lambda item: item[1], reverse=True)[:2]
    return {
        **_hierarchy(row),
        "name": row["name"],
        "score": score,
        "components": components,
        "risk_factors": risk_factors,
        "last_access_age_days": last_access_age_days,
        "reason": (
            f"Overall risk is {score}/100; {leading[0][0].title()} ({leading[0][1]}/100) "
            f"and {leading[1][0].title()} ({leading[1][1]}/100) are the two largest "
            "transparent risk dimensions."
            + (
                f" Key factors: {'; '.join(risk_factors[:3])}."
                if risk_factors
                else ""
            )
        ),
    }


def risks(
    rows: list[dict[str, Any]],
    limit: int | None = 10,
    minimum_score: float = 0.0,
) -> list[dict[str, Any]]:
    scored = [risk_score(row) for row in rows]
    ranked = sorted(
        (item for item in scored if item["score"] >= minimum_score),
        key=lambda item: item["score"],
        reverse=True,
    )
    return ranked if limit is None else ranked[:limit]


def security_findings(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    findings = [risk_score(row) for row in rows]
    findings = [item for item in findings if item["components"]["security"] > 0]
    return sorted(
        findings,
        key=lambda item: (item["components"]["security"], item["score"]),
        reverse=True,
    )[:limit]


def governance_findings(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    findings = [risk_score(row) for row in rows]
    return sorted(
        (item for item in findings if item["components"]["governance"] > 0),
        key=lambda item: (item["components"]["governance"], item["score"]),
        reverse=True,
    )[:limit]


def resilience_findings(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    findings = [
        risk_score(row)
        for row in rows
        if row.get("replication") not in {"GRS", "GZRS"}
    ]
    return sorted(
        findings,
        key=lambda item: (item["components"]["configuration"], item["score"]),
        reverse=True,
    )[:limit]


def databricks_impact(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    impacted = []
    for row in rows:
        if not row["databricks_workspace"]:
            continue
        impact = (
            row["databricks_io_tb"] * 0.35
            + row["small_file_ratio"] * 45
            + row["throttling_pct"] * 7
            + max(0, row["latency_ms"] - 35) * 0.18
        )
        impacted.append(
            {
                **_hierarchy(row),
                "workspace": row["databricks_workspace"],
                "impact_score": _round(min(100, impact)),
                "io_tb": row["databricks_io_tb"],
                "small_file_ratio": row["small_file_ratio"],
                "latency_ms": row["latency_ms"],
                "reason": (
                    f"Impact score {_round(min(100, impact))}/100 combines "
                    f"{row['databricks_io_tb']} TB IO, {round(row['small_file_ratio'] * 100, 1)}% "
                    f"small files, {row['throttling_pct']}% throttling, and {row['latency_ms']} ms latency."
                ),
            }
        )
    return _top(impacted, "impact_score", limit)


def compare(rows: list[dict[str, Any]], dimension: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[dimension])].append(row)
    result = []
    for name, group in groups.items():
        summary = portfolio_summary(group)
        summary[dimension] = name
        result.append(summary)
    return sorted(result, key=lambda item: item["capacity_tb"], reverse=True)


def freshness(rows: list[dict[str, Any]], limit: int = 20) -> dict[str, Any]:
    stale = [
        {
            **_hierarchy(row),
            "inventory_age_hours": row["inventory_age_hours"],
            "metrics_age_hours": row["metrics_age_hours"],
            "action": "refresh inventory" if row["inventory_age_hours"] > 48 else "refresh metrics",
            "reason": (
                f"Inventory is {row['inventory_age_hours']} hours old and metrics are "
                f"{row['metrics_age_hours']} hours old; freshness limits are 48 and 24 hours."
            ),
        }
        for row in rows
        if row["inventory_age_hours"] > 48 or row["metrics_age_hours"] > 24
    ]
    stale.sort(key=lambda item: max(item["inventory_age_hours"], item["metrics_age_hours"]), reverse=True)
    return {"stale_count": len(stale), "accounts": stale[:limit]}


def configuration_findings(rows: list[dict[str, Any]], kind: str, limit: int = 10) -> list[dict[str, Any]]:
    if kind == "lifecycle":
        findings = [
            {
                **_hierarchy(row),
                "capacity_tb": row["capacity_tb"],
                "issue": "missing lifecycle policy",
                "reason": f"No lifecycle policy is configured for {row['capacity_tb']} TB of stored data.",
            }
            for row in rows
            if not row["lifecycle_policy"]
        ]
        return _top(findings, "capacity_tb", limit)
    if kind == "archive":
        findings = [
            {
                **_hierarchy(row),
                "last_access_p90_days": row["last_access_p90_days"],
                "cold_fraction": row["cold_fraction"],
                "issue": "rehydration or early-deletion exposure",
                "reason": (
                    f"{round(row['cold_fraction'] * 100, 1)}% of data is cold, but the "
                    f"90th-percentile last access is only {row['last_access_p90_days']} days."
                ),
            }
            for row in rows
            if row["cold_fraction"] > 0.45 and row["last_access_p90_days"] < 180
        ]
        return _top(findings, "cold_fraction", limit)
    if kind == "transactions":
        findings = [
            {
                **_hierarchy(row),
                "transactions_per_tb_m": _round(row["transactions_m"] / max(0.01, row["capacity_tb"])),
                "monthly_cost_usd": row["monthly_cost_usd"],
                "reason": (
                    f"{_round(row['transactions_m'] / max(0.01, row['capacity_tb']))} million "
                    f"transactions per TB contributes to ${row['monthly_cost_usd']} monthly cost."
                ),
            }
            for row in rows
        ]
        return _top(findings, "transactions_per_tb_m", limit)
    if kind == "overhead":
        findings = [
            {
                **_hierarchy(row),
                "avoidable_overhead_pct": _round(
                    row["version_overhead_pct"] + row["soft_delete_overhead_pct"] + row["snapshot_overhead_pct"]
                ),
                "reason": (
                    f"Versioning, soft-delete, and snapshots add "
                    f"{_round(row['version_overhead_pct'] + row['soft_delete_overhead_pct'] + row['snapshot_overhead_pct'])}% "
                    "avoidable capacity overhead."
                ),
            }
            for row in rows
        ]
        return _top(findings, "avoidable_overhead_pct", limit)
    findings = [
        {
            **_hierarchy(row),
            "replication": row["replication"],
            "business_criticality": row["business_criticality"],
            "monthly_cost_usd": row["monthly_cost_usd"],
            "reason": (
                f"{row['replication']} is used for a {row['business_criticality']}-criticality "
                f"account costing ${row['monthly_cost_usd']} per month."
            ),
        }
        for row in rows
        if row["replication"] in {"GRS", "GZRS"} and row["business_criticality"] == "low"
    ]
    return _top(findings, "monthly_cost_usd", limit)


def top_actions(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    savings = tier_savings(rows, 0.25, limit)["top_accounts"]
    risk_by_id = {item["account_id"]: item for item in risks(rows, 50)}
    actions = []
    for item in savings:
        risk = risk_by_id.get(item["account_id"], {"score": 0})
        actions.append(
            {
                **_hierarchy(item),
                "action": f"validate {item['target_tier']} tiering",
                "monthly_savings_usd": item["net_monthly_savings_usd"],
                "risk_reduction_score": risk["score"],
                "effort": "medium" if item["early_deletion_risk"] else "low",
                "reason": (
                    f"Modeled ${item['net_monthly_savings_usd']} monthly savings and "
                    f"{risk['score']}/100 risk support validating {item['target_tier']} tiering."
                ),
            }
        )
    return actions[:limit]
