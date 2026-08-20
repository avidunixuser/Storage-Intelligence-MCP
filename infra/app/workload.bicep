targetScope = 'resourceGroup'

param location string
param environmentName string
param tags object
param principalId string
param vnetName string
param vnetId string
param peSubnetId string
param mcpSubnetId string
param functionSubnetId string
param acrName string
param acrId string
param acrLoginServer string
param appInsightsName string
param webAuthClientId string
param functionAuthClientId string
param aiAccountName string
param aiProjectName string
param aiProjectEndpoint string
param modelDeploymentName string
param cosmosName string

var token = take(toLower(uniqueString(subscription().id, resourceGroup().id, environmentName)), 8)
var functionName = 'func-storage-intel-${token}'
var functionStorageName = 'stfunc${token}'
var lakeStorageName = 'stlake${token}'
var schedulerName = 'dts-storage-intel-${token}'
var keyVaultName = 'kvsi${token}'
var managedEnvironmentName = 'cae-storage-intel-${token}'
var webAppName = 'ca-storage-intel-${token}'
var inventoryDatabaseName = 'storage-intelligence'
var inventoryContainerName = 'storage-accounts'
var functionAudience = 'api://${functionAuthClientId}'
var webAudience = 'api://${webAuthClientId}'

var blobDataOwnerRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
var blobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
var durableTaskDataContributorRoleId = '0ad04412-c4d5-4796-b79c-f76d14c8d402'
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
var monitoringMetricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'
var foundryUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
var websiteContributorRoleId = 'de139f84-1756-47ae-9be6-808fbbe84772'
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: aiAccountName
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = {
  parent: foundryAccount
  name: aiProjectName
}

resource functionIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-function-${token}'
  location: location
  tags: tags
}

resource webIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-web-${token}'
  location: location
  tags: tags
}

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = {
  name: cosmosName
}

resource inventoryDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-11-15' = {
  parent: cosmosAccount
  name: inventoryDatabaseName
  properties: {
    resource: {
      id: inventoryDatabaseName
    }
    options: {
      throughput: 400
    }
  }
}

resource inventoryContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15' = {
  parent: inventoryDatabase
  name: inventoryContainerName
  properties: {
    resource: {
      id: inventoryContainerName
      partitionKey: {
        paths: [
          '/subscription_id'
        ]
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
    }
    options: {}
  }
}

resource webCosmosInventoryContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2022-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, webIdentity.id, inventoryDatabaseName, cosmosDataContributorRoleId)
  properties: {
    principalId: webIdentity.properties.principalId
    roleDefinitionId: resourceId(
      'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions',
      cosmosName,
      cosmosDataContributorRoleId
    )
    scope: '${cosmosAccount.id}/dbs/${inventoryDatabaseName}'
  }
  dependsOn: [
    inventoryDatabase
  ]
}

resource functionStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: functionStorageName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      bypass: 'None'
      defaultAction: 'Deny'
    }
  }
}

resource functionBlobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: functionStorage
  name: 'default'
}

resource deploymentContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: functionBlobService
  name: 'deployment'
  properties: {
    publicAccess: 'None'
  }
}

resource lakeStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: lakeStorageName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_ZRS'
  }
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      bypass: 'None'
      defaultAction: 'Deny'
    }
  }
}

resource lakeBlobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: lakeStorage
  name: 'default'
}

resource lakeContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for zone in [
    'raw'
    'normalized'
    'curated'
    'findings'
  ]: {
    parent: lakeBlobService
    name: zone
    properties: {
      publicAccess: 'None'
    }
  }
]

resource blobDns 'Microsoft.Network/privateDnsZones@2024-06-01' existing = {
  name: 'privatelink.blob.${environment().suffixes.storage}'
}

resource dfsDns 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'privatelink.dfs.${environment().suffixes.storage}'
  location: 'global'
}

resource dfsDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: dfsDns
  name: '${vnetName}-dfs-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false
  }
}

resource functionStoragePe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${functionStorageName}-blob-pe'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'blob'
        properties: {
          privateLinkServiceId: functionStorage.id
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

resource functionStorageDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: functionStoragePe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'blob'
        properties: {
          privateDnsZoneId: blobDns.id
        }
      }
    ]
  }
}

resource lakeBlobPe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${lakeStorageName}-blob-pe'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'blob'
        properties: {
          privateLinkServiceId: lakeStorage.id
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

resource lakeBlobDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: lakeBlobPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'blob'
        properties: {
          privateDnsZoneId: blobDns.id
        }
      }
    ]
  }
}

resource lakeDfsPe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${lakeStorageName}-dfs-pe'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'dfs'
        properties: {
          privateLinkServiceId: lakeStorage.id
          groupIds: [
            'dfs'
          ]
        }
      }
    ]
  }
}

resource lakeDfsDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: lakeDfsPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'dfs'
        properties: {
          privateDnsZoneId: dfsDns.id
        }
      }
    ]
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: tenant().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enablePurgeProtection: true
    enableSoftDelete: true
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      bypass: 'None'
      defaultAction: 'Deny'
    }
  }
}

