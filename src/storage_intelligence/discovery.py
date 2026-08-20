from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AzureCliDiscoveryError(RuntimeError):
    pass


def _run_az(arguments: list[str], timeout: int = 180) -> Any:
    cli = os.getenv("AZURE_CLI_PATH", "az")
    if shutil.which(cli) is None:
        raise AzureCliDiscoveryError(f"Azure CLI executable was not found: {cli}")
    result = subprocess.run(
        [cli, *arguments, "--only-show-errors", "--output", "json"],
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Azure CLI command failed"
        raise AzureCliDiscoveryError(message[:2000])
    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        raise AzureCliDiscoveryError("Azure CLI returned invalid JSON") from exc


def _configured_tenants() -> list[str]:
    return [
        value.strip()
        for value in os.getenv("DISCOVERY_TENANT_IDS", "").split(",")
        if value.strip()
    ]


def _tag_value(tags: dict[str, Any], *keys: str) -> str | None:
    normalized = {
        "".join(character.lower() for character in str(key) if character.isalnum()): value
        for key, value in tags.items()
    }
    for key in keys:
        value = normalized.get(key)
        if value:
            return str(value).strip()
    return None


def _tag_bool(tags: dict[str, Any], *keys: str) -> bool | None:
    value = _tag_value(tags, *keys)
    if value is None:
        return None
    normalized = value.casefold()
    if normalized in {"1", "true", "yes", "enabled", "active", "defunct"}:
        return True
    if normalized in {"0", "false", "no", "disabled", "inactive", "active-project"}:
        return False
    return None


def _subsidiary(tags: dict[str, Any]) -> str:
    return _tag_value(
        tags,
        "subsidiary",
        "subsidiaryname",
        "businessunit",
        "businessunitname",
        "bu",
    ) or "Unassigned"


def _environment(tags: dict[str, Any], subscription_name: str) -> str:
    value = (_tag_value(tags, "environment", "environmentname", "env", "stage") or "").casefold()
    aliases = {
        "dev": "Dev",
        "development": "Dev",
        "qa": "QA",
        "test": "QA",
        "testing": "QA",
        "perf": "Perf",
        "performance": "Perf",
        "prod": "Prod",
        "production": "Prod",
    }
    if value in aliases:
        return aliases[value]
    normalized_name = "".join(
        character if character.isalnum() else "-"
        for character in subscription_name.casefold()
    )
    tokens = set(normalized_name.split("-"))
    for alias, canonical in aliases.items():
        if alias in tokens:
            return canonical
    return "Unassigned"


def _management_group(
    tags: dict[str, Any],
    subscription: dict[str, Any],
    subscription_groups: dict[str, str],
) -> str:
    return (
        _tag_value(tags, "managementgroup", "managementgroupid", "mg")
        or subscription_groups.get(str(subscription.get("id")))
        or str(subscription.get("managementGroup") or "").strip()
        or "Unassigned"
    )


def _platform_tag(tags: dict[str, Any], *keys: str) -> str | None:
    normalized = {
        "".join(character.lower() for character in str(key) if character.isalnum()): value
        for key, value in tags.items()
    }
    for key in keys:
        value = normalized.get(key)
        if value:
            return str(value).strip()
    return None


def _management_group_subscriptions() -> tuple[dict[str, str], list[str]]:
    subscription_groups: dict[str, str] = {}
    warnings: list[str] = []
    try:
        groups = _run_az(["account", "management-group", "list"])
    except AzureCliDiscoveryError as exc:
        return {}, [f"Management-group discovery unavailable: {exc}"]

    for group in groups or []:
        group_id = str(group.get("name") or group.get("id") or "").rsplit("/", 1)[-1]
        if not group_id:
            continue
        try:
            subscriptions = _run_az(
                [
                    "account",
                    "management-group",
                    "subscription",
                    "show-sub-under-mg",
                    "--name",
                    group_id,
                ]
            )
        except AzureCliDiscoveryError as exc:
            warnings.append(f"Management group {group_id} could not be enumerated: {exc}")
            continue
        for subscription in subscriptions or []:
            subscription_id = str(
                subscription.get("subscriptionId")
                or subscription.get("name")
                or subscription.get("id")
                or ""
            ).rsplit("/", 1)[-1]
            if subscription_id:
                subscription_groups.setdefault(subscription_id, group_id)
    return subscription_groups, warnings


def discover_storage_accounts(tenant_ids: list[str] | None = None) -> dict[str, Any]:
    requested_tenants = tenant_ids if tenant_ids is not None else _configured_tenants()
    managed_identity_client_id = os.getenv("AZURE_CLIENT_ID")
    if managed_identity_client_id and os.getenv("DISCOVERY_USE_MANAGED_IDENTITY", "true").lower() == "true":
        _run_az(["login", "--identity", "--client-id", managed_identity_client_id, "--allow-no-subscriptions"])

    subscriptions = _run_az(["account", "list", "--all"])
    enabled = [
        subscription
        for subscription in subscriptions
        if str(subscription.get("state", "")).casefold() == "enabled"
    ]
    visible_tenants = {str(subscription.get("tenantId")) for subscription in enabled}
    if requested_tenants:
        missing = sorted(set(requested_tenants) - visible_tenants)
        if missing:
            raise AzureCliDiscoveryError(
                f"Azure CLI has no authorized subscriptions for tenant(s): {', '.join(missing)}"
            )
        enabled = [
            subscription
            for subscription in enabled
            if str(subscription.get("tenantId")) in requested_tenants
        ]

    subscription_groups, warnings = _management_group_subscriptions()
    accounts: list[dict[str, Any]] = []
    for subscription in enabled:
        subscription_id = str(subscription["id"])
        subscription_name = str(subscription.get("name") or subscription_id)
        storage_accounts = _run_az(["storage", "account", "list", "--subscription", subscription_id])
        for account in storage_accounts:
            tags = account.get("tags") or {}
            private_endpoints = account.get("privateEndpointConnections") or []
            private_endpoint_enabled = any(
                str(
                    (connection.get("privateLinkServiceConnectionState") or {}).get("status")
                    or connection.get("provisioningState")
                    or ""
                ).casefold()
                in {"approved", "succeeded"}
                for connection in private_endpoints
            )
            project_status = _tag_value(tags, "projectstatus", "status") or ""
            project_defunct = _tag_bool(tags, "projectdefunct", "defunct")
            if project_defunct is None:
                project_defunct = project_status.casefold() in {
                    "defunct",
                    "decommissioned",
                    "retired",
                    "closed",
                }
            accounts.append(
                {
                    "account_id": account["id"],
                    "name": account["name"],
                    "tenant_id": str(subscription.get("tenantId") or ""),
                    "subscription_id": subscription_id,
                    "subscription_name": subscription_name,
                    "environment": _environment(tags, subscription_name),
                    "management_group": _management_group(tags, subscription, subscription_groups),
                    "subsidiary": _subsidiary(tags),
                    "business_unit": _subsidiary(tags),
                    "region": str(account.get("primaryLocation") or account.get("location") or "").lower(),
                    "tier": str(account.get("accessTier") or "Hot").title(),
                    "tier_assumed": not bool(account.get("accessTier")),
                    "kind": account.get("kind"),
                    "sku": (account.get("sku") or {}).get("name"),
                    "uses_sas_keys": bool(
                        _tag_bool(tags, "usessaskeys", "sasaccess", "sasenabled")
                    ),
                    "shared_key_access_enabled": bool(
                        account.get("allowSharedKeyAccess")
                        if account.get("allowSharedKeyAccess") is not None
                        else True
                    ),
                    "public_network_access": (
                        str(account.get("publicNetworkAccess") or "Enabled").casefold()
                        != "disabled"
                    ),
                    "blob_public_access_enabled": bool(account.get("allowBlobPublicAccess")),
                    "private_endpoint_enabled": private_endpoint_enabled,
                    "service_principal_access_enabled": bool(
                        _tag_bool(
                            tags,
                            "serviceprincipalaccess",
                            "serviceprincipalenabled",
                            "spaccess",
                        )
                    ),
                    "network_security_group": _platform_tag(
                        tags,
                        "networksecuritygroup",
                        "nsg",
                    ),
                    "application_security_group": _platform_tag(
                        tags,
                        "applicationsecuritygroup",
                        "asg",
                    ),
                    "project_name": _platform_tag(
                        tags,
                        "project",
                        "projectname",
                        "projectid",
                    )
                    or "Unassigned",
                    "tag_business_unit": _subsidiary(tags),
                    "last_accessed_date": _platform_tag(
                        tags,
                        "lastaccesseddate",
                        "lastaccessdate",
                        "lastuseddate",
                    ),
                    "project_defunct": project_defunct,
                    "databricks_workspace": _platform_tag(
                        tags,
                        "databricksworkspace",
                        "databricks",
                    ),
                    "fabric_lakehouse": _platform_tag(
                        tags,
                        "fabriclakehouse",
                        "lakehouse",
                    ),
                    "sap_system": _platform_tag(
                        tags,
                        "sapsystem",
                        "sapworkload",
                        "sap",
                    ),
                    "azure_data_factory": _platform_tag(
                        tags,
                        "azuredatafactory",
                        "datafactory",
                        "adf",
                    ),
                    "hns_enabled": bool(account.get("isHnsEnabled")),
                    "sftp_enabled": bool(
                        account.get("isSftpEnabled")
                        or _tag_bool(tags, "sftpenabled", "sftp")
                    ),
                    "application_insights_resource": _platform_tag(
                        tags,
                        "applicationinsights",
                        "applicationinsightsresource",
                        "appinsights",
                        "appinsightsresource",
                        "telemetryresource",
                    ),
                }
            )

    return {
        "pulled_at": datetime.now(UTC).isoformat(),
        "tenants": sorted({account["tenant_id"] for account in accounts}),
        "management_groups": sorted({account["management_group"] for account in accounts}),
        "subsidiaries": sorted({account["subsidiary"] for account in accounts}),
        "environments": sorted({account["environment"] for account in accounts}),
        "subscriptions": len(enabled),
        "accounts": accounts,
        "warnings": warnings,
    }


def _write_output(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2), encoding="utf-8")
    temporary.replace(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull tenant-wide Azure Storage account details")
    parser.add_argument("--tenant-id", action="append", dest="tenant_ids")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(os.getenv("DISCOVERY_OUTPUT_PATH", "data/discovered-storage-accounts.json")),
    )
    args = parser.parse_args()
    result = discover_storage_accounts(args.tenant_ids)
    _write_output(result, args.output)
    print(json.dumps({"output": str(args.output), "accounts": len(result["accounts"])}))


if __name__ == "__main__":
    main()
