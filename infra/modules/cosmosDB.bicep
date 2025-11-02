param location string
param cosmosAccountName string
param databaseName string = 'VisionaryLabDB'
param containerName string = 'visionarylab'
param deployNew bool = true
param subnetId string = ''
// Control public access. Set to 'Enabled' for public Internet access, 'Disabled' for private-only
param publicNetworkAccess string = 'Enabled'

// Create a unique name if not provided
var uniqueCosmosAccountName = cosmosAccountName == '' ? 'cosmos-${uniqueString(resourceGroup().id)}' : cosmosAccountName

// Cosmos DB Account
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = if (deployNew) {
  name: uniqueCosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: false
    // Control public access
    publicNetworkAccess: publicNetworkAccess
    // Do not bypass network ACLs via trusted Azure services when PNA is disabled
    networkAclBypass: 'None'
    // With Private Endpoint, VNet filters are not required
    isVirtualNetworkFilterEnabled: false
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: []
    virtualNetworkRules: []
  }
}

// SQL Database
resource sqlDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = if (deployNew) {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

// Container: visionarylab
resource visionarylabContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = if (deployNew) {
  parent: sqlDatabase
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: [
          '/media_type'
        ]
        kind: 'Hash'
        version: 1 // Non-hierarchical partition key
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
            path: '/_etag/?'
          }
        ]
      }
    }
    options: {
      throughput: 600
    }
  }
}

// SQL Role Definition - Data Reader
resource dataReaderRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-05-15' = if (deployNew) {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, 'sql-role-definition-reader')
  properties: {
    roleName: '${uniqueCosmosAccountName}-data-reader-role'
    type: 'CustomRole'
    assignableScopes: [
      cosmosAccount.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read'
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/executeQuery'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/readChangeFeed'
        ]
      }
    ]
  }
}

// SQL Role Definition - Data Contributor
resource dataContributorRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-05-15' = if (deployNew) {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, 'sql-role-definition-contributor')
  properties: {
    roleName: '${uniqueCosmosAccountName}-data-contributor-role'
    type: 'CustomRole'
    assignableScopes: [
      cosmosAccount.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
        ]
      }
    ]
  }
}

// Reference to existing Cosmos DB account when not deploying new
resource existingCosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = if(!deployNew) {
  name: uniqueCosmosAccountName
}

// Reference to existing database
resource existingSqlDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' existing = if(!deployNew) {
  parent: existingCosmosAccount
  name: databaseName
}

// Reference to existing container
resource existingVisionarylabContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' existing = if(!deployNew) {
  parent: existingSqlDatabase
  name: containerName
}

// Reference to existing role definitions
resource existingDataReaderRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-05-15' existing = if(!deployNew) {
  parent: existingCosmosAccount
  name: guid(existingCosmosAccount.id, 'sql-role-definition-reader')
}

resource existingDataContributorRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-05-15' existing = if(!deployNew) {
  parent: existingCosmosAccount
  name: guid(existingCosmosAccount.id, 'sql-role-definition-contributor')
}

// Outputs
output cosmosAccountId string = deployNew ? cosmosAccount!.id : existingCosmosAccount!.id
output cosmosAccountName string = deployNew ? cosmosAccount!.name : existingCosmosAccount!.name
output cosmosAccountEndpoint string = deployNew ? cosmosAccount!.properties.documentEndpoint : existingCosmosAccount!.properties.documentEndpoint
output databaseName string = deployNew ? sqlDatabase!.name : existingSqlDatabase!.name
output containerName string = deployNew ? visionarylabContainer!.name : existingVisionarylabContainer!.name
output systemAssignedIdentityPrincipalId string = deployNew ? cosmosAccount!.identity.principalId : existingCosmosAccount!.identity.principalId
output dataReaderRoleId string = deployNew ? dataReaderRole!.id : existingDataReaderRole!.id
output dataContributorRoleId string = deployNew ? dataContributorRole!.id : existingDataContributorRole!.id
