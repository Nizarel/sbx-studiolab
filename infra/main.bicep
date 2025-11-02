// File: infra/main.bicep

// This Bicep template deploys an Azure Container App Environment and two Container Apps (backend and frontend) for the Visionary Lab project
// It also creates an Azure Storage Account and a Log Analytics workspace for monitoring and logging
// The backend container app is configured to use the Azure Blob Storage account and OpenAI deployments for LLM and image generation
// The frontend container app is configured to use the Azure Blob Storage account and OpenAI deployments for LLM and image generation

@description('Location for all resources')
param location string = resourceGroup().location

// Parameters for the Container App Environment and Container Apps
@description('Name of the Container App Environment')
param containerAppEnvName string = 'cae-${environmentName}'
@description('Name of the Container App')
param containerAppNameBackend string = 'ca-backend-${environmentName}'
param containerAppNameFrontend string = 'ca-frontend-${environmentName}'
// Parameters for the Log Analytics workspace
param logAnalyticsWorkspaceName string = 'log-${environmentName}'

// Parameters for the Azure Storage Account
@description('Unique name for the Storage Account (3-24 lowercase letters and numbers)')
param storageAccountName string = 'st${toLower(uniqueString(resourceGroup().id, environmentName))}'

// Parameters for the Azure Container Registry
@description('Unique name for the Container Registry (5-50 lowercase letters and numbers)')
param containerRegistryName string = 'cr${toLower(uniqueString(resourceGroup().id, environmentName))}'

// Parameters for the OpenAI deployments - LLM
@description('Name of the Azure OpenAI resource for LLM')
param LLM_AOAI_RESOURCE string
@description('Name of the LLM deployment')
param LLM_DEPLOYMENT string
@secure()
@description('API key for LLM Azure OpenAI service')
param LLM_AOAI_API_KEY string

// Parameters for the OpenAI deployments - Image Generation
@description('Name of the Azure OpenAI resource for image generation')
param IMAGEGEN_AOAI_RESOURCE string
@description('Name of the image generation deployment')
param IMAGEGEN_DEPLOYMENT string
@secure()
@description('API key for image generation Azure OpenAI service')
param IMAGEGEN_AOAI_API_KEY string

// Parameters for the OpenAI deployments - Sora
@description('Name of the Azure OpenAI resource for Sora')
param SORA_AOAI_RESOURCE string
@description('Name of the Sora deployment')
param SORA_DEPLOYMENT string
@secure()
@description('API key for Sora Azure OpenAI service')
param SORA_AOAI_API_KEY string

// Model types (internal use)
param llmModelType string = 'gpt-4o'
param imageGenModelType string = 'gpt-image-1'
// Parameters for the Docker images for the backend and frontend container apps
param DOCKER_IMAGE_BACKEND string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param DOCKER_IMAGE_FRONTEND string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param API_PROTOCOL string = ''
param API_HOSTNAME string = ''
param API_PORT string = ''

// Environment name for azd
param environmentName string = ''
// param principalId string = '' // Unused parameter removed

// Parameters for Cosmos DB
param cosmosAccountName string = 'visionary-lab-cosmos'
param cosmosDatabaseName string = 'VisionaryLabDB'
param cosmosContainerName string = 'visionarylab'

// Parameters for Private Networking
@description('Enable private endpoints for Storage and Cosmos DB')
param enablePrivateEndpoints bool = false

@description('Virtual Network name')
param vnetName string = 'vnet-${environmentName}'

@description('VNet address prefix')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('Container Apps subnet address prefix')
param containerAppsSubnetPrefix string = '10.0.0.0/23'

@description('Private Endpoints subnet address prefix')
param privateEndpointsSubnetPrefix string = '10.0.2.0/24'

// Parameters for second Container App Environment
@description('Deploy a second Container App Environment')
param deploySecondEnvironment bool = false

@description('Name of the second Container App Environment')
param containerAppEnvName2 string = 'cae-${environmentName}2'

@description('Name of the second backend Container App')
param containerAppNameBackend2 string = 'ca-backend-${environmentName}2'

@description('Name of the second frontend Container App')
param containerAppNameFrontend2 string = 'ca-frontend-${environmentName}2'

