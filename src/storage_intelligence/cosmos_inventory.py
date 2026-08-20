from __future__ import annotations

import hashlib
import os
from collections.abc import Callable
from typing import Any


def _enabled() -> bool:
    return os.getenv("COSMOS_INVENTORY_ENABLED", "false").lower() == "true"


def get_cosmos_container(
    *,
    client_factory: Callable[..., Any] | None = None,
    credential_factory: Callable[..., Any] | None = None,
) -> Any:
    endpoint = os.getenv("COSMOS_ENDPOINT")
    if not endpoint:
        raise RuntimeError("COSMOS_ENDPOINT is required when Cosmos inventory persistence is enabled")

    if client_factory is None or credential_factory is None:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential

        client_factory = client_factory or CosmosClient
        credential_factory = credential_factory or DefaultAzureCredential

    client_id = os.getenv("AZURE_CLIENT_ID")
    credential = credential_factory(managed_identity_client_id=client_id) if client_id else credential_factory()
    client = client_factory(endpoint, credential=credential)
    database_name = os.getenv("COSMOS_DATABASE", "storage-intelligence")
    container_name = os.getenv("COSMOS_CONTAINER", "storage-accounts")
    return client.get_database_client(database_name).get_container_client(container_name)


def persist_discovered_accounts(
    accounts: list[dict[str, Any]],
    *,
    pulled_at: str,
    trigger: str,
    client_factory: Callable[..., Any] | None = None,
    credential_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    database_name = os.getenv("COSMOS_DATABASE", "storage-intelligence")
    container_name = os.getenv("COSMOS_CONTAINER", "storage-accounts")
    if not _enabled():
        return {
            "status": "disabled",
            "upserted": 0,
            "database": database_name,
            "container": container_name,
        }

    container = get_cosmos_container(
        client_factory=client_factory,
        credential_factory=credential_factory,
    )

    for account in accounts:
        resource_id = str(account["account_id"])
        item = {
            **account,
            "id": hashlib.sha256(resource_id.encode("utf-8")).hexdigest(),
            "resource_id": resource_id,
            "document_type": "storage-account-inventory",
            "schema_version": 1,
            "source": "azure-cli-discovery-v1",
            "discovery_trigger": trigger,
            "pulled_at": pulled_at,
        }
        container.upsert_item(body=item)

    return {
        "status": "completed",
        "upserted": len(accounts),
        "database": database_name,
        "container": container_name,
    }
