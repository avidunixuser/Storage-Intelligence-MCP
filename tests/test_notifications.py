from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from storage_intelligence import generate_accounts
from web.notifications import render_notification, send_project_owner_notification


class FakePoller:
    def result(self):
        return {"id": "operation-123", "status": "Succeeded"}


class FakeEmailClient:
    def __init__(self):
        self.message = None

    def begin_send(self, message):
        self.message = message
        return FakePoller()


def test_notification_template_is_actionable_and_escapes_account_data():
    account = dict(generate_accounts(1)[0])
    account["name"] = "<script>alert('x')</script>"
    account["project_name"] = "Project <Critical>"
    account["azure_data_factory"] = "adf-<critical>"

    subject, html_body, plain_text = render_notification([account])

    assert subject == "Action required: review 1 Azure Storage account"
    assert "<script>" not in html_body
    assert "&lt;script&gt;" in html_body
    assert "Project &lt;Critical&gt;" in html_body
    assert "Azure Data Factory: adf-&lt;critical&gt;" in html_body
    assert "Azure Data Factory: adf-<critical>" in plain_text
    assert 'background:#0078d4' in html_body
    assert 'background:#0f6cbd' in html_body
    assert "Microsoft Azure" in html_body
    assert "Storage Atlas" in html_body
    assert 'aria-label="Azure Storage accounts requiring owner review"' in html_body
    for heading in (
        "Storage account",
        "Subscription",
        "Management group",
        "Business unit",
        "Environment",
        "Region",
        "Tier",
        "Project",
        "Azure service usage",
        "Risk",
        "Key findings",
        "Recommended action",
    ):
        assert heading in html_body
        assert heading in plain_text
    assert "This notification is advisory and does not change Azure resources." in plain_text


def test_notification_template_lists_every_known_azure_service_association():
    account = dict(generate_accounts(1)[0])
    account.update(
        {
            "databricks_workspace": "dbw-analytics",
            "fabric_lakehouse": "lakehouse-sales",
            "sap_system": "SAP-S4HANA",
            "azure_data_factory": "adf-ingestion",
            "sftp_enabled": True,
            "application_insights_resource": "appi-orders",
            "azure_function_app": "func-processor",
            "log_analytics_workspace": "law-operations",
        }
    )

    _, html_body, plain_text = render_notification([account])

    associations = (
        "Azure Databricks: dbw-analytics",
        "Microsoft Fabric: lakehouse-sales",
        "SAP on Azure: SAP-S4HANA",
        "Azure Data Factory: adf-ingestion",
        "Azure Storage SFTP",
        "Application Insights: appi-orders",
        "Azure Functions: func-processor",
        "Log Analytics: law-operations",
    )
    for association in associations:
        assert association in html_body
        assert association in plain_text


def test_notification_template_marks_accounts_without_a_service_association():
    account = dict(generate_accounts(1)[0])
    for field in (
        "databricks_workspace",
        "fabric_lakehouse",
        "sap_system",
        "azure_data_factory",
        "sftp_enabled",
        "application_insights_resource",
        "azure_function_app",
        "log_analytics_workspace",
    ):
        account[field] = None

    _, html_body, plain_text = render_notification([account])

    assert "No linked Azure service recorded" in html_body
    assert "No linked Azure service recorded" in plain_text


def test_notification_template_uses_query_findings_and_tier_aligned_action():
    account = dict(generate_accounts(1)[0])
    account.update(
        {
            "public_network_access": True,
            "blob_public_access_enabled": True,
            "shared_key_access_enabled": True,
        }
    )
    finding = (
        "41.2 TB is eligible for Archive, producing $532.18 net monthly savings "
        "after $18.04 retrieval and operation costs."
    )
    question = "How much can we save by tiering <cold> data?"

    subject, html_body, plain_text = render_notification(
        [account],
        question=question,
        tool="cost.tier_savings",
        findings={account["account_id"]: finding},
    )

    assert subject == "Agent investigation: How much can we save by tiering <cold> data?"
    assert "How much can we save by tiering &lt;cold&gt; data?" in html_body
    assert f"Question: {question}" in plain_text
    assert finding in html_body
    assert finding in plain_text
    assert "Query finding" in html_body
    assert "Validate the proposed target tier against access patterns" in html_body
    assert "Disable public access" not in html_body
    assert "Migrate access to managed identity" not in html_body


