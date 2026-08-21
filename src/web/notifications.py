from __future__ import annotations

import html
import os
from functools import lru_cache
from typing import Any, Protocol

from azure.communication.email import EmailClient
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ServiceRequestError,
    ServiceResponseError,
)
from azure.identity import DefaultAzureCredential

from storage_intelligence.analytics import AT_RISK_THRESHOLD, risk_score


class NotificationConfigurationError(RuntimeError):
    pass


class NotificationDeliveryError(RuntimeError):
    pass


class EmailPoller(Protocol):
    def result(self) -> Any: ...


class EmailSender(Protocol):
    def begin_send(self, message: dict[str, Any]) -> EmailPoller: ...


def _required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise NotificationConfigurationError(f"{name} is required for owner notifications")
    return value


@lru_cache(maxsize=4)
def _email_client(endpoint: str, managed_identity_client_id: str | None) -> EmailClient:
    credential = DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
    return EmailClient(endpoint, credential)


def _recommended_action(account: dict[str, Any], factors: list[str], score: float) -> str:
    if account.get("public_network_access") or account.get("blob_public_access_enabled"):
        return "Disable public access and validate approved private-endpoint connectivity."
    if account.get("uses_sas_keys") or account.get("shared_key_access_enabled"):
        return "Migrate access to managed identity, then disable shared-key and SAS access."
    if account.get("private_endpoint_enabled") is False:
        return "Create or validate an approved private endpoint before restricting public access."
    if account.get("project_defunct") is True:
        return "Confirm ownership and retention requirements, then archive or retire the account."
    if not account.get("lifecycle_policy"):
        return "Define and validate a lifecycle policy against access and retention requirements."
    if score >= AT_RISK_THRESHOLD or factors:
        return "Review the listed findings with the project and platform owners and record a remediation date."
    return "Validate the current posture and confirm the accountable project owner."


def notification_rows(accounts: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for account in accounts:
        risk = risk_score(account)
        factors = [str(factor) for factor in risk["risk_factors"]]
        rows.append(
            {
                "account": str(account["name"]),
                "subscription": str(account["subscription"]),
                "management_group": str(account["management_group"]),
                "business_unit": str(account.get("subsidiary") or account.get("business_unit") or "Unassigned"),
                "environment": str(account["environment"]),
                "region": str(account["region"]),
                "tier": str(account["tier"]),
                "project": str(account.get("project_name") or "Unassigned"),
                "risk": f"{risk['score']}/100",
                "findings": "; ".join(factors[:5]) if factors else "No explicit risk factor recorded",
                "action": _recommended_action(account, factors, risk["score"]),
            }
        )
    return rows


def render_notification(accounts: list[dict[str, Any]]) -> tuple[str, str, str]:
    rows = notification_rows(accounts)
    subject = f"Action required: review {len(rows)} Azure Storage account{'s' if len(rows) != 1 else ''}"
    columns = [
        ("account", "Account"),
        ("subscription", "Subscription"),
        ("management_group", "Management group"),
        ("business_unit", "Business unit"),
        ("environment", "Environment"),
        ("region", "Region"),
        ("tier", "Tier"),
        ("project", "Project"),
        ("risk", "Risk"),
        ("findings", "Key findings"),
        ("action", "Recommended action"),
    ]
    header_cells = "".join(
        f'<th style="border:1px solid #cbd5e1;background:#eaf1f8;padding:8px;text-align:left">{html.escape(label)}</th>'
        for _, label in columns
    )
    body_rows = "".join(
        "<tr>"
        + "".join(
            f'<td style="border:1px solid #cbd5e1;padding:8px;vertical-align:top">{html.escape(row[key])}</td>'
            for key, _ in columns
        )
        + "</tr>"
        for row in rows
    )
    html_body = (
        "<!doctype html><html><body style=\"font-family:Segoe UI,Arial,sans-serif;color:#1c2b3a\">"
        "<h2>Azure Storage account review requested</h2>"
        "<p>The Storage Intelligence application identified the following accounts for owner review. "
        "Please validate the findings, assign an accountable owner, and record a remediation date.</p>"
        '<table style="border-collapse:collapse;width:100%;font-size:12px"><thead><tr>'
        f"{header_cells}</tr></thead><tbody>{body_rows}</tbody></table>"
        "<p style=\"color:#617386;font-size:11px\">This notification is advisory and does not change Azure resources.</p>"
        "</body></html>"
    )
    plain_lines = [
        "Azure Storage account review requested",
        "",
        "Validate the findings, assign an accountable owner, and record a remediation date.",
        "",
        " | ".join(label for _, label in columns),
        " | ".join("---" for _ in columns),
    ]
    plain_lines.extend(" | ".join(row[key] for key, _ in columns) for row in rows)
    plain_lines.extend(["", "This notification is advisory and does not change Azure resources."])
    return subject, html_body, "\n".join(plain_lines)


def _result_value(result: Any, key: str) -> str:
    if isinstance(result, dict):
        return str(result.get(key, ""))
    return str(getattr(result, key, ""))


def send_project_owner_notification(
    accounts: list[dict[str, Any]],
    *,
    client: EmailSender | None = None,
    endpoint: str | None = None,
    sender: str | None = None,
    recipient: str | None = None,
) -> dict[str, Any]:
    if not accounts:
        raise ValueError("At least one storage account is required")

    endpoint = endpoint or _required_setting("AZURE_COMMUNICATION_EMAIL_ENDPOINT")
    sender = sender or _required_setting("AZURE_COMMUNICATION_EMAIL_SENDER")
    recipient = recipient or _required_setting("PROJECT_OWNER_NOTIFICATION_RECIPIENT")
    managed_identity_client_id = os.getenv("AZURE_CLIENT_ID", "").strip() or None
    email_client = client or _email_client(endpoint, managed_identity_client_id)
    subject, html_body, plain_text = render_notification(accounts)
    message = {
        "senderAddress": sender,
        "recipients": {
            "to": [
                {
                    "address": recipient,
                    "displayName": "Storage Project Owner",
                }
            ]
        },
        "content": {
            "subject": subject,
            "plainText": plain_text,
            "html": html_body,
        },
        "userEngagementTrackingDisabled": True,
    }
    try:
        result = email_client.begin_send(message).result()
    except (
        ClientAuthenticationError,
        HttpResponseError,
        ServiceRequestError,
        ServiceResponseError,
    ) as exc:
        raise NotificationDeliveryError("Azure Communication Services did not accept the email") from exc

    status = _result_value(result, "status")
    operation_id = _result_value(result, "id")
    if status.casefold() != "succeeded":
        raise NotificationDeliveryError(f"Azure Communication Services email operation ended with status {status}")
    return {
        "operation_id": operation_id,
        "status": status,
        "recipient": recipient,
        "account_count": len(accounts),
    }
