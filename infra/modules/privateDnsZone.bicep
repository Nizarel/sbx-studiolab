@description('Name of the private DNS zone')
param privateDnsZoneName string

@description('Virtual Network ID to link the DNS zone to')
param vnetId string

@description('Location is global for private DNS zones')
param location string = 'global'

@description('Whether to deploy new Private DNS Zone')
param deployNew bool = true

// Private DNS Zone
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (deployNew) {
  name: privateDnsZoneName
  location: location
}

// Reference existing Private DNS Zone when deployNew is false
resource existingPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' existing = if (!deployNew) {
  name: privateDnsZoneName
}

// Link DNS Zone to VNet
resource privateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (deployNew) {
  parent: privateDnsZone
  name: '${privateDnsZoneName}-link'
  location: location
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

output privateDnsZoneId string = deployNew ? privateDnsZone.id : existingPrivateDnsZone.id
output privateDnsZoneName string = privateDnsZoneName