@description('Name of the second Log Analytics workspace')
param logAnalyticsWorkspaceName2 string = 'log-${environmentName}2'

@description('Deploy new VNet (set false to reuse existing)')
param deployNewVNet bool = true

@description('Deploy new DNS zones (set false to reuse existing)')
param deployNewDnsZones bool = true

@description('Deploy new private endpoints (set false to reuse existing)')
param deployNewPrivateEndpoints bool = true

// Virtual Network (when private endpoints are enabled)
module vnetMod './modules/virtualNetwork.bicep' = if (enablePrivateEndpoints) {
  name: 'vnetMod'
  params: {
    location: location
    vnetName: vnetName
    vnetAddressPrefix: vnetAddressPrefix
    containerAppsSubnetPrefix: containerAppsSubnetPrefix
    privateEndpointsSubnetPrefix: privateEndpointsSubnetPrefix
    deployNew: deployNewVNet
  }
}

// Private DNS Zone for Storage Blob
module storageBlobDnsZoneMod './modules/privateDnsZone.bicep' = if (enablePrivateEndpoints) {
  name: 'storageBlobDnsZoneMod'
  params: {
    privateDnsZoneName: 'privatelink.blob.${environment().suffixes.storage}'
    vnetId: vnetMod.outputs.vnetId
    deployNew: deployNewDnsZones
  }
  dependsOn: [
    vnetMod
  ]
}

// Private DNS Zone for Cosmos DB
module cosmosDnsZoneMod './modules/privateDnsZone.bicep' = if (enablePrivateEndpoints) {
  name: 'cosmosDnsZoneMod'
  params: {
    privateDnsZoneName: 'privatelink.documents.azure.com'
    vnetId: vnetMod.outputs.vnetId
    deployNew: deployNewDnsZones
  }
  dependsOn: [
    vnetMod
  ]
}

// Azure Storage Account
module storageAccountMod './modules/storageAccount.bicep' = {
  name: 'storageAccountMod'
  params: {
    location: location
    storageAccountName: storageAccountName
    // keyVaultName: keyVaultMod.outputs.keyVaultName
    deployNew: true // set false to reuse an existing storage account
    publicNetworkAccess: enablePrivateEndpoints ? 'Disabled' : 'Enabled'
  }
}


// Azure Storage Account Container
// This module creates a container in the storage account for storing images
module storageContainerMod './modules/storageAccountContainer.bicep' = {
  name: 'storageContainerMod'
  params: {
    storageAccountName: storageAccountName
    containerName: 'images'
    deployNew: true // set false to reuse an existing container
  }
  dependsOn: [
    storageAccountMod
  ]
}

// Private Endpoint for Storage Account
module storagePrivateEndpointMod './modules/storagePrivateEndpoint.bicep' = if (enablePrivateEndpoints) {
  name: 'storagePrivateEndpointMod'
  params: {
    location: location
    privateEndpointName: 'pe-${storageAccountName}'
    storageAccountId: storageAccountMod.outputs.storageAccountId
    subnetId: vnetMod.outputs.privateEndpointsSubnetId
    privateDnsZoneId: storageBlobDnsZoneMod.outputs.privateDnsZoneId
    deployNew: deployNewPrivateEndpoints
  }
  dependsOn: [
    storageAccountMod
    vnetMod
    storageBlobDnsZoneMod
  ]
}

// Azure Container Registry
// This module creates a container registry for storing Docker images
module containerRegistryMod './modules/containerRegistry.bicep' = {
  name: 'containerRegistryMod'
  params: {
    location: location
    containerRegistryName: containerRegistryName
    deployNew: true  // set false to reuse an existing container registry
  }
}

