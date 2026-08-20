from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from .cosmos_inventory import get_cosmos_container

DEFAULT_QUESTIONS = [
    "Which accounts grew abnormally last week?",
    "Which storage accounts should I worry about, and why?",
    "How much can we save by tiering cold data?",
    "Which accounts are negatively impacting Databricks?",
    "Why did storage costs increase last month?",
    "When will we need more capacity?",
    "Show a what-if comparison for 10%, 25%, and 50% tiering adoption.",
    "Which findings are based on incomplete data?",
    "Which lifecycle policies are missing?",
    "Where would Archive create rehydration or early-deletion risk?",
    "Which accounts have the highest transaction intensity?",
    "Where do versioning, snapshots, or soft delete create avoidable overhead?",
    "Which replication choices appear over-provisioned?",
    "What changed since the previous weekly review?",
    "What are the top five actions by savings, risk reduction, and effort?",
    "Which subscriptions are cost or capacity outliers?",
    "Compare risk across management groups and subsidiaries.",
    "Which tenant has the highest storage growth and monthly cost?",
    "Which stale accounts also have high cost or operational risk?",
    "Which SAP-linked storage accounts should be reviewed first?",
    "Which Azure Data Factory-linked accounts have the highest operational pressure?",
    "Where do Databricks small files and throttling overlap?",
    "Which accounts combine rapid growth with weak lifecycle coverage?",
    "Which subsidiaries have the largest defensible tiering opportunity?",
    "Compare storage risk, growth, and cost across Dev, QA, Perf, and Prod environments.",
    "Which storage accounts still use SAS tokens or shared keys?",
    "Which publicly accessible accounts have no private endpoint?",
    "Which accounts have no service-principal-based access enabled?",
    "Which NSG or ASG-linked accounts still expose public access?",
    "Which accounts lack GRS or GZRS resilience?",
    "Which defunct projects still retain storage accounts?",
    "Which projects have not accessed their storage in more than 180 days?",
    "Which SFTP-enabled storage accounts have public access or no private endpoint?",
    "Which accounts storing Application Insights data have weak security or resilience?",
]

QUESTION_PARTITION = "__agent_questions__"
MAX_CUSTOM_QUESTIONS = 100
QUESTION_LOCK = RLock()


class QuestionAlreadyExistsError(ValueError):
    pass


class QuestionLibraryFullError(ValueError):
    pass


def _normalized(question: str) -> str:
    return " ".join(question.split())


def _local_path() -> Path:
    return Path(os.getenv("SAVED_QUESTIONS_PATH", "data/saved-agent-questions.json"))


def _cosmos_enabled() -> bool:
    return os.getenv("COSMOS_INVENTORY_ENABLED", "false").lower() == "true"


def _load_custom_from_local() -> list[dict[str, Any]]:
    path = _local_path()
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Saved question library could not be read: {path}") from exc
    if not isinstance(value, list):
        raise RuntimeError(f"Saved question library must contain a JSON list: {path}")
    return [item for item in value if isinstance(item, dict) and item.get("question")]


def _load_custom_from_cosmos() -> list[dict[str, Any]]:
    container = get_cosmos_container()
    return list(
        container.query_items(
            query=(
                "SELECT c.id, c.question, c.created_at, c.created_by "
                "FROM c WHERE c.document_type = @document_type"
            ),
            parameters=[
                {"name": "@document_type", "value": "saved-agent-question"},
            ],
            partition_key=QUESTION_PARTITION,
        )
    )


def _custom_questions() -> list[dict[str, Any]]:
    records = _load_custom_from_cosmos() if _cosmos_enabled() else _load_custom_from_local()
    return sorted(records, key=lambda item: (str(item.get("created_at") or ""), str(item["question"])))


def list_questions() -> list[dict[str, Any]]:
    with QUESTION_LOCK:
        entries = [{"question": question, "custom": False} for question in DEFAULT_QUESTIONS]
        seen = {question.casefold() for question in DEFAULT_QUESTIONS}
        for item in _custom_questions():
            question = _normalized(str(item["question"]))
            if question.casefold() in seen:
                continue
            seen.add(question.casefold())
            entries.append(
                {
                    "question": question,
                    "custom": True,
                    "created_at": item.get("created_at"),
                }
            )
        return entries


def save_question(question: str, created_by: str) -> dict[str, Any]:
    with QUESTION_LOCK:
        normalized = _normalized(question)
        existing = list_questions()
        if any(item["question"].casefold() == normalized.casefold() for item in existing):
            raise QuestionAlreadyExistsError("This question is already in the investigation library")
        if sum(bool(item["custom"]) for item in existing) >= MAX_CUSTOM_QUESTIONS:
            raise QuestionLibraryFullError(
                f"The investigation library is limited to {MAX_CUSTOM_QUESTIONS} custom questions"
            )

        created_at = datetime.now(UTC).isoformat()
        item = {
            "id": f"agent-question-{hashlib.sha256(normalized.casefold().encode('utf-8')).hexdigest()}",
            "subscription_id": QUESTION_PARTITION,
            "document_type": "saved-agent-question",
            "schema_version": 1,
            "question": normalized,
            "created_at": created_at,
            "created_by": created_by,
        }
        if _cosmos_enabled():
            get_cosmos_container().upsert_item(body=item)
        else:
            path = _local_path()
            records = _load_custom_from_local()
            records.append(item)
            temporary = path.with_suffix(f"{path.suffix}.tmp")
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
                temporary.replace(path)
            except OSError as exc:
                raise RuntimeError(f"Saved question library could not be persisted: {path}") from exc
        return {
            "question": normalized,
            "custom": True,
            "created_at": created_at,
        }
