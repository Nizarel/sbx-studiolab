# Quick Start: Enable Private Endpoints for Existing Deployment

This guide is specifically for enabling private endpoints in the **rg-sbuxstudio** resource group with:
- Storage Account: `stpp37s7tza4fqc`
- Cosmos DB: `pp37s-visionary-lab-cosmos`
- Subscription: `b6e08f96-9a62-46d0-b276-8dc80e6bc02a`

## Background

Your company policy requires disabling public network access for Azure resources. This guide shows how to deploy the necessary Virtual Network infrastructure and private endpoints to ensure your Container App can continue to access Storage and Cosmos DB after public access is disabled.

## Prerequisites

1. **Azure CLI** installed and authenticated
   ```bash
   az login
   az account set --subscription b6e08f96-9a62-46d0-b276-8dc80e6bc02a
   ```

2. **Azure Developer CLI (azd)** installed (recommended method)
   - Install: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd

3. **Permissions**: Contributor access to the subscription

## Option 1: Using Azure Developer CLI (Recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Nizarel/sbx-studiolab.git
cd sbx-studiolab
```

### Step 2: Initialize Azure Developer Environment

```bash
# Create a new environment or use existing
azd auth login
azd env new sbuxstudio  # or use your existing environment name
```

### Step 3: Configure Environment Variables

Set your Azure OpenAI configuration (if not already set):

```bash
# LLM Configuration
azd env set LLM_AOAI_RESOURCE "<your-llm-openai-resource>"
azd env set LLM_DEPLOYMENT "<your-llm-deployment-name>"
azd env set LLM_AOAI_API_KEY "<your-llm-api-key>"

# Image Generation Configuration
azd env set IMAGEGEN_AOAI_RESOURCE "<your-imagegen-openai-resource>"
azd env set IMAGEGEN_DEPLOYMENT "<your-imagegen-deployment-name>"
azd env set IMAGEGEN_AOAI_API_KEY "<your-imagegen-api-key>"

# Sora Configuration
azd env set SORA_AOAI_RESOURCE "<your-sora-openai-resource>"
azd env set SORA_DEPLOYMENT "<your-sora-deployment-name>"
azd env set SORA_AOAI_API_KEY "<your-sora-api-key>"
```

### Step 4: Deploy with Private Endpoints Enabled

```bash
azd up --parameters enablePrivateEndpoints=true
```

This command will:
1. ✅ Create a Virtual Network (vnet-sbuxstudio) with two subnets
2. ✅ Create Private DNS Zones for Storage and Cosmos DB
3. ✅ Create Private Endpoints for your existing Storage and Cosmos DB
4. ✅ Update Storage Account to disable public network access
5. ✅ Update Cosmos DB to disable public network access
6. ✅ Reconfigure Container Apps Environment with VNet integration
7. ✅ Redeploy Container Apps with VNet integration

**Expected duration**: 15-20 minutes

### Step 5: Verify Deployment

```bash
# Check that private endpoints were created
az network private-endpoint list \
  --resource-group rg-sbuxstudio \
  --output table

# Verify Storage private endpoint
az network private-endpoint show \
  --name pe-stpp37s7tza4fqc \
  --resource-group rg-sbuxstudio

# Verify Cosmos DB private endpoint
az network private-endpoint show \
  --name pe-pp37s-visionary-lab-cosmos \
  --resource-group rg-sbuxstudio

# Check that VNet was created
az network vnet show \
  --name vnet-sbuxstudio \
  --resource-group rg-sbuxstudio

# Verify Private DNS Zones
az network private-dns zone list \
  --resource-group rg-sbuxstudio \
  --output table
```

### Step 6: Test Application

1. Get your Container App URL:
   ```bash
   azd env get-values | grep FRONTEND_URI
   ```

2. Access the application in your browser

3. Test functionality:
   - Generate an image
   - Generate a video (if Sora is configured)
   - View gallery
   - Verify no connectivity errors

## Option 2: Direct Azure CLI Deployment

If you prefer not to use azd:

```bash
# Navigate to the repository
cd sbx-studiolab

# Deploy with Azure CLI
az deployment group create \
  --resource-group rg-sbuxstudio \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters enablePrivateEndpoints=true \
  --parameters environmentName=sbuxstudio \
  --parameters storageAccountName=stpp37s7tza4fqc \
  --parameters cosmosAccountName=visionary-lab-cosmos \
  --parameters LLM_AOAI_RESOURCE="<your-llm-resource>" \
  --parameters LLM_DEPLOYMENT="<your-llm-deployment>" \
  --parameters LLM_AOAI_API_KEY="<your-llm-key>" \
  --parameters IMAGEGEN_AOAI_RESOURCE="<your-imagegen-resource>" \
  --parameters IMAGEGEN_DEPLOYMENT="<your-imagegen-deployment>" \
  --parameters IMAGEGEN_AOAI_API_KEY="<your-imagegen-key>" \
  --parameters SORA_AOAI_RESOURCE="<your-sora-resource>" \
  --parameters SORA_DEPLOYMENT="<your-sora-deployment>" \
  --parameters SORA_AOAI_API_KEY="<your-sora-key>"
