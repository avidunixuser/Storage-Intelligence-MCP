from __future__ import annotations

from typing import Any

TENANTS = [
    {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Avidunixuser Americas (Synthetic)",
    },
    {
        "id": "22222222-2222-4222-8222-222222222222",
        "name": "Avidunixuser Europe (Synthetic)",
    },
    {
        "id": "33333333-3333-4333-8333-333333333333",
        "name": "Avidunixuser APAC (Synthetic)",
    },
]

MANAGEMENT_GROUPS = [
    {
        "id": "mg-americas-platform",
        "name": "Americas Platform",
        "tenant_id": TENANTS[0]["id"],
    },
    {
        "id": "mg-americas-consumer",
        "name": "Americas Consumer",
        "tenant_id": TENANTS[0]["id"],
    },
    {
        "id": "mg-europe-enterprise",
        "name": "Europe Enterprise",
        "tenant_id": TENANTS[1]["id"],
    },
    {
        "id": "mg-apac-data",
        "name": "APAC Data",
        "tenant_id": TENANTS[2]["id"],
    },
]

SUBSIDIARIES = [
    "Avidunixuser North America",
    "Frito-Lay North America",
    "Quaker Foods North America",
    "Avidunixuser Europe",
    "Avidunixuser APAC",
]

ENVIRONMENTS = ["Dev", "QA", "Perf", "Prod"]

BASE_SUBSCRIPTIONS = [
    {
        "id": "aaaaaaaa-0000-4000-8000-000000000001",
        "name": "platform-prod",
        "tenant_id": TENANTS[0]["id"],
        "management_group": "mg-americas-platform",
        "subsidiary": "Avidunixuser North America",
        "environment": "Prod",
    },
    {
        "id": "aaaaaaaa-0000-4000-8000-000000000002",
        "name": "data-prod",
        "tenant_id": TENANTS[0]["id"],
        "management_group": "mg-americas-consumer",
        "subsidiary": "Frito-Lay North America",
        "environment": "Prod",
    },
    {
        "id": "aaaaaaaa-0000-4000-8000-000000000003",
        "name": "analytics-prod",
        "tenant_id": TENANTS[2]["id"],
        "management_group": "mg-apac-data",
        "subsidiary": "Avidunixuser APAC",
        "environment": "Prod",
    },
    {
        "id": "aaaaaaaa-0000-4000-8000-000000000004",
        "name": "business-apps",
        "tenant_id": TENANTS[1]["id"],
        "management_group": "mg-europe-enterprise",
        "subsidiary": "Avidunixuser Europe",
        "environment": "Prod",
    },
    {
        "id": "aaaaaaaa-0000-4000-8000-000000000005",
        "name": "archive-estate",
        "tenant_id": TENANTS[0]["id"],
        "management_group": "mg-americas-consumer",
        "subsidiary": "Quaker Foods North America",
        "environment": "Prod",
    },
]

MANAGEMENT_GROUP_SUBSIDIARIES = {
    "mg-americas-platform": [
        "Avidunixuser North America",
        "Quaker Foods North America",
    ],
    "mg-americas-consumer": [
        "Frito-Lay North America",
        "Avidunixuser North America",
        "Quaker Foods North America",
    ],
    "mg-europe-enterprise": ["Avidunixuser Europe"],
    "mg-apac-data": ["Avidunixuser APAC"],
}

SUBSIDIARY_SLUGS = {
    "Avidunixuser North America": "avidna",
    "Frito-Lay North America": "flna",
    "Quaker Foods North America": "quaker",
    "Avidunixuser Europe": "europe",
    "Avidunixuser APAC": "apac",
}


def _build_subscriptions(count: int = 339) -> list[dict[str, Any]]:
    subscriptions = list(BASE_SUBSCRIPTIONS)
    for ordinal in range(len(subscriptions) + 1, count + 1):
        group = MANAGEMENT_GROUPS[(ordinal - 1) % len(MANAGEMENT_GROUPS)]
        subsidiaries = MANAGEMENT_GROUP_SUBSIDIARIES[group["id"]]
        subsidiary = subsidiaries[(ordinal - 1) % len(subsidiaries)]
        environment = ENVIRONMENTS[(ordinal - 1) % len(ENVIRONMENTS)]
        subscriptions.append(
            {
                "id": f"aaaaaaaa-0000-4000-8000-{ordinal:012d}",
                "name": f"{SUBSIDIARY_SLUGS[subsidiary]}-{environment.lower()}-{ordinal:03d}",
                "tenant_id": group["tenant_id"],
                "management_group": group["id"],
                "subsidiary": subsidiary,
                "environment": environment,
            }
        )
    return subscriptions


SUBSCRIPTIONS = _build_subscriptions()


def tenant_labels() -> dict[str, str]:
    return {tenant["id"]: tenant["name"] for tenant in TENANTS}


def management_group_labels() -> dict[str, str]:
    return {group["id"]: group["name"] for group in MANAGEMENT_GROUPS}


def subscription_by_name() -> dict[str, dict[str, Any]]:
    return {subscription["name"]: subscription for subscription in SUBSCRIPTIONS}
