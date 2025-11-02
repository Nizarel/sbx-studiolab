@description('Name of the Virtual Network')
param vnetName string

@description('Name of the subnet')
param subnetName string

@description('Address prefix for the subnet')
param subnetPrefix string

@description('Whether to deploy new subnet')
param deployNew bool = true

@description('Whether to delegate subnet to Container Apps')
param delegateToContainerApps bool = false

// Subnet resource
resource subnet 'Microsoft.Network/virtualNetworks/subnets@2023-11-01' = if (deployNew) {
  name: '${vnetName}/${subnetName}'
  properties: {
    addressPrefix: subnetPrefix
    delegations: delegateToContainerApps ? [
      {
        name: 'Microsoft.App/environments'
        properties: {
          serviceName: 'Microsoft.App/environments'
        }
      }
    ] : []
    serviceEndpoints: []
    privateEndpointNetworkPolicies: delegateToContainerApps ? 'Enabled' : 'Disabled'
  }
}

// Reference existing subnet
resource existingSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-11-01' existing = if (!deployNew) {
  name: '${vnetName}/${subnetName}'
}

output subnetId string = deployNew ? subnet.id : existingSubnet.id
output subnetName string = subnetName
