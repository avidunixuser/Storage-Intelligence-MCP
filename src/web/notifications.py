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

AZURE_SERVICE_FIELDS = (
    ("databricks_workspace", "Azure Databricks"),
    ("fabric_lakehouse", "Microsoft Fabric"),
    ("sap_system", "SAP on Azure"),
    ("azure_data_factory", "Azure Data Factory"),
    ("sftp_enabled", "Azure Storage SFTP"),
    ("application_insights_resource", "Application Insights"),
    ("azure_function_app", "Azure Functions"),
    ("log_analytics_workspace", "Log Analytics"),
)


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


def _azure_service_usage(account: dict[str, Any]) -> str:
    services: list[str] = []
    for field, label in AZURE_SERVICE_FIELDS:
        value = account.get(field)
        if not value:
            continue
        services.append(label if value is True else f"{label}: {value}")
    return "; ".join(services) or "No linked Azure service recorded"


def _investigation_action(tool: str | None) -> str:
    if tool == "cost.tier_savings":
        return (
            "Validate the proposed target tier against access patterns, retrieval and operation "
            "charges, and early-deletion exposure before implementation."
        )
    if tool and tool.startswith("cost."):
        return "Validate the identified cost driver or savings opportunity and agree an owner action."
    if tool and tool.startswith("capacity."):
        return "Validate the capacity signal and update the growth, lifecycle, or capacity plan."
    if tool and tool.startswith("databricks."):
        return "Review the storage finding with the Databricks owner and validate the proposed remediation."
    if tool and tool.startswith("evidence."):
        return "Refresh or validate the cited evidence before making a remediation decision."
    if tool and tool.startswith("risk."):
        return "Review the described risk with the project owner and record a remediation date."
    if tool and tool.startswith("portfolio."):
        return "Review the portfolio finding with accountable owners and record the agreed next step."
    return "Review this query-specific finding with the project owner and record the agreed next step."


def notification_rows(
    accounts: list[dict[str, Any]],
    *,
    findings: dict[str, str] | None = None,
    tool: str | None = None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for account in accounts:
        risk = risk_score(account)
        factors = [str(factor) for factor in risk["risk_factors"]]
        account_id = str(account["account_id"])
        query_finding = findings.get(account_id) if findings is not None else None
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
                "azure_service_usage": _azure_service_usage(account),
                "signal": "Query finding" if findings is not None else f"Risk {risk['score']}/100",
                "signal_tone": "#0f6cbd"
                if findings is not None
                else "#a4262c"
                if risk["score"] >= AT_RISK_THRESHOLD
                else "#8a6d1d",
                "findings": query_finding
                if query_finding
                else "; ".join(factors[:5])
                if factors
                else "No explicit risk factor recorded",
                "action": _investigation_action(tool)
                if findings is not None
                else _recommended_action(account, factors, risk["score"]),
            }
        )
    return rows