// Add this module after your storage modules
// Azure Cosmos DB Account for Visionary Lab
// This module creates a Cosmos DB account with SQL API for storing Visionary Lab data
// Generate a short, stable prefix per environment to avoid name collisions across deployments
var cosmosPrefix = toLower(substring(uniqueString(resourceGroup().id, environmentName), 0, 5))
var cosmosAccountNamePrefixed = '${cosmosPrefix}-${cosmosAccountName}'
module cosmosDbMod './modules/cosmosDB.bicep' = {
  name: 'cosmosDbMod'
  params: {
    location: location
    cosmosAccountName: cosmosAccountNamePrefixed
    databaseName: cosmosDatabaseName
    containerName: cosmosContainerName
    subnetId: '' // Private Endpoint is used; VNet rules not required
    deployNew: true
    publicNetworkAccess: enablePrivateEndpoints ? 'Disabled' : 'Enabled'
  }
}

// Private Endpoint for Cosmos DB
module cosmosPrivateEndpointMod './modules/cosmosPrivateEndpoint.bicep' = if (enablePrivateEndpoints) {
  name: 'cosmosPrivateEndpointMod'
  params: {
    location: location
    privateEndpointName: 'pe-${cosmosAccountNamePrefixed}'
    cosmosAccountId: cosmosDbMod.outputs.cosmosAccountId
    subnetId: vnetMod.outputs.privateEndpointsSubnetId
    privateDnsZoneId: cosmosDnsZoneMod.outputs.privateDnsZoneId
    deployNew: deployNewPrivateEndpoints
  }
  dependsOn: [
    cosmosDbMod
    vnetMod
    cosmosDnsZoneMod
  ]
}

// OpenAI deployment module for LLM
// This module creates an OpenAI deployment for the LLM model
module llmOpenAiAccount './modules/openAiDeployment.bicep' = {
  name: 'llmOpenAiAccount'
  params: {
    openAiAccountName: LLM_AOAI_RESOURCE
    DeploymentName: LLM_DEPLOYMENT
    ModelType: llmModelType
    ModelVersion: '2024-11-20'
    location: location
    deployNew: false // set false to reuse an existing deployment
  }
  dependsOn: [
    // keyVaultMod
    storageAccountMod
  ]
}

// OpenAI deployment for Image Generation
// This module creates an OpenAI deployment for the image generation models
module imageGenOpenAiAccount './modules/openAiDeployment.bicep' = {
  name: 'imageGenOpenAiAccount'
  params: {
    openAiAccountName: IMAGEGEN_AOAI_RESOURCE
    DeploymentName: IMAGEGEN_DEPLOYMENT
    ModelType: imageGenModelType
    ModelVersion: '2024-11-20'
    location: location
    deployNew: false // set false to reuse an existing deployment
  }
  dependsOn: [
    storageAccountMod
  ]
}

// Azure Container App Environment
// This module creates a container app environment for the backend and frontend container apps
// It also creates a Log Analytics workspace for monitoring and logging
// The Log Analytics workspace is linked to the container app environment
module containerAppEnvMod './modules/containerAppEnv.bicep' = {
  name: 'containerAppEnvMod'
  params: {
    location: location
    containerAppEnvName: containerAppEnvName
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
    subnetId: enablePrivateEndpoints ? vnetMod.outputs.containerAppsSubnetId : ''
    deployNew: true // set false to reuse an existing environment
  }
  dependsOn: enablePrivateEndpoints ? [
    vnetMod
  ] : []
}

