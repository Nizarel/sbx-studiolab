param location string
param containerRegistryName string
param deployNew bool = true

// Use stable API version for ACR
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = if(deployNew) {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Reference existing registry when not deploying new
resource existingRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if(!deployNew) {
  name: containerRegistryName
}

output containerRegistryId string = deployNew ? containerRegistry!.id : existingRegistry!.id
output containerRegistryName string = containerRegistryName
output containerRegistryLoginServer string = deployNew ? containerRegistry!.properties.loginServer : existingRegistry!.properties.loginServer
output containerRegistryUsername string = deployNew ? listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-07-01').username : listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-07-01').username
output containerRegistryPassword string = deployNew ? listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-07-01').passwords[0].value : listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-07-01').passwords[0].value
