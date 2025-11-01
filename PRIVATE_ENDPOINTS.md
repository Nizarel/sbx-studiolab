# Private Endpoint Deployment Guide

This guide explains how to deploy the Visionary Lab with **private endpoints** for Azure Storage and Cosmos DB, ensuring all network traffic stays within your Azure Virtual Network and complies with security policies that disable public network access.

## Architecture Overview

When private endpoints are enabled, the following infrastructure is deployed:

### Network Components
- **Virtual Network (VNet)**: A dedicated VNet with customizable address space (default: `10.0.0.0/16`)
  - **Container Apps Subnet**: For Azure Container Apps environment integration (default: `10.0.0.0/23`)
  - **Private Endpoints Subnet**: For private endpoint network interfaces (default: `10.0.2.0/24`)

### Private Connectivity
- **Private Endpoints**:
  - Azure Storage Account (Blob service)
  - Azure Cosmos DB (SQL API)
  
- **Private DNS Zones**:
  - `privatelink.blob.core.windows.net` - for Storage Account
  - `privatelink.documents.azure.com` - for Cosmos DB

### Security Configuration
- **Storage Account**: Public network access disabled, only accessible via private endpoint
- **Cosmos DB**: Public network access disabled, only accessible via private endpoint
- **Container Apps Environment**: Integrated with VNet for secure communication

## Prerequisites

Same as the main deployment, plus:
- Permissions to create Virtual Networks and Private DNS Zones in your subscription
- Understanding of Azure networking concepts (VNets, subnets, private endpoints)

## Deployment Methods

### Method 1: Using Azure Developer CLI (azd) - Recommended

#### Step 1: Enable Private Endpoints

Set the `enablePrivateEndpoints` parameter to `true`. You can do this by modifying the parameters file or setting it during deployment:

**Option A: Modify parameters file before deployment**

Edit `infra/main.parameters.json` and change:
```json
"enablePrivateEndpoints": {
  "value": true
}
```

**Option B: Set parameter during deployment**

```bash
azd auth login
azd env new <environment-name>

# Configure OpenAI resources (same as before)
azd env set LLM_AOAI_RESOURCE "your-openai-resource-name"
azd env set LLM_DEPLOYMENT "gpt-4.1"
azd env set LLM_AOAI_API_KEY "your-gpt-key"
azd env set IMAGEGEN_AOAI_RESOURCE "your-openai-resource-name"
azd env set IMAGEGEN_DEPLOYMENT "gpt-image-1"
azd env set IMAGEGEN_AOAI_API_KEY "your-image-gen-key"
azd env set SORA_AOAI_RESOURCE "your-openai-resource-name"
azd env set SORA_DEPLOYMENT "sora"
azd env set SORA_AOAI_API_KEY "your-sora-key"

# Deploy with private endpoints
azd up --parameters enablePrivateEndpoints=true
```

#### Step 2: Deployment Process

The `azd up` command will:
1. ✅ Create the Virtual Network with subnets
2. ✅ Create Private DNS Zones and link them to the VNet
3. ✅ Deploy Storage Account with public access disabled
4. ✅ Deploy Cosmos DB with public access disabled
5. ✅ Create Private Endpoints for Storage and Cosmos DB
6. ✅ Configure Private DNS Zone Groups for automatic DNS registration
7. ✅ Deploy Container Apps Environment with VNet integration
8. ✅ Deploy backend and frontend Container Apps
9. ✅ Configure RBAC permissions for managed identities

**Deployment time**: Approximately 15-20 minutes

### Method 2: Manual Azure CLI Deployment

If you prefer to deploy manually using Azure CLI:

```bash
# 1. Create resource group
az group create --name rg-sbuxstudio --location eastus

# 2. Deploy infrastructure with private endpoints
az deployment group create \
  --resource-group rg-sbuxstudio \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters enablePrivateEndpoints=true \
  --parameters environmentName=prod \
  --parameters LLM_AOAI_RESOURCE="your-llm-resource" \
  --parameters LLM_DEPLOYMENT="gpt-4.1" \
  --parameters LLM_AOAI_API_KEY="your-llm-key" \
  --parameters IMAGEGEN_AOAI_RESOURCE="your-imagegen-resource" \
  --parameters IMAGEGEN_DEPLOYMENT="gpt-image-1" \
  --parameters IMAGEGEN_AOAI_API_KEY="your-imagegen-key" \
  --parameters SORA_AOAI_RESOURCE="your-sora-resource" \
  --parameters SORA_DEPLOYMENT="sora" \
  --parameters SORA_AOAI_API_KEY="your-sora-key"
```

## Customizing Network Configuration

You can customize the VNet address spaces by providing additional parameters:

```bash
azd up \
  --parameters enablePrivateEndpoints=true \
  --parameters vnetAddressPrefix="10.1.0.0/16" \
  --parameters containerAppsSubnetPrefix="10.1.0.0/23" \
  --parameters privateEndpointsSubnetPrefix="10.1.2.0/24"
```

