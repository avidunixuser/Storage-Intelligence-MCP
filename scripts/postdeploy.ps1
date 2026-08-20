$ErrorActionPreference = 'Stop'

azd env get-values | ForEach-Object {
    if ($_ -match '^([^=]+)="(.*)"$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

$image = "$($env:AZURE_CONTAINER_REGISTRY_ENDPOINT)/storage-intelligence:$($env:AZURE_ENV_NAME)"
az acr build `
    --registry $env:AZURE_CONTAINER_REGISTRY_NAME `
    --image "storage-intelligence:$($env:AZURE_ENV_NAME)" `
    --file src/web/Dockerfile `
    . `
    --no-logs

az containerapp update `
    --name $env:SERVICE_WEB_NAME `
    --resource-group $env:AZURE_RESOURCE_GROUP `
    --image $image `
    --output none

$redirect = "$($env:WEB_URL)/.auth/login/aad/callback"
az ad app update `
    --id $env:WEB_AUTH_CLIENT_ID `
    --web-redirect-uris $redirect `
    --enable-id-token-issuance true | Out-Null

Write-Output "Deployed web image and Entra redirect. The VNet-integrated web revision creates or verifies the Foundry agent."