// Container App for Backend
// This module creates a container app for the backend service
// It uses the container app environment created in the previous module
// The container app is configured to use the Azure Blob Storage account and OpenAI deployments for LLM and image generation
module containerAppBackend './modules/containerApp.bicep' = {
  name: 'containerAppBackend'
  params: {
    location: location
    containerAppName: containerAppNameBackend
    containerAppEnvId: containerAppEnvMod.outputs.containerAppEnvId
    targetPort: 80
    deployNew: true // set false to reuse an existing container app
    AZURE_BLOB_SERVICE_URL: storageAccountMod.outputs.storageAccountPrimaryEndpoint
    AZURE_STORAGE_ACCOUNT_NAME: storageAccountName
    AZURE_BLOB_IMAGE_CONTAINER: 'images'
    DOCKER_IMAGE: DOCKER_IMAGE_BACKEND
    AZURE_CONTAINER_REGISTRY_ENDPOINT: containerRegistryMod.outputs.containerRegistryLoginServer
    AZURE_CONTAINER_REGISTRY_USERNAME: containerRegistryMod.outputs.containerRegistryUsername
    AZURE_CONTAINER_REGISTRY_PASSWORD: containerRegistryMod.outputs.containerRegistryPassword
    IMAGEGEN_AOAI_RESOURCE: IMAGEGEN_AOAI_RESOURCE
    IMAGEGEN_DEPLOYMENT: IMAGEGEN_DEPLOYMENT
    IMAGEGEN_AOAI_API_KEY: IMAGEGEN_AOAI_API_KEY
    LLM_AOAI_RESOURCE: LLM_AOAI_RESOURCE
    LLM_DEPLOYMENT: LLM_DEPLOYMENT
    LLM_AOAI_API_KEY: LLM_AOAI_API_KEY
    SORA_AOAI_RESOURCE: SORA_AOAI_RESOURCE
    SORA_DEPLOYMENT: SORA_DEPLOYMENT
    SORA_AOAI_API_KEY: SORA_AOAI_API_KEY
    COSMOS_ENDPOINT: cosmosDbMod.outputs.cosmosAccountEndpoint
    COSMOS_DATABASE_NAME: cosmosDbMod.outputs.databaseName
    COSMOS_CONTAINER_NAME: cosmosDbMod.outputs.containerName
    azdServiceName: 'backend'
  }
  dependsOn: [
    cosmosDbMod
  ]
}

// Container App for Frontend
// This module creates a container app for the frontend service
// It uses the container app environment created in the previous module
// The container app is configured to use the Azure Blob Storage account and OpenAI deployments for LLM and image generation
module containerAppFrontend './modules/containerApp.bicep' = {
  name: 'containerAppFrontend'
  params: {
    location: location
    containerAppName: containerAppNameFrontend
    containerAppEnvId: containerAppEnvMod.outputs.containerAppEnvId
    targetPort: 3000
    deployNew: true // set false to reuse an existing container app
    AZURE_BLOB_SERVICE_URL: storageAccountMod.outputs.storageAccountPrimaryEndpoint
    AZURE_STORAGE_ACCOUNT_NAME: storageAccountName
    AZURE_BLOB_IMAGE_CONTAINER: 'images'
    DOCKER_IMAGE: DOCKER_IMAGE_FRONTEND
    AZURE_CONTAINER_REGISTRY_ENDPOINT: containerRegistryMod.outputs.containerRegistryLoginServer
    AZURE_CONTAINER_REGISTRY_USERNAME: containerRegistryMod.outputs.containerRegistryUsername
    AZURE_CONTAINER_REGISTRY_PASSWORD: containerRegistryMod.outputs.containerRegistryPassword
    IMAGEGEN_AOAI_RESOURCE: IMAGEGEN_AOAI_RESOURCE
    IMAGEGEN_DEPLOYMENT: IMAGEGEN_DEPLOYMENT
    IMAGEGEN_AOAI_API_KEY: IMAGEGEN_AOAI_API_KEY
    LLM_AOAI_RESOURCE: LLM_AOAI_RESOURCE
    LLM_DEPLOYMENT: LLM_DEPLOYMENT
    LLM_AOAI_API_KEY: LLM_AOAI_API_KEY
    API_PROTOCOL: API_PROTOCOL == '' ? 'https' : API_PROTOCOL
    API_PORT: API_PORT == '' ? '443' : API_PORT
    // Use the backend external FQDN (public Internet)
    API_HOSTNAME: API_HOSTNAME == '' ? '${containerAppNameBackend}.${containerAppEnvMod.outputs.containerAppDefaultDomain}' : API_HOSTNAME
    azdServiceName: 'frontend'
  }
}

// ========== SECOND CONTAINER APP ENVIRONMENT AND APPS ==========
// Deploy a second Container App Environment with VNet integration
module containerAppEnvMod2 './modules/containerAppEnv.bicep' = if (deploySecondEnvironment) {
  name: 'containerAppEnvMod2'
  params: {
    location: location
    containerAppEnvName: containerAppEnvName2
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName2
    subnetId: enablePrivateEndpoints ? vnetMod.outputs.containerAppsSubnetId : ''
    deployNew: true // Always deploy new for the second environment
  }
  dependsOn: enablePrivateEndpoints ? [
    vnetMod
  ] : []
}

