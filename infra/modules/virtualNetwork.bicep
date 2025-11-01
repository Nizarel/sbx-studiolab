@description('Location for all resources')
param location string

@description('Name of the Virtual Network')
param vnetName string

@description('Address prefix for the VNet')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('Name of the Container Apps subnet')
param containerAppsSubnetName string = 'snet-containerApps'

@description('Address prefix for the Container Apps subnet')
param containerAppsSubnetPrefix string = '10.0.0.0/23'

@description('Name of the Private Endpoints subnet')
param privateEndpointsSubnetName string = 'snet-privateEndpoints'

@description('Address prefix for the Private Endpoints subnet')
param privateEndpointsSubnetPrefix string = '10.0.2.0/24'

@description('Whether to deploy new VNet')
param deployNew bool = true

// Virtual Network
resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = if (deployNew) {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: containerAppsSubnetName
        properties: {
          addressPrefix: containerAppsSubnetPrefix
          delegations: [
            {
              name: 'Microsoft.App/environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
          serviceEndpoints: []
          privateEndpointNetworkPolicies: 'Enabled'
        }
      }
      {
        name: privateEndpointsSubnetName
        properties: {
          addressPrefix: privateEndpointsSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// Output subnet IDs
output vnetId string = deployNew ? vnet.id : ''
output vnetName string = deployNew ? vnet.name : vnetName
output containerAppsSubnetId string = deployNew ? '${vnet.id}/subnets/${containerAppsSubnetName}' : ''
output privateEndpointsSubnetId string = deployNew ? '${vnet.id}/subnets/${privateEndpointsSubnetName}' : ''
