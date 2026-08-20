from __future__ import annotations

import hashlib
import json
import random
from datetime import UTC, datetime, timedelta
from typing import Any

from .hierarchy import SUBSCRIPTIONS

SEED = 20260811
DATA_AS_OF = datetime(2026, 8, 11, 16, 0, tzinfo=UTC)

REGIONS = ["eastus2", "eastus", "centralus", "westus2", "westeurope"]
TIERS = ["Hot", "Cool", "Cold", "Archive"]
REPLICATION = ["LRS", "ZRS", "GRS", "GZRS"]


def generate_accounts(count: int = 2500, seed: int = SEED) -> list[dict[str, Any]]:
    """Generate a repeatable, varied estate with seeded operational edge cases."""
    rng = random.Random(seed)
    accounts: list[dict[str, Any]] = []
    for index in range(count):
        hierarchy = SUBSCRIPTIONS[index % len(SUBSCRIPTIONS)]
        subscription = hierarchy["name"]
        subsidiary = hierarchy["subsidiary"]
        region = REGIONS[(index * 3) % len(REGIONS)]
        tier = rng.choices(TIERS, weights=[48, 30, 15, 7], k=1)[0]
        capacity_tb = round(0.8 + rng.lognormvariate(2.25, 1.05), 2)
        growth = round(rng.gauss(3.8, 5.2), 2)
        if index % 137 == 0:
            growth = round(28 + rng.random() * 35, 2)
        if index % 307 == 0:
            growth = round(-18 - rng.random() * 12, 2)
        transactions_m = round(max(0.02, rng.lognormvariate(0.9, 1.0)), 2)
        base_rate = {"Hot": 19.0, "Cool": 11.0, "Cold": 5.8, "Archive": 1.4}[tier]
        cost_monthly = round(capacity_tb * base_rate + transactions_m * 4.2, 2)
        cost_change = round(growth * 0.72 + rng.gauss(0, 3.5), 2)
        cold_fraction = round(min(0.92, max(0.03, rng.betavariate(2.4, 2.2))), 3)
        stale = index % 211 == 0
        inventory_age = 96 + index % 60 if stale else 2 + index % 28
        metric_age = 30 + index % 48 if index % 419 == 0 else index % 8
        throttling = round(max(0, rng.gauss(0.1, 0.35)) + (4.5 if index % 173 == 0 else 0), 2)
        latency = round(max(8, rng.gauss(36, 17)) + (140 if index % 173 == 0 else 0), 1)
        has_databricks = index % 3 == 0
        has_fabric = index % 5 == 0
        platform_rng = random.Random(f"{seed}:{index}:enterprise-platform")
        has_sap = index == 0 or platform_rng.random() < 0.12
        has_data_factory = index == 0 or platform_rng.random() < 0.18
        has_sftp = index == 0 or platform_rng.random() < 0.09
        has_app_insights = index == 0 or platform_rng.random() < 0.15
        hns_enabled = has_sftp or platform_rng.random() < 0.38
        security_rng = random.Random(f"{seed}:{index}:security-posture")
        uses_sas_keys = security_rng.random() < 0.22
        shared_key_access_enabled = uses_sas_keys or security_rng.random() < 0.28
        public_network_access = security_rng.random() < 0.19
        blob_public_access_enabled = public_network_access and security_rng.random() < 0.28
        private_endpoint_enabled = security_rng.random() < 0.73
        service_principal_access_enabled = security_rng.random() < 0.66
        network_security_group = (
            f"nsg-storage-{index % 23:02d}" if security_rng.random() < 0.14 else None
        )
        application_security_group = (
            f"asg-data-{index % 17:02d}" if security_rng.random() < 0.11 else None
        )
        project_defunct = security_rng.random() < 0.07
        last_access_days = (
            security_rng.randint(365, 900)
            if project_defunct
            else security_rng.randint(1, 320)
        )
        project_name = f"project-{hierarchy['name']}-{index % 97:02d}"
        small_files = round(rng.uniform(0.08, 0.88), 3) if has_databricks else 0.0
        lifecycle = index % 4 != 0
        version_overhead = round(rng.uniform(1, 29) if index % 5 == 0 else rng.uniform(0, 8), 2)
        soft_delete_overhead = round(rng.uniform(1, 18) if index % 8 == 0 else rng.uniform(0, 5), 2)
        account_id = (
            f"/subscriptions/{hierarchy['id']}/resourceGroups/rg-{index % 41:02d}/"
            f"providers/Microsoft.Storage/storageAccounts/st{index:05d}"
        )
        accounts.append(
            {
                "account_id": account_id,
                "name": f"st{index:05d}",
                "tenant_id": hierarchy["tenant_id"],
                "management_group": hierarchy["management_group"],
                "subscription_id": hierarchy["id"],
                "subscription": subscription,
                "environment": hierarchy["environment"],
                "subsidiary": subsidiary,
                "business_unit": subsidiary,
                "region": region,
                "tier": tier,
                "capacity_tb": capacity_tb,
                "growth_30d_pct": growth,
                "monthly_cost_usd": cost_monthly,
                "cost_change_pct": cost_change,
                "transactions_m": transactions_m,
                "cold_fraction": cold_fraction,
                "last_access_p90_days": int(8 + cold_fraction * 260),
                "replication": REPLICATION[index % len(REPLICATION)],
                "uses_sas_keys": uses_sas_keys,
                "shared_key_access_enabled": shared_key_access_enabled,
                "public_network_access": public_network_access,
                "blob_public_access_enabled": blob_public_access_enabled,
                "private_endpoint_enabled": private_endpoint_enabled,
                "service_principal_access_enabled": service_principal_access_enabled,
                "network_security_group": network_security_group,
                "application_security_group": application_security_group,
                "project_name": project_name,
                "tag_business_unit": subsidiary,
                "last_accessed_date": (DATA_AS_OF - timedelta(days=last_access_days)).date().isoformat(),
                "project_defunct": project_defunct,
                "business_criticality": ["low", "medium", "high"][index % 3],
                "lifecycle_policy": lifecycle,
                "inventory_age_hours": inventory_age,
                "metrics_age_hours": metric_age,
                "throttling_pct": throttling,
                "latency_ms": latency,
                "databricks_workspace": f"dbw-{index % len(SUBSCRIPTIONS)}-{index % 11}" if has_databricks else None,
                "fabric_lakehouse": f"lakehouse-{index % len(SUBSCRIPTIONS)}-{index % 9}" if has_fabric else None,
                "sap_system": f"SAP-{['S4HANA', 'BW', 'ECC'][index % 3]}-{index % 17:02d}" if has_sap else None,
                "azure_data_factory": f"adf-{index % len(SUBSCRIPTIONS)}-{index % 19:02d}" if has_data_factory else None,
                "hns_enabled": hns_enabled,
                "sftp_enabled": has_sftp,
                "application_insights_resource": (
                    f"appi-{index % len(SUBSCRIPTIONS)}-{index % 29:02d}"
                    if has_app_insights
                    else None
                ),
                "databricks_io_tb": round(capacity_tb * rng.uniform(0.1, 2.5), 2) if has_databricks else 0.0,
                "small_file_ratio": small_files,
                "version_overhead_pct": version_overhead,
                "soft_delete_overhead_pct": soft_delete_overhead,
                "snapshot_overhead_pct": round(rng.uniform(0, 12), 2),
                "data_as_of": DATA_AS_OF.isoformat(),
                "source": "synthetic-v1",
            }
        )
    return accounts


def dataset_fingerprint(accounts: list[dict[str, Any]]) -> str:
    payload = json.dumps(accounts, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