// Container App for Backend (Second Environment)
module containerAppBackend2 './modules/containerApp.bicep' = if (deploySecondEnvironment) {
  name: 'containerAppBackend2'
  params: {
    location: location
    containerAppName: containerAppNameBackend2
    containerAppEnvId: containerAppEnvMod2.outputs.containerAppEnvId
    targetPort: 80
    deployNew: true
    AZURE_BLOB_SERVICE_URL: storageAccountMod.outputs.storageAccountPrimaryEndpoint
    AZURE_STORAGE_ACCOUNT_NAME: storageAccountName
    AZURE_BLOB_IMAGE_CONTAINER: 'images'
    DOCKER_IMAGE: DOCKER_IMAGE_BACKEND
    AZURE_CONTAINER_REGISTRY_ENDPOINT: containerRegistryMod.outputs.containerRegistryLoginServer
    AZURE_CONTAINER_REGISTRY_USERNAME: containerRegistryMod.outputs.containerRegistryUsername
    AZURE_CONTAINER_REGISTRY_PASSWORD: containerRegistryMod.outputs.containerRegistryPassword
    IMAGEGEN_AOAI_RESOURCE: IMAGEGEN_AOAI_RESOURCE
    IMAGEGEN_DEPLOYMENT: IMAGEGEN_DEPLOYMENT
    IMAGEGEN_AOAI_API_KEY: IMAGEGEN_AOAI_API_KEY
    LLM_AOAI_RESOURCE: LLM_AOAI_RESOURCE
    LLM_DEPLOYMENT: LLM_DEPLOYMENT
    LLM_AOAI_API_KEY: LLM_AOAI_API_KEY
    SORA_AOAI_RESOURCE: SORA_AOAI_RESOURCE
    SORA_DEPLOYMENT: SORA_DEPLOYMENT
    SORA_AOAI_API_KEY: SORA_AOAI_API_KEY
    COSMOS_ENDPOINT: cosmosDbMod.outputs.cosmosAccountEndpoint
    COSMOS_DATABASE_NAME: cosmosDbMod.outputs.databaseName
    COSMOS_CONTAINER_NAME: cosmosDbMod.outputs.containerName
    azdServiceName: 'backend2'
  }
  dependsOn: [
    cosmosDbMod
    containerAppEnvMod2
  ]
}

// Container App for Frontend (Second Environment)
module containerAppFrontend2 './modules/containerApp.bicep' = if (deploySecondEnvironment) {
  name: 'containerAppFrontend2'
  params: {
    location: location
    containerAppName: containerAppNameFrontend2
    containerAppEnvId: containerAppEnvMod2.outputs.containerAppEnvId
    targetPort: 3000
    deployNew: true
    AZURE_BLOB_SERVICE_URL: storageAccountMod.outputs.storageAccountPrimaryEndpoint
    AZURE_STORAGE_ACCOUNT_NAME: storageAccountName
    AZURE_BLOB_IMAGE_CONTAINER: 'images'
    DOCKER_IMAGE: DOCKER_IMAGE_FRONTEND
    AZURE_CONTAINER_REGISTRY_ENDPOINT: containerRegistryMod.outputs.containerRegistryLoginServer
    AZURE_CONTAINER_REGISTRY_USERNAME: containerRegistryMod.outputs.containerRegistryUsername
    AZURE_CONTAINER_REGISTRY_PASSWORD: containerRegistryMod.outputs.containerRegistryPassword
    IMAGEGEN_AOAI_RESOURCE: IMAGEGEN_AOAI_RESOURCE
    IMAGEGEN_DEPLOYMENT: IMAGEGEN_DEPLOYMENT
    IMAGEGEN_AOAI_API_KEY: IMAGEGEN_AOAI_API_KEY
    LLM_AOAI_RESOURCE: LLM_AOAI_RESOURCE
    LLM_DEPLOYMENT: LLM_DEPLOYMENT
    LLM_AOAI_API_KEY: LLM_AOAI_API_KEY
    API_PROTOCOL: API_PROTOCOL == '' ? 'https' : API_PROTOCOL
    API_PORT: API_PORT == '' ? '443' : API_PORT
    // Use the second backend's FQDN
    API_HOSTNAME: API_HOSTNAME == '' ? '${containerAppNameBackend2}.${containerAppEnvMod2.outputs.containerAppDefaultDomain}' : API_HOSTNAME
    azdServiceName: 'frontend2'
  }
  dependsOn: [
    containerAppBackend2
  ]
}