```

## What Gets Created

The deployment creates these new resources in **rg-sbuxstudio**:

| Resource | Name | Purpose |
|----------|------|---------|
| Virtual Network | `vnet-sbuxstudio` | Network isolation |
| Subnet | `snet-containerApps` | For Container Apps |
| Subnet | `snet-privateEndpoints` | For private endpoints |
| Private Endpoint | `pe-stpp37s7tza4fqc` | Storage private access |
| Private Endpoint | `pe-pp37s-visionary-lab-cosmos` | Cosmos DB private access |
| Private DNS Zone | `privatelink.blob.core.windows.net` | Storage DNS |
| Private DNS Zone | `privatelink.documents.azure.com` | Cosmos DB DNS |

## What Gets Modified

Existing resources that will be updated:

| Resource | Change |
|----------|--------|
| Storage Account `stpp37s7tza4fqc` | Public network access → **Disabled** |
| Cosmos DB `pp37s-visionary-lab-cosmos` | Public network access → **Disabled** |
| Container App Environment | VNet integration → **Enabled** |

## Network Configuration

The default configuration creates:

- **VNet Address Space**: `10.0.0.0/16`
- **Container Apps Subnet**: `10.0.0.0/23` (512 addresses)
- **Private Endpoints Subnet**: `10.0.2.0/24` (256 addresses)

### Custom Network Configuration (Optional)

If you need different address ranges:

```bash
azd up \
  --parameters enablePrivateEndpoints=true \
  --parameters vnetAddressPrefix="10.1.0.0/16" \
  --parameters containerAppsSubnetPrefix="10.1.0.0/23" \
  --parameters privateEndpointsSubnetPrefix="10.1.2.0/24"
```

## Validation Steps

### 1. Check DNS Resolution

From a VM in the same VNet (or use Azure Bastion):

```bash
# Storage should resolve to private IP (10.0.2.x)
nslookup stpp37s7tza4fqc.blob.core.windows.net

# Cosmos DB should resolve to private IP (10.0.2.x)
nslookup pp37s-visionary-lab-cosmos.documents.azure.com
```

### 2. Check Container App Logs

```bash
# Backend logs
az containerapp logs show \
  --name ca-backend-sbuxstudio \
  --resource-group rg-sbuxstudio \
  --follow

# Look for any connection errors
# Successful connection means private endpoints are working
```

### 3. Verify Public Access is Disabled

```bash
# Try to access storage from public internet (should fail)
curl https://stpp37s7tza4fqc.blob.core.windows.net/

# Expected: Connection refused or timeout
```

## Rollback Plan

If you need to rollback to public endpoints:

```bash
# Redeploy without private endpoints
azd up --parameters enablePrivateEndpoints=false

# This will:
# - Re-enable public access on Storage and Cosmos DB
# - Remove VNet integration from Container Apps
# Note: VNet and private endpoints will remain but won't be used
```

To fully remove private endpoint resources:

```bash
# Delete private endpoints
az network private-endpoint delete --name pe-stpp37s7tza4fqc --resource-group rg-sbuxstudio
az network private-endpoint delete --name pe-pp37s-visionary-lab-cosmos --resource-group rg-sbuxstudio

# Delete private DNS zones
az network private-dns zone delete --name privatelink.blob.core.windows.net --resource-group rg-sbuxstudio
az network private-dns zone delete --name privatelink.documents.azure.com --resource-group rg-sbuxstudio

# Delete VNet (if no longer needed)
az network vnet delete --name vnet-sbuxstudio --resource-group rg-sbuxstudio
```

## Troubleshooting

### Issue: Deployment Fails with "Subnet already exists"

**Solution**: Use existing VNet by setting `deployNew: false` in the virtualNetwork module parameters

### Issue: Container Apps can't connect to Storage/Cosmos

**Checks**:
1. Verify private endpoints are in "Approved" state
2. Check DNS zones are linked to VNet
3. Ensure Container Apps subnet has proper delegation
4. Review Container App logs for specific errors

### Issue: DNS not resolving to private IP

**Solution**:
1. Wait 5-10 minutes for DNS propagation
2. Verify private DNS zone groups are configured
3. Check VNet link status in private DNS zones

## Cost Impact

Additional monthly costs for private endpoints:

- **2 Private Endpoints**: ~$14.60/month ($7.30 each)
- **2 Private DNS Zones**: ~$1.00/month ($0.50 each)
- **VNet**: Free
- **Total Additional Cost**: ~$15-20/month

## Next Steps After Deployment

1. ✅ **Test thoroughly**: Verify all application features work
2. ✅ **Monitor logs**: Watch for any connectivity issues
3. ✅ **Update documentation**: Document your specific configuration
4. ✅ **Set up alerts**: Configure monitoring for private endpoint health
5. ✅ **Compliance verification**: Confirm public access is disabled as required

## Support

For issues:
- Review [PRIVATE_ENDPOINTS.md](PRIVATE_ENDPOINTS.md) for detailed guide
- Check [ARCHITECTURE_PRIVATE_ENDPOINTS.md](ARCHITECTURE_PRIVATE_ENDPOINTS.md) for architecture details
- Review Azure Container Apps logs for specific errors

## Summary Checklist

Before you begin:
- [ ] Have Azure CLI and azd installed
- [ ] Authenticated to correct subscription
- [ ] Have OpenAI resource details ready
- [ ] Planned network address space (or use defaults)

Deployment:
- [ ] Run `azd up --parameters enablePrivateEndpoints=true`
- [ ] Wait for deployment to complete (15-20 minutes)
- [ ] Verify private endpoints created
- [ ] Verify DNS zones created and linked
- [ ] Test application functionality

Post-deployment:
- [ ] Verify public access disabled on Storage
- [ ] Verify public access disabled on Cosmos DB
- [ ] DNS resolving to private IPs
- [ ] Container Apps connecting successfully
- [ ] All features working (image/video generation, gallery)
