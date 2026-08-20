from __future__ import annotations

import io
import os
import time
import zipfile
from pathlib import Path

import httpx
from azure.identity import DefaultAzureCredential


def _package_function(source_root: Path) -> bytes:
    required = [
        source_root / "function_app.py",
        source_root / "host.json",
        source_root / "requirements.txt",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Function package inputs are missing: {', '.join(missing)}")

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in required:
            archive.write(path, path.name)
        package_root = source_root / "storage_intelligence"
        for path in package_root.rglob("*.py"):
            archive.write(path, path.relative_to(source_root).as_posix())
        dependencies_root = Path(os.environ.get("FUNCTION_PACKAGES_ROOT", "/function-packages"))
        if not dependencies_root.exists():
            raise RuntimeError(f"Function dependencies are missing: {dependencies_root}")
        for path in dependencies_root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                target = Path(".python_packages/lib/site-packages") / path.relative_to(dependencies_root)
                archive.write(path, target.as_posix())
    return output.getvalue()


def deploy_function() -> dict[str, str | int]:
    function_name = os.environ["FUNCTION_APP_NAME"]
    client_id = os.environ["AZURE_CLIENT_ID"]
    source_root = Path(os.environ.get("FUNCTION_SOURCE_ROOT", "/app/src"))
    payload = _package_function(source_root)

    with DefaultAzureCredential(managed_identity_client_id=client_id) as credential:
        token = credential.get_token("https://management.azure.com/.default").token
        function_token = credential.get_token(f"{os.environ['FUNCTION_TOOL_AUDIENCE']}/.default").token
    endpoint = f"https://{function_name}.scm.azurewebsites.net/api/publish?type=zip"
    response = httpx.post(
        endpoint,
        content=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/zip",
        },
        timeout=300,
    )
    print(
        f"Function publish response: status={response.status_code} "
        f"location={response.headers.get('location')!r} body={response.text[:500]!r}"
    )
    if response.status_code not in {200, 202}:
        raise RuntimeError(f"Private Function deployment failed ({response.status_code}): {response.text[:1000]}")

    deployment_url = f"https://{function_name}.scm.azurewebsites.net/api/deployments/latest"
    for attempt in range(60):
        try:
            deployment = httpx.get(
                deployment_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if deployment.status_code == 200:
                details = deployment.json()
                status = int(details.get("status", 0))
                if attempt % 6 == 0:
                    print(
                        f"Function deployment attempt {attempt + 1}/60: "
                        f"status={status} message={details.get('message')!r}"
                    )
                if status == 4:
                    break
                if status == 3:
                    log_url = details.get("log_url")
                    log = ""
                    if log_url:
                        log_response = httpx.get(
                            log_url,
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=30,
                        )
                        log = log_response.text[:4000]
                    raise RuntimeError(f"Private Function build failed: {details}; log={log}")
        except httpx.HTTPError as exc:
            if attempt % 6 == 0:
                print(f"Function deployment status attempt {attempt + 1}/60 failed: {exc!r}")
        time.sleep(5)
    else:
        raise RuntimeError("Private Function deployment did not complete within five minutes.")

    health_url = f"https://{function_name}.azurewebsites.net/api/healthz"
    last_status = 0
    last_body = ""
    for attempt in range(72):
        try:
            health = httpx.get(
                health_url,
                headers={"Authorization": f"Bearer {function_token}"},
                timeout=15,
            )
        except httpx.HTTPError as exc:
            if attempt % 6 == 0:
                print(f"Function health attempt {attempt + 1}/72 failed: {exc!r}")
            time.sleep(5)
            continue
        last_status = health.status_code
        last_body = health.text[:500]
        if attempt % 6 == 0:
            print(
                f"Function health attempt {attempt + 1}/72: "
                f"status={last_status} body={last_body!r}"
            )
        if health.status_code == 200:
            return {
                "status": "deployed",
                "status_code": response.status_code,
                "function": function_name,
                "health": "passed",
            }
        time.sleep(5)
    raise RuntimeError(f"Private Function health failed ({last_status}): {last_body}")
