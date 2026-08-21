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

    subject, html_body, plain_text = render_notification([account])

    assert subject == "Action required: review 1 Azure Storage account"
    assert "<script>" not in html_body
    assert "&lt;script&gt;" in html_body
    assert "Project &lt;Critical&gt;" in html_body
    for heading in (
        "Account",
        "Subscription",
        "Management group",
        "Business unit",
        "Environment",
        "Region",
        "Tier",
        "Project",
        "Risk",
        "Key findings",
        "Recommended action",
    ):
        assert heading in html_body
        assert heading in plain_text
    assert "This notification is advisory and does not change Azure resources." in plain_text


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

    def fake_send(accounts):
        captured.extend(accounts)
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


def test_notification_ui_and_infrastructure_cover_every_account_surface():
    root = Path(__file__).parents[1]
    app_script = (root / "src" / "web" / "static" / "app.js").read_text(encoding="utf-8")
    styles = (root / "src" / "web" / "static" / "styles.css").read_text(encoding="utf-8")
    translations = (root / "src" / "web" / "static" / "translations.js").read_text(encoding="utf-8")
    workload = (root / "infra" / "app" / "workload.bicep").read_text(encoding="utf-8")
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")

    assert app_script.count("e(NotificationToolbar") == 6
    for surface in ("platform", "risk", "agent", "savings", "findings", "posture"):
        assert f'notifyProjectOwners("{surface}", ids)' in app_script
        assert f'toggleAccountSelection("{surface}"' in app_script
    assert 'fetch("/api/notifications/project-owners"' in app_script
    assert 'disabled: props.busy || props.selectedIds.length === 0' in app_script
    assert "function AccountCheckbox(props)" in app_script
    assert "function NotificationToolbar(props)" in app_script
    assert ".notify-owners-button:disabled" in styles
    assert ".account-select-control input:checked + .account-select-box" in styles
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
