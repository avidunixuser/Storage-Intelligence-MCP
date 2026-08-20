targetScope = 'subscription'

@minLength(1)
@maxLength(40)
param environmentName string

@allowed([
  'swedencentral'
])
param location string = 'swedencentral'

param principalId string
param webAuthClientId string
param functionAuthClientId string

var token = take(toLower(uniqueString(subscription().id, environmentName, location)), 8)
var resourceGroupName = 'rg-storage-intel-${environmentName}'
var tags = {
  'azd-env-name': environmentName
  application: 'storage-intelligence-agent'
  environment: environmentName
  workload: 'synthetic-pilot'
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module foundryOwner './app/foundry-owner.bicep' = {
  name: 'foundry-account-owner-${token}'
  scope: rg
  params: {
    principalId: principalId
  }
}

module foundry './foundry/main.bicep' = {
  name: 'foundry-private-network-${token}'
  scope: rg
  params: {
    location: location
    aiServices: 'si${token}'
    firstProjectName: 'storageintel'
    projectDescription: 'Private read-only Storage Intelligence Agent'
    displayName: 'Storage Intelligence Agent'
    modelName: 'gpt-5.4-mini'
    modelFormat: 'OpenAI'
    modelVersion: '2026-03-17'
    modelSkuName: 'DataZoneStandard'
    modelCapacity: 10
    vnetName: 'vnet-storage-intel-${token}'
    agentSubnetName: 'agent-subnet'
    peSubnetName: 'private-endpoints-subnet'
    mcpSubnetName: 'container-apps-subnet'
    functionsSubnetName: 'functions-subnet'
    vnetAddressPrefix: '192.168.0.0/16'
    agentSubnetPrefix: '192.168.0.0/24'
    peSubnetPrefix: '192.168.1.0/24'
    mcpSubnetPrefix: '192.168.2.0/24'
    functionsSubnetPrefix: '192.168.3.0/24'
    enableContainerRegistry: true
    developerIpCidr: ''
  }
  dependsOn: [
    foundryOwner
  ]
}

module workload './app/workload.bicep' = {
  name: 'storage-intelligence-workload-${token}'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    tags: tags
    principalId: principalId
    vnetName: foundry.outputs.vnetName
    vnetId: foundry.outputs.vnetId
    peSubnetId: foundry.outputs.peSubnetId
    mcpSubnetId: foundry.outputs.mcpSubnetId
    functionSubnetId: foundry.outputs.functionsSubnetId
    acrName: foundry.outputs.acrName
    acrId: foundry.outputs.acrId
    acrLoginServer: foundry.outputs.acrLoginServer
    appInsightsName: foundry.outputs.appInsightsName
    webAuthClientId: webAuthClientId
    functionAuthClientId: functionAuthClientId
    aiAccountName: foundry.outputs.aiAccountName
    aiProjectName: foundry.outputs.aiProjectName
    aiProjectEndpoint: foundry.outputs.aiProjectEndpoint
    modelDeploymentName: foundry.outputs.modelDeploymentName
    cosmosName: foundry.outputs.cosmosName
  }
}

output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId
output AZURE_AI_ACCOUNT_NAME string = foundry.outputs.aiAccountName
output AZURE_AI_PROJECT_NAME string = foundry.outputs.aiProjectName
output AZURE_AI_PROJECT_ID string = foundry.outputs.aiProjectId
output AZURE_AI_PROJECT_ENDPOINT string = foundry.outputs.aiProjectEndpoint
output AZURE_AI_MODEL_DEPLOYMENT_NAME string = foundry.outputs.modelDeploymentName
output AZURE_CONTAINER_REGISTRY_NAME string = foundry.outputs.acrName
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = foundry.outputs.acrLoginServer
output APPLICATIONINSIGHTS_CONNECTION_STRING string = foundry.outputs.appInsightsConnectionString
output SERVICE_WEB_NAME string = workload.outputs.webAppName
output WEB_URL string = workload.outputs.webUrl
output SERVICE_TOOLS_NAME string = workload.outputs.functionAppName
output AZURE_FUNCTION_NAME string = workload.outputs.functionAppName
output FUNCTION_TOOL_BASE_URL string = workload.outputs.functionToolBaseUrl
output FUNCTION_TOOL_AUDIENCE string = workload.outputs.functionToolAudience
output DURABLE_TASK_SCHEDULER_NAME string = workload.outputs.schedulerName
output LAKE_STORAGE_NAME string = workload.outputs.lakeStorageName
output FUNCTION_STORAGE_NAME string = workload.outputs.functionStorageName
output KEY_VAULT_NAME string = workload.outputs.keyVaultName
output WEB_AUTH_CLIENT_ID string = webAuthClientId
output FUNCTION_AUTH_CLIENT_ID string = functionAuthClientId
