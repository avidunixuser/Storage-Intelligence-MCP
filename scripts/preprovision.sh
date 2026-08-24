#!/usr/bin/env sh
set -eu

: "${AZURE_ENV_NAME:?AZURE_ENV_NAME is required}"
: "${AZURE_LOCATION:?AZURE_LOCATION is required}"
AZURE_SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}"
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
AZURE_PRINCIPAL_ID="$(az ad signed-in-user show --query id -o tsv)"
azd env set AZURE_PRINCIPAL_ID "$AZURE_PRINCIPAL_ID"
azd env set AZURE_LOCATION "$AZURE_LOCATION"

for provider in Microsoft.App Microsoft.CognitiveServices Microsoft.ContainerRegistry Microsoft.DocumentDB Microsoft.DurableTask Microsoft.Insights Microsoft.KeyVault Microsoft.ManagedIdentity Microsoft.Network Microsoft.OperationalInsights Microsoft.Search Microsoft.Storage Microsoft.Web; do
  az provider register --namespace "$provider" >/dev/null
done

ensure_app() {
  display_name="$1"
  app_id="$(az ad app list --filter "displayName eq '$display_name'" --query '[0].appId' -o tsv)"
  if [ -z "$app_id" ]; then
    app_id="$(az ad app create --display-name "$display_name" --sign-in-audience AzureADMyOrg --query appId -o tsv)"
  fi
  az ad app update --id "$app_id" --identifier-uris "api://$app_id" >/dev/null
  printf '%s' "$app_id"
}

WEB_AUTH_CLIENT_ID="$(ensure_app "Storage Atlas Web - $AZURE_ENV_NAME")"
FUNCTION_AUTH_CLIENT_ID="$(ensure_app "Storage Atlas Tools - $AZURE_ENV_NAME")"
ADMIN_ROLE_ID="df3e3a1f-7f91-4cb7-a9f6-848ef6fb7a5b"
ADMIN_APP_ROLES="[{\"allowedMemberTypes\":[\"User\"],\"description\":\"Manage read-only storage discovery and schedules.\",\"displayName\":\"Storage Atlas Admin\",\"id\":\"$ADMIN_ROLE_ID\",\"isEnabled\":true,\"value\":\"StorageIntelligence.Admin\"}]"
ADMIN_ROLE_FILE="$(mktemp)"
trap 'rm -f "$ADMIN_ROLE_FILE"' EXIT
printf '%s' "$ADMIN_APP_ROLES" >"$ADMIN_ROLE_FILE"
az ad app update \
  --id "$WEB_AUTH_CLIENT_ID" \
  --enable-id-token-issuance true \
  --app-roles "@$ADMIN_ROLE_FILE" \
  >/dev/null

WEB_SERVICE_PRINCIPAL_ID="$(az ad sp list --filter "appId eq '$WEB_AUTH_CLIENT_ID'" --query '[0].id' -o tsv)"
if [ -z "$WEB_SERVICE_PRINCIPAL_ID" ]; then
  WEB_SERVICE_PRINCIPAL_ID="$(az ad sp create --id "$WEB_AUTH_CLIENT_ID" --query id -o tsv)"
fi
ASSIGNMENT_COUNT="$(az rest \
  --method get \
  --url "https://graph.microsoft.com/v1.0/users/$AZURE_PRINCIPAL_ID/appRoleAssignments" \
  --query "length(value[?resourceId=='$WEB_SERVICE_PRINCIPAL_ID' && appRoleId=='$ADMIN_ROLE_ID'])" \
  -o tsv)"
if [ "$ASSIGNMENT_COUNT" = "0" ]; then
  az rest \
    --method post \
    --url "https://graph.microsoft.com/v1.0/servicePrincipals/$WEB_SERVICE_PRINCIPAL_ID/appRoleAssignedTo" \
    --headers "Content-Type=application/json" \
    --body "{\"principalId\":\"$AZURE_PRINCIPAL_ID\",\"resourceId\":\"$WEB_SERVICE_PRINCIPAL_ID\",\"appRoleId\":\"$ADMIN_ROLE_ID\"}" \
    >/dev/null
fi
azd env set WEB_AUTH_CLIENT_ID "$WEB_AUTH_CLIENT_ID"
azd env set FUNCTION_AUTH_CLIENT_ID "$FUNCTION_AUTH_CLIENT_ID"