resource keyVaultDns 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'privatelink.vaultcore.azure.net'
  location: 'global'
}

resource keyVaultDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: keyVaultDns
  name: '${vnetName}-vault-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false
  }
}

resource keyVaultPe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${keyVaultName}-pe'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'vault'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: [
            'vault'
          ]
        }
      }
    ]
  }
}

resource keyVaultDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: keyVaultPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'vault'
        properties: {
          privateDnsZoneId: keyVaultDns.id
        }
      }
    ]
  }
}

resource scheduler 'Microsoft.DurableTask/schedulers@2026-02-01' = {
  name: schedulerName
  location: location
  tags: tags
  properties: {
    ipAllowlist: []
    publicNetworkAccess: 'Disabled'
    sku: {
      name: 'Consumption'
    }
  }
}

resource taskHub 'Microsoft.DurableTask/schedulers/taskHubs@2026-02-01' = {
  parent: scheduler
  name: 'default'
}

resource durableDns 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'privatelink.durabletask.io'
  location: 'global'
}

resource durableDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: durableDns
  name: '${vnetName}-durable-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false
  }
}

resource durablePe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${schedulerName}-pe'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'scheduler'
        properties: {
          privateLinkServiceId: scheduler.id
          groupIds: [
            'scheduler'
          ]
        }
      }
    ]
  }
}

resource durableDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: durablePe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'scheduler'
        properties: {
          privateDnsZoneId: durableDns.id
        }
      }
    ]
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource functionPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: 'plan-function-${token}'
  location: location
  tags: tags
  kind: 'functionapp'
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: functionName
  location: location
  tags: union(tags, {
    'azd-service-name': 'tools'
  })
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${functionIdentity.id}': {}
    }
  }
  properties: {
    publicNetworkAccess: 'Disabled'
    serverFarmId: functionPlan.id
    virtualNetworkSubnetId: functionSubnetId
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${functionStorage.properties.primaryEndpoints.blob}${deploymentContainer.name}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: functionIdentity.id
          }
        }
      }
      runtime: {
        name: 'python'
        version: '3.13'
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 20
        instanceMemoryMB: 2048
      }
    }
    siteConfig: {
      alwaysOn: false
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'AzureWebJobsStorage__blobServiceUri'
          value: functionStorage.properties.primaryEndpoints.blob
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'AzureWebJobsStorage__clientId'
          value: functionIdentity.properties.clientId
        }
        {
          name: 'LakeStorage__blobServiceUri'
          value: lakeStorage.properties.primaryEndpoints.blob
        }
        {
          name: 'LakeStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'LakeStorage__clientId'
          value: functionIdentity.properties.clientId
        }
        {
          name: 'DURABLE_TASK_SCHEDULER_CONNECTION_STRING'
          value: 'Endpoint=${scheduler.properties.endpoint};TaskHub=${taskHub.name};Authentication=ManagedIdentity;ClientID=${functionIdentity.properties.clientId}'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'APPLICATIONINSIGHTS_AUTHENTICATION_STRING'
          value: 'ClientId=${functionIdentity.properties.clientId};Authorization=AAD'
        }
        {
          name: 'AUTH_DISABLED'
          value: 'false'
        }
      ]
    }
  }
  dependsOn: [
    functionStorageRole
  ]
}

resource functionAuth 'Microsoft.Web/sites/config@2024-04-01' = {
  parent: functionApp
  name: 'authsettingsV2'
  properties: {
    platform: {
      enabled: true
      runtimeVersion: '~1'
    }
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'Return401'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: functionAuthClientId
          openIdIssuer: '${environment().authentication.loginEndpoint}${tenant().tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: [
            functionAudience
          ]
        }
      }
    }
    httpSettings: {
      requireHttps: true
    }
  }
}

resource functionDns 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'privatelink.azurewebsites.net'
  location: 'global'
}

resource functionDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: functionDns
  name: '${vnetName}-function-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false
  }
}

resource functionPe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${functionName}-pe'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: peSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'sites'
        properties: {
          privateLinkServiceId: functionApp.id
          groupIds: [
            'sites'
          ]
        }
      }
    ]
  }
}