def test_notification_sender_uses_dual_format_message_and_fixed_recipient():
    accounts = generate_accounts(2)
    client = FakeEmailClient()

    result = send_project_owner_notification(
        accounts,
        client=client,
        endpoint="https://acs.example.communication.azure.com",
        sender="DoNotReply@example.azurecomm.net",
        recipient="nrp@microsoft.com",
    )

    assert result == {
        "operation_id": "operation-123",
        "status": "Succeeded",
        "recipient": "nrp@microsoft.com",
        "account_count": 2,
    }
    assert client.message["senderAddress"] == "DoNotReply@example.azurecomm.net"
    assert client.message["recipients"]["to"] == [
        {
            "address": "nrp@microsoft.com",
            "displayName": "Storage Project Owner",
        }
    ]
    assert client.message["content"]["plainText"]
    assert client.message["content"]["html"].startswith("<!doctype html>")
    assert client.message["userEngagementTrackingDisabled"] is True


def test_notification_api_resolves_accounts_and_rejects_untrusted_input(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "true")
    from web import app as web_app

    selected = web_app.ACCOUNTS[:2]
    captured = []

    def fake_send(accounts, **kwargs):
        captured.extend(accounts)
        assert kwargs == {"question": None, "tool": None, "findings": None}
        return {
            "operation_id": "operation-api",
            "status": "Succeeded",
            "recipient": "nrp@microsoft.com",
            "account_count": len(accounts),
        }

    monkeypatch.setattr(web_app, "send_project_owner_notification", fake_send)
    client = TestClient(web_app.app)
    response = client.post(
        "/api/notifications/project-owners",
        json={"account_ids": [account["account_id"] for account in selected]},
    )

    assert response.status_code == 202
    assert response.json()["operation_id"] == "operation-api"
    assert [account["account_id"] for account in captured] == [
        account["account_id"] for account in selected
    ]
    assert client.post(
        "/api/notifications/project-owners",
        json={"account_ids": [selected[0]["account_id"], selected[0]["account_id"]]},
    ).status_code == 422
    assert client.post(
        "/api/notifications/project-owners",
        json={"account_ids": ["unknown-account-id"]},
    ).status_code == 422
    assert client.post(
        "/api/notifications/project-owners",
        json={"account_ids": [], "recipient": "attacker@example.com"},
    ).status_code == 422
    assert client.post(
        "/api/notifications/project-owners",
        json={"account_ids": [account["account_id"] for account in web_app.ACCOUNTS[:101]]},
    ).status_code == 422


def test_agent_notification_recomputes_and_sends_exact_query_findings(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "true")
    from web import app as web_app

    question = "How much can we save by tiering cold data?"
    investigation = web_app.ENGINE.answer(question)
    selected_reasons = investigation["account_reasons"][:2]
    selected_ids = [item["account_id"] for item in selected_reasons]
    captured = {}

    def fake_send(accounts, **kwargs):
        captured["accounts"] = accounts
        captured.update(kwargs)
        return {
            "operation_id": "operation-agent",
            "status": "Succeeded",
            "recipient": "nrp@microsoft.com",
            "account_count": len(accounts),
        }

    monkeypatch.setattr(web_app, "send_project_owner_notification", fake_send)
    client = TestClient(web_app.app)
    response = client.post(
        "/api/notifications/project-owners",
        json={
            "account_ids": selected_ids,
            "investigation": {"question": question, "filters": {}},
        },
    )

    assert response.status_code == 202
    assert captured["question"] == question
    assert captured["tool"] == "cost.tier_savings"
    assert captured["findings"] == {
        item["account_id"]: item["reason"] for item in selected_reasons
    }
    assert [account["account_id"] for account in captured["accounts"]] == selected_ids


