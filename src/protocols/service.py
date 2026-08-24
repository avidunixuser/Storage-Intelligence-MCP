from __future__ import annotations

from typing import Any

from storage_intelligence import IntelligenceEngine
from storage_intelligence.analytics import portfolio_summary

SUPPORTED_FILTERS = (
    "tenant_id",
    "management_group",
    "subsidiary",
    "business_unit",
    "subscription",
    "environment",
    "region",
    "tier",
    "databricks",
)


class StorageIntelligenceService:
    """Protocol-neutral facade over the deterministic intelligence engine."""

    def __init__(self, engine: IntelligenceEngine):
        self._engine = engine

    def investigate(
        self,
        question: str,
        filters: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self._engine.answer(question, filters)

    def portfolio(self, filters: dict[str, str] | None = None) -> dict[str, Any]:
        rows = self._engine.filter(filters)
        result = self._engine.answer("portfolio overview", filters)
        result["data"] = portfolio_summary(rows)
        return result

    @staticmethod
    def capabilities() -> dict[str, Any]:
        return {
            "name": "Storage Atlas Agent",
            "version": "0.1.0",
            "read_only": True,
            "operations": [
                {
                    "name": "investigate_storage",
                    "description": "Answer a storage estate question with evidence and confidence.",
                },
                {
                    "name": "summarize_storage_portfolio",
                    "description": "Return scoped capacity, cost, savings, freshness, and risk metrics.",
                },
            ],
            "filters": list(SUPPORTED_FILTERS),
        }
