from __future__ import annotations

import json
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def invoke_agent(question: str | None = None) -> dict[str, str]:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    agent_name = os.environ.get("STORAGE_AGENT_NAME", "storage-intelligence-agent")
    prompt = question or os.environ.get(
        "AGENT_QUESTION",
        "Which storage accounts grew abnormally last week?",
    )
    managed_identity_client_id = os.environ.get("AZURE_CLIENT_ID")
    with (
        DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id) as credential,
        AIProjectClient(credential=credential, endpoint=endpoint) as project,
        project.get_openai_client() as openai,
    ):
        conversation = openai.conversations.create()
        response = openai.responses.create(
            conversation=conversation.id,
            input=prompt,
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        )
        result = {"conversation_id": conversation.id, "answer": response.output_text}
        print(json.dumps(result))
        return result


def main() -> None:
    invoke_agent()
