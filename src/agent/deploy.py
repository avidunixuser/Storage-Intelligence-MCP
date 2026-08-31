from __future__ import annotations

import json
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    OpenApiFunctionDefinition,
    OpenApiAgentTool,
    OpenApiManagedAuthDetails,
    OpenApiManagedSecurityScheme,
    PromptAgentDefinition,
)
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential

ROOT = Path(__file__).parent


def deploy_agent() -> dict[str, str]:
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5.4-mini")
    function_url = os.environ["FUNCTION_TOOL_BASE_URL"].rstrip("/")
    audience = os.environ["FUNCTION_TOOL_AUDIENCE"]
    agent_name = os.environ.get("STORAGE_AGENT_NAME", "storage-intelligence-agent")

    spec = json.loads((ROOT / "openapi.json").read_text(encoding="utf-8"))
    spec["servers"] = [{"url": function_url}]
    instructions = (ROOT / "instructions.md").read_text(encoding="utf-8")
    auth = OpenApiManagedAuthDetails(
        security_scheme=OpenApiManagedSecurityScheme(audience=audience)
    )
    tool = OpenApiAgentTool(
        openapi=OpenApiFunctionDefinition(
            name="storage_intelligence",
            spec=spec,
            description="Read-only deterministic storage analytics with evidence.",
            auth=auth,
        )
    )

    managed_identity_client_id = os.environ.get("AZURE_CLIENT_ID")
    with (
        DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id) as credential,
        AIProjectClient(credential=credential, endpoint=endpoint) as client,
    ):
        try:
            client.agents.get(agent_name)
            status = "updated"
        except ResourceNotFoundError:
            status = "created"
        version = client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=model,
                instructions=instructions,
                tools=[tool],
            ),
        )
        result = {
            "name": version.name,
            "version": str(version.version),
            "id": version.id,
            "status": status,
        }
        print(json.dumps(result))
        return result


def main() -> None:
    deploy_agent()


if __name__ == "__main__":
    main()
