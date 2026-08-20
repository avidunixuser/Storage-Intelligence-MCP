from __future__ import annotations

import asyncio
import os
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import TaskUpdater
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentProvider,
    AgentSkill,
    Part,
    Task,
    TaskState,
    TaskStatus,
)
from fastapi import FastAPI
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct, Value

from .service import StorageIntelligenceService


def _metadata_filters(context: RequestContext) -> dict[str, str]:
    if not context.message or not context.message.metadata:
        return {}
    metadata = MessageToDict(context.message.metadata)
    raw_filters = metadata.get("filters", {})
    if not isinstance(raw_filters, dict):
        raise ValueError("A2A message metadata.filters must be an object")
    return {str(key): str(value) for key, value in raw_filters.items()}


class StorageIntelligenceAgentExecutor(AgentExecutor):
    def __init__(self, service: StorageIntelligenceService):
        self._service = service
        self._running_tasks: set[str] = set()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if not context.message or not context.task_id or not context.context_id:
            raise ValueError("A2A request requires a message, task ID, and context ID")

        self._running_tasks.add(context.task_id)
        await event_queue.enqueue_event(
            Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                history=[context.message],
            )
        )
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.start_work(
            message=updater.new_agent_message(
                [Part(text="Running deterministic storage intelligence analysis.")]
            )
        )

        try:
            result = await asyncio.to_thread(
                self._service.investigate,
                context.get_user_input(),
                _metadata_filters(context),
            )
            if context.task_id not in self._running_tasks:
                return
            structured = Struct()
            structured.update(result)
            await updater.add_artifact(
                parts=[
                    Part(text=result["answer"]),
                    Part(data=Value(struct_value=structured)),
                ],
                name="storage-intelligence-result",
                metadata={"contentType": "application/json", "readOnly": True},
                last_chunk=True,
            )
            await updater.complete()
        except ValueError as exc:
            await updater.failed(
                message=updater.new_agent_message([Part(text=str(exc))])
            )
        finally:
            self._running_tasks.discard(context.task_id)

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if not context.task_id or not context.context_id:
            raise ValueError("A2A cancellation requires a task ID and context ID")
        self._running_tasks.discard(context.task_id)
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


def build_agent_card(public_url: str | None = None) -> AgentCard:
    base_url = (public_url or os.getenv("A2A_PUBLIC_URL") or "http://localhost:8000").rstrip("/")
    return AgentCard(
        name="Storage Intelligence Agent",
        description=(
            "Read-only Azure Storage estate analysis with deterministic evidence, "
            "scope, assumptions, and confidence."
        ),
        provider=AgentProvider(
            organization="Storage Intelligence",
            url=base_url,
        ),
        version="0.1.0",
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
        ),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain", "application/json"],
        skills=[
            AgentSkill(
                id="investigate-storage-estate",
                name="Investigate storage estate",
                description=(
                    "Analyze storage capacity, cost, growth, savings, freshness, "
                    "configuration, security, governance, and platform relationships."
                ),
                tags=["azure-storage", "finops", "dataops", "read-only"],
                examples=[
                    "Which storage accounts grew abnormally last week?",
                    "Which publicly accessible accounts have no private endpoint?",
                    "How much can we save by tiering cold data?",
                ],
                input_modes=["text/plain"],
                output_modes=["text/plain", "application/json"],
            )
        ],
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version="1.0",
                url=f"{base_url}/a2a",
            ),
            AgentInterface(
                protocol_binding="HTTP+JSON",
                protocol_version="1.0",
                url=f"{base_url}/a2a/rest",
            ),
        ],
    )


def register_a2a_routes(
    app: FastAPI,
    service: StorageIntelligenceService,
    public_url: str | None = None,
) -> AgentCard:
    card = build_agent_card(public_url)
    handler = DefaultRequestHandler(
        agent_executor=StorageIntelligenceAgentExecutor(service),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(agent_card=card),
        jsonrpc_routes=create_jsonrpc_routes(
            request_handler=handler,
            rpc_url="/a2a",
        ),
        rest_routes=create_rest_routes(
            request_handler=handler,
            path_prefix="/a2a/rest",
        ),
    )
    return card