def render_notification(
    accounts: list[dict[str, Any]],
    *,
    question: str | None = None,
    tool: str | None = None,
    findings: dict[str, str] | None = None,
) -> tuple[str, str, str]:
    normalized_question = " ".join(question.split()) if question else None
    rows = notification_rows(accounts, findings=findings, tool=tool)
    subject = (
        f"Agent investigation: {normalized_question[:120]}"
        if normalized_question
        else f"Action required: review {len(rows)} Azure Storage account{'s' if len(rows) != 1 else ''}"
    )
    body_rows: list[str] = []
    for index, row in enumerate(rows):
        background = "#ffffff" if index % 2 == 0 else "#f7fafd"
        body_rows.append(
            f'<tr style="background:{background}">'
            '<td style="border-bottom:1px solid #dbe6f1;padding:14px 12px;vertical-align:top">'
            f'<strong style="color:#0f3b5d;font-size:14px">{html.escape(row["account"])}</strong>'
            f'<div style="color:#5b7083;font-size:11px;margin-top:4px">Subscription · '
            f'{html.escape(row["subscription"])}</div>'
            "</td>"
            '<td style="border-bottom:1px solid #dbe6f1;padding:14px 12px;vertical-align:top">'
            f'<div style="color:#0f6cbd;font-weight:600">{html.escape(row["azure_service_usage"])}</div>'
            "</td>"
            '<td style="border-bottom:1px solid #dbe6f1;padding:14px 12px;vertical-align:top">'
            f'<strong>Management group · {html.escape(row["management_group"])}</strong>'
            f'<div style="color:#5b7083;margin-top:4px">Business unit · '
            f'{html.escape(row["business_unit"])}</div>'
            "</td>"
            '<td style="border-bottom:1px solid #dbe6f1;padding:14px 12px;vertical-align:top">'
            f'<strong>Environment · {html.escape(row["environment"])}</strong>'
            f'<div style="color:#5b7083;margin-top:4px">Region · {html.escape(row["region"])}'
            f'<br>Tier · {html.escape(row["tier"])}</div>'
            "</td>"
            '<td style="border-bottom:1px solid #dbe6f1;padding:14px 12px;vertical-align:top">'
            f'<strong>Project · {html.escape(row["project"])}</strong>'
            f'<div style="color:{row["signal_tone"]};font-weight:700;margin-top:6px">'
            f'{html.escape(row["signal"])}</div>'
            "</td>"
            '<td style="border-bottom:1px solid #dbe6f1;padding:14px 12px;vertical-align:top">'
            f'<div style="color:#334e68">{html.escape(row["findings"])}</div>'
            f'<div style="border-left:3px solid #0078d4;color:#0f3b5d;margin-top:10px;padding-left:9px">'
            f'<strong>Recommended action</strong><br>{html.escape(row["action"])}</div>'
            "</td>"
            "</tr>"
        )
    heading = "Agent Investigation owner review" if normalized_question else "Azure Storage account review requested"
    question_summary = (
        '<table role="presentation" style="border-collapse:collapse;margin-top:18px;width:100%"><tr>'
        '<td style="background:#e8f3fc;border-left:4px solid #0078d4;border-radius:4px;color:#0f3b5d;'
        f'font-size:13px;padding:12px 14px"><strong>Question:</strong> {html.escape(normalized_question)}</td>'
        "</tr></table>"
        if normalized_question
        else ""
    )
    review_scope = (
        "Query-specific findings, Azure service associations, governance context, and aligned owner actions."
        if normalized_question
        else "Azure service associations, governance context, risk signals, and recommended actions."
    )
    html_body = (
        '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        '<body style="background:#eef3f8;color:#1c2b3a;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:24px">'
        '<table role="presentation" style="border-collapse:collapse;margin:0 auto;max-width:1200px;width:100%">'
        '<tr><td style="background:#0078d4;border-radius:10px 10px 0 0;color:#ffffff;padding:24px 28px">'
        '<div style="font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase">Microsoft Azure</div>'
        '<div style="font-size:26px;font-weight:700;margin-top:5px">Storage Atlas</div>'
        '<div style="color:#deecf9;font-size:14px;margin-top:6px">Project owner action notification</div>'
        "</td></tr>"
        '<tr><td style="background:#ffffff;padding:26px 28px 14px">'
        f'<h1 style="color:#0f3b5d;font-size:21px;margin:0 0 10px">{heading}</h1>'
        '<p style="color:#445d70;font-size:14px;line-height:1.55;margin:0">Storage Atlas identified '
        f'<strong>{len(rows)} account{"s" if len(rows) != 1 else ""}</strong> for owner review. '
        "Validate the findings, confirm the accountable project owner, and record a remediation date.</p>"
        f"{question_summary}"
        '<table role="presentation" style="border-collapse:collapse;margin-top:18px;width:100%"><tr>'
        '<td style="background:#e8f3fc;border-left:4px solid #0078d4;border-radius:4px;color:#0f3b5d;'
        'font-size:13px;padding:12px 14px"><strong>Review scope:</strong> '
        f"{review_scope}</td></tr></table>"
        "</td></tr>"
        '<tr><td style="background:#ffffff;padding:12px 28px 28px">'
        '<table aria-label="Azure Storage accounts requiring owner review" role="table" '
        'style="border:1px solid #c7d8e8;border-collapse:separate;border-radius:7px;border-spacing:0;'
        'font-size:12px;overflow:hidden;width:100%">'
        '<thead><tr style="background:#0f6cbd;color:#ffffff">'
        '<th style="padding:11px 12px;text-align:left">Storage account</th>'
        '<th style="padding:11px 12px;text-align:left">Azure service usage</th>'
        '<th style="padding:11px 12px;text-align:left">Management group / business unit</th>'
        '<th style="padding:11px 12px;text-align:left">Environment / region / tier</th>'
        '<th style="padding:11px 12px;text-align:left">Project / risk or query signal</th>'
        '<th style="padding:11px 12px;text-align:left">Key findings / action</th>'
        f'</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'
        "</td></tr>"
        '<tr><td style="background:#f7fafd;border-top:1px solid #dbe6f1;border-radius:0 0 10px 10px;'
        'color:#617386;font-size:11px;line-height:1.5;padding:16px 28px">'
        "<strong>Advisory only.</strong> This notification does not change Azure resources. "
        "Service associations reflect the latest inventory metadata available to Storage Atlas."
        "</td></tr></table></body></html>"
    )
    columns = [
        ("account", "Storage account"),
        ("subscription", "Subscription"),
        ("management_group", "Management group"),
        ("business_unit", "Business unit"),
        ("environment", "Environment"),
        ("region", "Region"),
        ("tier", "Tier"),
        ("project", "Project"),
        ("azure_service_usage", "Azure service usage"),
        ("signal", "Risk / query signal"),
        ("findings", "Key findings"),
        ("action", "Recommended action"),
    ]
    plain_lines = [
        "MICROSOFT AZURE | STORAGE ATLAS",
        "Azure Storage account review requested",
        "",
        *([f"Question: {normalized_question}", ""] if normalized_question else []),
        "Validate the findings, assign an accountable owner, and record a remediation date.",
        "",
        " | ".join(label for _, label in columns),
        " | ".join("---" for _ in columns),
    ]
    plain_lines.extend(" | ".join(row[key] for key, _ in columns) for row in rows)
    plain_lines.extend(
        [
            "",
            "This notification is advisory and does not change Azure resources.",
            "Service associations reflect the latest inventory metadata available to Storage Atlas.",
        ]
    )
    return subject, html_body, "\n".join(plain_lines)


def _result_value(result: Any, key: str) -> str:
    if isinstance(result, dict):
        return str(result.get(key, ""))
    return str(getattr(result, key, ""))


def send_project_owner_notification(
    accounts: list[dict[str, Any]],
    *,
    question: str | None = None,
    tool: str | None = None,
    findings: dict[str, str] | None = None,
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
    subject, html_body, plain_text = render_notification(
        accounts,
        question=question,
        tool=tool,
        findings=findings,
    )
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
