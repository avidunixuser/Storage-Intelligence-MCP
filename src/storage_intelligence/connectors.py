from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable


class ConnectorDisabledError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConnectorContext:
    source: str
    enabled: bool
    watermark: datetime | None = None
    tenant_id: str | None = None
    managed_identity_client_id: str | None = None


class Connector(ABC):
    env_flag: str

    def __init__(self, context: ConnectorContext):
        self.context = context

    def require_enabled(self) -> None:
        configured = os.getenv(self.env_flag, "false").lower() == "true"
        if not self.context.enabled or not configured:
            raise ConnectorDisabledError(
                f"{self.context.source} is disabled. Set both the connector context and {self.env_flag}=true."
            )

    @abstractmethod
    def collect(self) -> Iterable[dict[str, Any]]:
        raise NotImplementedError


class ResourceGraphConnector(Connector):
    env_flag = "ENABLE_RESOURCE_GRAPH"

    def __init__(self, context: ConnectorContext, subscriptions: list[str]):
        super().__init__(context)
        self.subscriptions = subscriptions

    def collect(self) -> Iterable[dict[str, Any]]:
        self.require_enabled()
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.resourcegraph import ResourceGraphClient
        from azure.mgmt.resourcegraph.models import QueryRequest

        credential = DefaultAzureCredential(managed_identity_client_id=self.context.managed_identity_client_id)
        client = ResourceGraphClient(credential)
        query = """
resources
| where type =~ 'microsoft.storage/storageaccounts'
| project id, name, subscriptionId, resourceGroup, location, sku, kind, tags, properties
"""
        response = client.resources(QueryRequest(subscriptions=self.subscriptions, query=query))
        return response.data


class BlobInventoryConnector(Connector):
    env_flag = "ENABLE_BLOB_INVENTORY"

    def __init__(self, context: ConnectorContext, account_url: str, paths: list[str]):
        super().__init__(context)
        self.account_url = account_url
        self.paths = paths

    def collect(self) -> Iterable[dict[str, Any]]:
        self.require_enabled()
        import pyarrow.parquet as parquet
        from azure.identity import DefaultAzureCredential
        from azure.storage.filedatalake import DataLakeServiceClient

        credential = DefaultAzureCredential(managed_identity_client_id=self.context.managed_identity_client_id)
        service = DataLakeServiceClient(account_url=self.account_url, credential=credential)
        for path in self.paths:
            filesystem, file_path = path.split("/", 1)
            payload = service.get_file_system_client(filesystem).get_file_client(file_path).download_file().readall()
            yield from parquet.read_table(source=__import__("io").BytesIO(payload)).to_pylist()


class AzureMonitorMetricsConnector(Connector):
    env_flag = "ENABLE_AZURE_MONITOR_METRICS"

    def __init__(self, context: ConnectorContext, resource_ids: list[str]):
        super().__init__(context)
        self.resource_ids = resource_ids

    def collect(self) -> Iterable[dict[str, Any]]:
        self.require_enabled()
        from azure.identity import DefaultAzureCredential
        from azure.monitor.querymetrics import MetricsClient

        credential = DefaultAzureCredential(managed_identity_client_id=self.context.managed_identity_client_id)
        client = MetricsClient("https://eastus2.metrics.monitor.azure.com", credential)
        names = ["UsedCapacity", "Transactions", "Ingress", "Egress", "Availability", "SuccessE2ELatency"]
        for offset in range(0, len(self.resource_ids), 50):
            batch = self.resource_ids[offset : offset + 50]
            for response in client.query_resources(batch, metric_namespace="Microsoft.Storage/storageAccounts", metric_names=names):
                yield {"resource_id": response.resource_id, "metrics": response.metrics}


class CostExportConnector(BlobInventoryConnector):
    env_flag = "ENABLE_COST_EXPORTS"


class DatabricksSystemTableExportConnector(BlobInventoryConnector):
    env_flag = "ENABLE_DATABRICKS_EXPORTS"
