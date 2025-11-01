@description('Location for all resources')
param location string

@description('Name of the Private Endpoint')
param privateEndpointName string

@description('Resource ID of the Storage Account')
param storageAccountId string

@description('Subnet ID where the Private Endpoint will be created')
param subnetId string

@description('Private DNS Zone ID for blob storage')
param privateDnsZoneId string

@description('Whether to deploy new Private Endpoint')
param deployNew bool = true

// Private Endpoint for Storage Account (Blob)
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = if (deployNew) {
  name: privateEndpointName
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${privateEndpointName}-connection'
        properties: {
          privateLinkServiceId: storageAccountId
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

// Private DNS Zone Group for automatic DNS registration
resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = if (deployNew) {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'blob-config'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

output privateEndpointId string = deployNew ? privateEndpoint.id : ''
output privateEndpointName string = deployNew ? privateEndpoint.name : privateEndpointName
