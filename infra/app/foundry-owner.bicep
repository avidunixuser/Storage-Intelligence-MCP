targetScope = 'resourceGroup'

param principalId string

var foundryAccountOwnerRoleId = 'e47c6f54-e4a2-4754-9501-8e0985b135e1'

resource foundryOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, foundryAccountOwnerRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryAccountOwnerRoleId)
    principalId: principalId
    principalType: 'User'
  }
}