resource functionDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: functionPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'sites'
        properties: {
          privateDnsZoneId: functionDns.id
        }
      }
    ]
  }
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: managedEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'azure-monitor'
    }
    vnetConfiguration: {
      infrastructureSubnetId: mcpSubnetId
      internal: false
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource webAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acrId, webIdentity.id, acrPullRoleId)
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource webFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryProject.id, webIdentity.id, foundryUserRoleId)
  scope: foundryProject
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource webFunctionDeployer 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(functionApp.id, webIdentity.id, websiteContributorRoleId)
  scope: functionApp
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', websiteContributorRoleId)
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource webApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: webAppName
  location: location
  tags: union(tags, {
    'azd-service-name': 'web'
  })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${webIdentity.id}': {}
    }
  }
  properties: {
    environmentId: managedEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        allowInsecure: false
        targetPort: 8000
        transport: 'auto'
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: acrLoginServer
          identity: webIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
            {
              name: 'AUTH_DISABLED'
              value: 'false'
            }
            {
              name: 'A2A_PUBLIC_URL'
              value: 'https://${webAppName}.${managedEnvironment.properties.defaultDomain}'
            }
            {
              name: 'MCP_ALLOWED_HOSTS'
              value: '${webAppName}.${managedEnvironment.properties.defaultDomain}'
            }
            {
              name: 'MCP_ALLOWED_ORIGINS'
              value: 'https://${webAppName}.${managedEnvironment.properties.defaultDomain}'
            }
            {
              name: 'AGENT_DEPLOY_ON_STARTUP'
              value: 'false'
            }
            {
              name: 'AGENT_SMOKE_ON_STARTUP'
              value: 'false'
            }
            {
              name: 'FUNCTION_DEPLOY_ON_STARTUP'
              value: 'false'
            }
            {
              name: 'FUNCTION_APP_NAME'
              value: functionApp.name
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: webIdentity.properties.clientId
            }
            {
              name: 'AZURE_AI_PROJECT_ENDPOINT'
              value: aiProjectEndpoint
            }
            {
              name: 'AZURE_AI_MODEL_DEPLOYMENT_NAME'
              value: modelDeploymentName
            }
            {
              name: 'COSMOS_INVENTORY_ENABLED'
              value: 'true'
            }
            {
              name: 'COSMOS_ENDPOINT'
              value: cosmosAccount.properties.documentEndpoint
            }
            {
              name: 'COSMOS_DATABASE'
              value: inventoryDatabaseName
            }
            {
              name: 'COSMOS_CONTAINER'
              value: inventoryContainerName
            }
            {
              name: 'FUNCTION_TOOL_BASE_URL'
              value: 'https://${functionApp.properties.defaultHostName}/api'
            }
            {
              name: 'FUNCTION_TOOL_AUDIENCE'
              value: functionAudience
            }
            {
              name: 'STORAGE_AGENT_NAME'
              value: 'storage-intelligence-agent'
            }
          ]
          resources: {
            cpu: json('1')
            memory: '2Gi'
          }
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/healthz'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 0
              periodSeconds: 10
              timeoutSeconds: 10
              failureThreshold: 60
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/healthz'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 60
              periodSeconds: 20
              timeoutSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/readyz'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 10
              failureThreshold: 30
            }
          ]
        }
      ]
      scale: {
        // A2A task and cancellation state is process-local in the SDK task handler.
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
  dependsOn: [
    webAcrPull
    webFoundryUser
    webFunctionDeployer
    inventoryContainer
    webCosmosInventoryContributor
  ]
}

resource webAuth 'Microsoft.App/containerApps/authConfigs@2024-03-01' = {
  parent: webApp
  name: 'current'
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'azureactivedirectory'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: webAuthClientId
          openIdIssuer: '${environment().authentication.loginEndpoint}${tenant().tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: [
            webAuthClientId
            webAudience
          ]
        }
      }
    }
    httpSettings: {
      requireHttps: true
    }
  }
}

resource functionStorageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(functionStorage.id, functionIdentity.id, blobDataOwnerRoleId)
  scope: functionStorage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', blobDataOwnerRoleId)
    principalId: functionIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource deployerStorageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(functionStorage.id, principalId, blobDataOwnerRoleId)
  scope: functionStorage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', blobDataOwnerRoleId)
    principalId: principalId
    principalType: 'User'
  }
}

resource lakeRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(lakeStorage.id, functionIdentity.id, blobDataContributorRoleId)
  scope: lakeStorage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', blobDataContributorRoleId)
    principalId: functionIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource durableRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(scheduler.id, functionIdentity.id, durableTaskDataContributorRoleId)
  scope: scheduler
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', durableTaskDataContributorRoleId)
    principalId: functionIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource durableDashboardRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(scheduler.id, principalId, durableTaskDataContributorRoleId)
  scope: scheduler
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', durableTaskDataContributorRoleId)
    principalId: principalId
    principalType: 'User'
  }
}

resource keyVaultRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionIdentity.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: functionIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource monitoringRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsights.id, functionIdentity.id, monitoringMetricsPublisherRoleId)
  scope: appInsights
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
    principalId: functionIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output webAppName string = webApp.name
output webUrl string = 'https://${webApp.properties.configuration.ingress.fqdn}'
output functionAppName string = functionApp.name
output functionToolBaseUrl string = 'https://${functionApp.properties.defaultHostName}/api'
output functionToolAudience string = functionAudience
output schedulerName string = scheduler.name
output schedulerEndpoint string = scheduler.properties.endpoint
output lakeStorageName string = lakeStorage.name
output functionStorageName string = functionStorage.name
output keyVaultName string = keyVault.name
output functionIdentityClientId string = functionIdentity.properties.clientId
output functionIdentityPrincipalId string = functionIdentity.properties.principalId
output webIdentityPrincipalId string = webIdentity.properties.principalId
output cosmosInventoryDatabaseName string = inventoryDatabase.name
output cosmosInventoryContainerName string = inventoryContainer.name