// Role assignment for second backend Container App
module cosmosRoleAssignmentMod2 './modules/cosmosRoleAssignment.bicep' = if (deploySecondEnvironment) {
  name: 'cosmosRoleAssignmentMod2'
  params: {
    cosmosAccountName: cosmosAccountNamePrefixed
    containerAppPrincipalId: containerAppBackend2.outputs.containerAppPrincipalId
    dataContributorRoleId: cosmosDbMod.outputs.dataContributorRoleId
  }
  dependsOn: [
    containerAppBackend2
    cosmosDbMod
  ]
}

// Storage role assignment for second backend Container App
module storageRoleAssignmentMod2 './modules/storageRoleAssignment.bicep' = if (deploySecondEnvironment) {
  name: 'storageRoleAssignmentMod2'
  params: {
    storageAccountName: storageAccountName
    containerAppPrincipalId: containerAppBackend2.outputs.containerAppPrincipalId
  }
  dependsOn: [
    containerAppBackend2
    storageAccountMod
  ]
}

// Role assignment module - deployed after both Container App and Cosmos DB exist
module cosmosRoleAssignmentMod './modules/cosmosRoleAssignment.bicep' = {
  name: 'cosmosRoleAssignmentMod'
  params: {
    cosmosAccountName: cosmosAccountNamePrefixed
    containerAppPrincipalId: containerAppBackend.outputs.containerAppPrincipalId
    dataContributorRoleId: cosmosDbMod.outputs.dataContributorRoleId
  }
  dependsOn: [
    containerAppBackend
    cosmosDbMod
  ]
}

// Storage role assignment - grant backend Container App access to blob storage
module storageRoleAssignmentMod './modules/storageRoleAssignment.bicep' = {
  name: 'storageRoleAssignmentMod'
  params: {
    storageAccountName: storageAccountName
    containerAppPrincipalId: containerAppBackend.outputs.containerAppPrincipalId
  }
}

// Outputs for azd
output AZURE_LOCATION string = location
output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerAppEnvMod.outputs.containerAppEnvId
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistryMod.outputs.containerRegistryLoginServer
output BACKEND_URI string = 'https://${containerAppBackend.outputs.containerAppFqdn}'
// Internal URI not used in public-only mode; mirror external for compatibility
output BACKEND_INTERNAL_URI string = 'https://${containerAppBackend.outputs.containerAppFqdn}'
output FRONTEND_URI string = 'https://${containerAppFrontend.outputs.containerAppFqdn}'
output AZURE_STORAGE_ACCOUNT_NAME string = storageAccountName
output AZURE_BLOB_SERVICE_URL string = storageAccountMod.outputs.storageAccountPrimaryEndpoint

// Cosmos DB outputs
output COSMOS_DB_ENDPOINT string = cosmosDbMod.outputs.cosmosAccountEndpoint
output COSMOS_DB_DATABASE_NAME string = cosmosDbMod.outputs.databaseName
output COSMOS_DB_CONTAINER_NAME string = cosmosDbMod.outputs.containerName
// Intentionally do not output the Cosmos DB key; using Managed Identity + RBAC

// Outputs for second environment (conditional)
output AZURE_CONTAINER_ENVIRONMENT_NAME_2 string = deploySecondEnvironment ? containerAppEnvMod2.outputs.containerAppEnvId : ''
output BACKEND_URI_2 string = deploySecondEnvironment ? 'https://${containerAppBackend2.outputs.containerAppFqdn}' : ''
output FRONTEND_URI_2 string = deploySecondEnvironment ? 'https://${containerAppFrontend2.outputs.containerAppFqdn}' : ''
