param location string
param storageAccountName string = 'a${toLower(uniqueString(resourceGroup().id, 'storage'))}'
// param keyVaultName string
param deployNew bool = true
@description('Public network access setting. Set to Disabled when using private endpoints.')
param publicNetworkAccess string = 'Enabled'

resource storageAccount 'Microsoft.Storage/storageAccounts@2024-01-01' = if(deployNew) {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: true
    allowSharedKeyAccess: false
    publicNetworkAccess: publicNetworkAccess
    minimumTlsVersion: 'TLS1_2'
    networkAcls: publicNetworkAccess == 'Disabled' ? {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    } : null
  }
}

output storageAccountPrimaryEndpoint string = deployNew ? storageAccount.properties.primaryEndpoints.blob : ''
output storageAccountId string = deployNew ? storageAccount.id : ''
output storageAccountName string = storageAccountName

