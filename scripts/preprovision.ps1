$ErrorActionPreference = 'Stop'

if (-not $env:AZURE_ENV_NAME) {
    throw 'AZURE_ENV_NAME is required.'
}

$subscription = if ($env:AZURE_SUBSCRIPTION_ID) {
    $env:AZURE_SUBSCRIPTION_ID
} else {
    az account show --query id -o tsv
}
az account set --subscription $subscription

$principalId = az ad signed-in-user show --query id -o tsv
azd env set AZURE_PRINCIPAL_ID $principalId | Out-Null
if (-not $env:AZURE_LOCATION) {
    throw 'AZURE_LOCATION is required.'
}
azd env set AZURE_LOCATION $env:AZURE_LOCATION | Out-Null

foreach ($provider in @(
    'Microsoft.App',
    'Microsoft.CognitiveServices',
    'Microsoft.ContainerRegistry',
    'Microsoft.DocumentDB',
    'Microsoft.DurableTask',
    'Microsoft.Insights',
    'Microsoft.KeyVault',
    'Microsoft.ManagedIdentity',
    'Microsoft.Network',
    'Microsoft.OperationalInsights',
    'Microsoft.Search',
    'Microsoft.Storage',
    'Microsoft.Web'
)) {
    az provider register --namespace $provider | Out-Null
}

function Ensure-EntraApplication([string]$displayName, [string]$configuredAppId) {
    $appId = $configuredAppId
    if ($appId) {
        az ad app show --id $appId --query appId -o tsv | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Configured Entra application '$appId' was not found."
        }
    } else {
        $appId = az ad app list --filter "displayName eq '$displayName'" --query "[0].appId" -o tsv
    }
    if (-not $appId) {
        $appId = az ad app create --display-name $displayName --sign-in-audience AzureADMyOrg --query appId -o tsv
    }
    az ad app update --id $appId --display-name $displayName --identifier-uris "api://$appId" | Out-Null
    return $appId
}

$webAppId = Ensure-EntraApplication "Storage Atlas Web - $($env:AZURE_ENV_NAME)" $env:WEB_AUTH_CLIENT_ID
$functionAppId = Ensure-EntraApplication "Storage Atlas Tools - $($env:AZURE_ENV_NAME)" $env:FUNCTION_AUTH_CLIENT_ID
$adminRoleId = 'df3e3a1f-7f91-4cb7-a9f6-848ef6fb7a5b'
$adminAppRoles = '[{"allowedMemberTypes":["User"],"description":"Manage read-only storage discovery and schedules.","displayName":"Storage Atlas Admin","id":"' + $adminRoleId + '","isEnabled":true,"value":"StorageIntelligence.Admin"}]'
$adminRoleFile = [System.IO.Path]::GetTempFileName()
try {
    Set-Content -LiteralPath $adminRoleFile -Value $adminAppRoles -NoNewline
    az ad app update --id $webAppId --enable-id-token-issuance true --app-roles "@$adminRoleFile" | Out-Null
} finally {
    Remove-Item -LiteralPath $adminRoleFile -Force
}

$webServicePrincipalId = az ad sp list --filter "appId eq '$webAppId'" --query "[0].id" -o tsv
if (-not $webServicePrincipalId) {
    $webServicePrincipalId = az ad sp create --id $webAppId --query id -o tsv
}
$assignmentCount = az rest `
    --method get `
    --url "https://graph.microsoft.com/v1.0/users/$principalId/appRoleAssignments" `
    --query "length(value[?resourceId=='$webServicePrincipalId' && appRoleId=='$adminRoleId'])" `
    -o tsv
if ($assignmentCount -eq '0') {
    $assignmentBody = @{
        principalId = $principalId
        resourceId = $webServicePrincipalId
        appRoleId = $adminRoleId
    } | ConvertTo-Json -Compress
    az rest `
        --method post `
        --url "https://graph.microsoft.com/v1.0/servicePrincipals/$webServicePrincipalId/appRoleAssignedTo" `
        --headers 'Content-Type=application/json' `
        --body $assignmentBody | Out-Null
}
azd env set WEB_AUTH_CLIENT_ID $webAppId | Out-Null
azd env set FUNCTION_AUTH_CLIENT_ID $functionAppId | Out-Null

Write-Output "Prepared Entra applications and required providers for $($env:AZURE_ENV_NAME)."