def test_agent_notification_rejects_accounts_outside_recomputed_result(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "true")
    from web import app as web_app

    question = "How much can we save by tiering cold data?"
    result_ids = {
        item["account_id"] for item in web_app.ENGINE.answer(question)["account_reasons"]
    }
    mismatched_id = next(
        account["account_id"] for account in web_app.ACCOUNTS if account["account_id"] not in result_ids
    )

    client = TestClient(web_app.app)
    response = client.post(
        "/api/notifications/project-owners",
        json={
            "account_ids": [mismatched_id],
            "investigation": {"question": question, "filters": {}},
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["errors"] == [mismatched_id]


def test_notification_ui_and_infrastructure_cover_every_account_surface():
    root = Path(__file__).parents[1]
    app_script = (root / "src" / "web" / "static" / "app.js").read_text(encoding="utf-8")
    styles = (root / "src" / "web" / "static" / "styles.css").read_text(encoding="utf-8")
    translations = (root / "src" / "web" / "static" / "translations.js").read_text(encoding="utf-8")
    workload = (root / "infra" / "app" / "workload.bicep").read_text(encoding="utf-8")
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")

    assert app_script.count("e(NotificationToolbar") == 6
    for surface in ("platform", "risk", "savings", "findings", "posture"):
        assert f'notifyProjectOwners("{surface}", ids)' in app_script
        assert f'toggleAccountSelection("{surface}"' in app_script
        assert f'toggleVisibleAccountSelection("{surface}", ids, checked)' in app_script
    assert 'notifyProjectOwners("agent", ids, {' in app_script
    assert 'toggleAccountSelection("agent"' in app_script
    assert 'toggleVisibleAccountSelection("agent", ids, checked)' in app_script
    assert "question: response.question" in app_script
    assert "filters: response.scope.filters || {}" in app_script
    assert "investigation: investigation || undefined" in app_script
    assert 'fetch("/api/notifications/project-owners"' in app_script
    assert 'disabled: props.busy || props.selectedIds.length === 0' in app_script
    assert "function AccountCheckbox(props)" in app_script
    assert "function NotificationToolbar(props)" in app_script
    assert "function toggleVisibleAccountSelection(surface, visibleIds, checked)" in app_script
    assert 'text: "Select all"' in app_script
    assert 'indeterminate: partiallySelected' in app_script
    assert "const visibleIds = Array.from(new Set(props.visibleIds || []));" in app_script
    assert "for (let index = 0; index < uniqueIds.length; index += 100)" in app_script
    assert '" across " + operationIds.length + " batch(es)."' in app_script
    assert '" of " + uniqueIds.length + " account(s) were accepted."' in app_script
    assert "const acceptedIds = new Set(batch);" in app_script
    assert app_script.count("visibleIds:") == 6
    assert app_script.count("onSelectAll:") == 7
    assert ".notify-owners-button:disabled" in styles
    assert ".account-select-control input:checked + .account-select-box" in styles
    assert ".account-select-control input:indeterminate + .account-select-box" in styles
    assert '"Notify project owners": "Notificar a los propietarios del proyecto"' in translations

    assert "azure-communication-email==1.1.0" in pyproject
    assert "Microsoft.Communication/emailServices@2023-04-01" in workload
    assert "Microsoft.Communication/emailServices/domains@2023-04-01" in workload
    assert "Microsoft.Communication/communicationServices@2025-05-01" in workload
    assert "domainManagement: 'AzureManaged'" in workload
    assert "dataLocation: 'Europe'" in workload
    assert "disableLocalAuth: true" in workload
    assert "09976791-48a7-449e-bb21-39d1a415f350" in workload
    assert "AZURE_COMMUNICATION_EMAIL_ENDPOINT" in workload
    assert "AZURE_COMMUNICATION_EMAIL_SENDER" in workload
    assert "PROJECT_OWNER_NOTIFICATION_RECIPIENT" in workload
    assert "nrp@microsoft.com" in workload
    assert "listKeys()" not in workload
