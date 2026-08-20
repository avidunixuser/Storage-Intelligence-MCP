#!/usr/bin/env sh
set -eu

eval "$(azd env get-values | sed 's/^/export /')"
IMAGE="${AZURE_CONTAINER_REGISTRY_ENDPOINT}/storage-intelligence:${AZURE_ENV_NAME}"
az acr build --registry "$AZURE_CONTAINER_REGISTRY_NAME" --image "storage-intelligence:${AZURE_ENV_NAME}" --file src/web/Dockerfile . --no-logs
az containerapp update --name "$SERVICE_WEB_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --image "$IMAGE" --output none
az ad app update \
  --id "$WEB_AUTH_CLIENT_ID" \
  --web-redirect-uris "${WEB_URL}/.auth/login/aad/callback" \
  --enable-id-token-issuance true \
  >/dev/null