### Network Planning Guidelines

When planning your network configuration:

1. **VNet Address Space**: Choose a CIDR that doesn't overlap with your on-premises network or other Azure VNets you plan to peer with
2. **Container Apps Subnet**: Must be `/23` or larger for Container Apps Environment
3. **Private Endpoints Subnet**: A `/24` subnet can accommodate up to 251 private endpoints
4. **Reserved CIDR**: Container Apps uses `172.16.0.0/16` for platform reserved addresses (not configurable via parameters)

## Migration from Public to Private Endpoints

If you have an existing deployment with public endpoints and want to migrate to private endpoints:

### ⚠️ Important Considerations

1. **Downtime**: There will be a brief period during the transition where services are reconfigured
2. **DNS Propagation**: Private DNS changes may take a few minutes to propagate
3. **Testing**: Test thoroughly in a non-production environment first

### Migration Steps

1. **Backup**: Ensure you have backups of your data in Storage and Cosmos DB

2. **Deploy with private endpoints enabled**:
   ```bash
   azd up --parameters enablePrivateEndpoints=true
   ```

3. **The deployment will**:
   - Create the VNet infrastructure
   - Update Storage Account to disable public access and add private endpoint
   - Update Cosmos DB to disable public access and add private endpoint
   - Reconfigure Container Apps Environment for VNet integration

4. **Verify connectivity**:
   ```bash
   # Check Container App logs
   az containerapp logs show \
     --name ca-backend-<env-name> \
     --resource-group rg-sbuxstudio \
     --follow
   ```

5. **Test application**:
   - Access your application URL
   - Verify image/video generation works
   - Verify gallery/metadata features work

## Troubleshooting

### Common Issues

#### 1. Container Apps can't connect to Storage/Cosmos DB

**Symptom**: Application errors about unable to connect to storage or database

**Solution**:
- Verify private endpoints are deployed: `az network private-endpoint list -g rg-sbuxstudio`
- Check DNS resolution from Container App (should resolve to private IP)
- Verify Container Apps subnet has delegation for `Microsoft.App/environments`

#### 2. DNS Resolution Issues

**Symptom**: Services still resolving to public IPs

**Solution**:
- Verify Private DNS Zones are linked to the VNet
- Check Private DNS Zone Groups are configured on the private endpoints
- Wait 5-10 minutes for DNS propagation

#### 3. Deployment Fails During VNet Creation

**Symptom**: Bicep deployment fails at VNet module

**Solution**:
- Check for CIDR conflicts with existing resources in the subscription
- Verify you have permissions to create Virtual Networks
- Review subnet size requirements (Container Apps needs /23 or larger)

### Validation Commands

```bash
# List all resources in the resource group
az resource list --resource-group rg-sbuxstudio --output table

# Check VNet configuration
az network vnet show --name vnet-<env-name> --resource-group rg-sbuxstudio

# Check private endpoints
az network private-endpoint list --resource-group rg-sbuxstudio --output table

# Check private DNS zones
az network private-dns zone list --resource-group rg-sbuxstudio --output table

# Test Storage Account connectivity (should return private IP)
nslookup <storage-account-name>.blob.core.windows.net

# Test Cosmos DB connectivity (should return private IP)
nslookup <cosmos-account-name>.documents.azure.com
```

## Cost Considerations

Enabling private endpoints adds the following costs:

- **Private Endpoints**: ~$7.30/month per endpoint (2 endpoints = ~$14.60/month)
- **Private DNS Zones**: $0.50/month per zone (2 zones = $1.00/month)
- **VNet**: No additional cost (Azure VNets are free)
- **Data Processing**: ~$0.01/GB for data processed through private endpoints

**Estimated additional monthly cost**: ~$15-20 USD

## Security Benefits

With private endpoints enabled:

✅ **No public internet exposure**: Storage and Cosmos DB are not accessible from the internet
✅ **Traffic stays on Microsoft backbone**: All traffic between Container Apps and data services stays within Azure
✅ **Compliance ready**: Meets requirements for private-only networking
✅ **Network isolation**: Resources are isolated within your VNet
✅ **Defense in depth**: Additional layer of network security

## Next Steps

After successful deployment:

1. **Configure firewall rules** (if needed): Add any additional network security rules to subnet NSGs
2. **Set up monitoring**: Configure alerts for private endpoint health
3. **VNet Peering** (if needed): Connect to on-premises networks or other VNets
4. **Service Endpoints** (optional): Consider adding service endpoints for additional Azure services

## Support

For issues or questions:
- Review the main [DEPLOYMENT.md](DEPLOYMENT.md) for general deployment guidance
- Check Azure documentation for [Private Endpoints](https://docs.microsoft.com/azure/private-link/private-endpoint-overview)
- Review [Container Apps VNet integration](https://docs.microsoft.com/azure/container-apps/vnet-custom)
