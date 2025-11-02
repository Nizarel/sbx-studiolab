# Deploying Second Container App Environment

This guide explains how to deploy a second Container App Environment in the same resource group (`rg-sbuxstudio`) alongside the existing deployment.

## Overview

This deployment scenario allows you to:
- Deploy a new Container App Environment with VNet integration
- Create new Container Apps with different names (e.g., `ca-backend-sbuxstudio2`, `ca-frontend-sbuxstudio2`)
- Reuse existing resources (VNet, DNS Zones, Storage, Cosmos DB)
- Test the deployment strategy with `deployNew: false` for existing resources

## Deployment Scenarios

### Scenario 1: First Deployment with Private Endpoints

Deploy the initial environment with private endpoints enabled:

```bash
az deployment group create \
  --resource-group rg-sbuxstudio \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters enablePrivateEndpoints=true \
  --parameters environmentName=sbuxstudio \
  --parameters deployNewVNet=true \
  --parameters deployNewDnsZones=true \
  --parameters deployNewPrivateEndpoints=true
```

This creates:
- Virtual Network: `vnet-sbuxstudio`
- Container App Environment: `cae-sbuxstudio`
- Container Apps: `ca-backend-sbuxstudio`, `ca-frontend-sbuxstudio`
- Private Endpoints for Storage and Cosmos DB
- Private DNS Zones

### Scenario 2: Deploy Second Container App Environment (Reusing Existing Resources)

Deploy a second Container App Environment that reuses the existing VNet, DNS zones, and private endpoints:

```bash
az deployment group create \
  --resource-group rg-sbuxstudio \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters enablePrivateEndpoints=true \
  --parameters environmentName=sbuxstudio \
  --parameters deploySecondEnvironment=true \
  --parameters deployNewVNet=false \
  --parameters deployNewDnsZones=false \
  --parameters deployNewPrivateEndpoints=false
```

This creates:
- Container App Environment: `cae-sbuxstudio2`
- Container Apps: `ca-backend-sbuxstudio2`, `ca-frontend-sbuxstudio2`
- Reuses existing VNet, DNS zones, and private endpoints

### Scenario 3: Update Resources In-Place

To test updating resources in-place, first deploy with `deployNew: false` for specific resources, then switch to `true` to allow updates:

#### Step 1: Test with deployNew: false (No Changes)

```bash
az deployment group create \
  --resource-group rg-sbuxstudio \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters enablePrivateEndpoints=true \
  --parameters environmentName=sbuxstudio \
  --parameters deployNewVNet=false \
  --parameters deployNewDnsZones=false \
  --parameters deployNewPrivateEndpoints=false \
  --parameters deploySecondEnvironment=false
```

#### Step 2: Allow In-Place Updates

```bash
az deployment group create \
  --resource-group rg-sbuxstudio \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters enablePrivateEndpoints=true \
  --parameters environmentName=sbuxstudio \
  --parameters deployNewVNet=false \
  --parameters deployNewDnsZones=false \
  --parameters deployNewPrivateEndpoints=false \
  --parameters deploySecondEnvironment=true
```

## Parameter Reference

### Core Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `environmentName` | Base name for resources | - | Yes |
| `enablePrivateEndpoints` | Enable private endpoints | `false` | No |
| `deploySecondEnvironment` | Deploy second Container App Environment | `false` | No |

### VNet and Private Endpoint Control

| Parameter | Description | Default | Use Case |
|-----------|-------------|---------|----------|
| `deployNewVNet` | Create new VNet or reference existing | `true` | Set to `false` when VNet already exists |
| `deployNewDnsZones` | Create new DNS zones or reference existing | `true` | Set to `false` when DNS zones already exist |
| `deployNewPrivateEndpoints` | Create new private endpoints or reference existing | `true` | Set to `false` when private endpoints already exist |

### Second Environment Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `containerAppEnvName2` | Second Container App Environment name | `cae-${environmentName}2` |
| `containerAppNameBackend2` | Second backend Container App name | `ca-backend-${environmentName}2` |
| `containerAppNameFrontend2` | Second frontend Container App name | `ca-frontend-${environmentName}2` |
| `logAnalyticsWorkspaceName2` | Second Log Analytics workspace name | `log-${environmentName}2` |

## Resource Naming Convention

### First Environment (Default)

- Container App Environment: `cae-sbuxstudio`
- Backend Container App: `ca-backend-sbuxstudio`
- Frontend Container App: `ca-frontend-sbuxstudio`
- Log Analytics: `log-sbuxstudio`

### Second Environment

- Container App Environment: `cae-sbuxstudio2`
- Backend Container App: `ca-backend-sbuxstudio2`
- Frontend Container App: `ca-frontend-sbuxstudio2`
- Log Analytics: `log-sbuxstudio2`

### Shared Resources

- Virtual Network: `vnet-sbuxstudio`
- Storage Account: `st<unique-hash>`
- Cosmos DB: `<hash>-visionary-lab-cosmos`
- Container Registry: `cr<unique-hash>`

## Verification Steps

### 1. Verify Second Container App Environment

```bash
az containerapp env show \
  --name cae-sbuxstudio2 \
  --resource-group rg-sbuxstudio
```

### 2. Verify Second Container Apps

```bash
# Backend
az containerapp show \
  --name ca-backend-sbuxstudio2 \
  --resource-group rg-sbuxstudio

# Frontend
az containerapp show \
  --name ca-frontend-sbuxstudio2 \
  --resource-group rg-sbuxstudio
```

### 3. Get Container App URLs

```bash
# First environment
az containerapp show \
  --name ca-frontend-sbuxstudio \
  --resource-group rg-sbuxstudio \
  --query properties.configuration.ingress.fqdn \
  --output tsv

# Second environment
az containerapp show \
  --name ca-frontend-sbuxstudio2 \
  --resource-group rg-sbuxstudio \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

### 4. Test Application Access

Access both frontends in your browser:
- First environment: `https://ca-frontend-sbuxstudio.<default-domain>`
- Second environment: `https://ca-frontend-sbuxstudio2.<default-domain>`

### 5. Verify VNet Integration

```bash
# Check that both environments are using the same VNet
az containerapp env show \
  --name cae-sbuxstudio \
  --resource-group rg-sbuxstudio \
  --query properties.vnetConfiguration.infrastructureSubnetId

az containerapp env show \
  --name cae-sbuxstudio2 \
  --resource-group rg-sbuxstudio \
  --query properties.vnetConfiguration.infrastructureSubnetId
```

Both should show the same subnet ID.

## Deployment Outputs

After successful deployment, the template provides these outputs:

### First Environment Outputs

- `AZURE_CONTAINER_ENVIRONMENT_NAME`: Container App Environment ID
- `BACKEND_URI`: Backend URL (e.g., `https://ca-backend-sbuxstudio.<domain>`)
- `FRONTEND_URI`: Frontend URL (e.g., `https://ca-frontend-sbuxstudio.<domain>`)

### Second Environment Outputs

- `AZURE_CONTAINER_ENVIRONMENT_NAME_2`: Second Container App Environment ID
- `BACKEND_URI_2`: Second backend URL
- `FRONTEND_URI_2`: Second frontend URL

## Rollback

### Remove Second Environment Only

```bash
# Delete second environment Container Apps
az containerapp delete \
  --name ca-backend-sbuxstudio2 \
  --resource-group rg-sbuxstudio \
  --yes

az containerapp delete \
  --name ca-frontend-sbuxstudio2 \
  --resource-group rg-sbuxstudio \
  --yes

# Delete second Container App Environment
az containerapp env delete \
  --name cae-sbuxstudio2 \
  --resource-group rg-sbuxstudio \
  --yes

# Delete second Log Analytics workspace
az monitor log-analytics workspace delete \
  --workspace-name log-sbuxstudio2 \
  --resource-group rg-sbuxstudio \
  --yes
```

### Full Rollback (Remove All)

```bash
# Delete entire resource group (WARNING: This removes everything!)
az group delete \
  --name rg-sbuxstudio \
  --yes
```

## Troubleshooting

### Issue: VNet Not Found

**Error**: `Resource 'vnet-sbuxstudio' not found`

**Solution**: Ensure the VNet exists or set `deployNewVNet=true` to create it.

### Issue: DNS Zone Not Found

**Error**: `Private DNS Zone not found`

**Solution**: Ensure DNS zones exist or set `deployNewDnsZones=true` to create them.

### Issue: Container App Environment Deployment Fails

**Error**: `Subnet is already delegated to another service`

**Solution**: The subnet can only be used by one Container App Environment at a time. You need to use a different subnet or share the same Container App Environment.

**Note**: In this implementation, both environments share the same subnet. Azure Container Apps supports multiple environments in the same subnet.

### Issue: Role Assignment Fails

**Error**: `Principal not found`

**Solution**: Wait a few minutes for the managed identity to propagate, then retry the deployment.

## Best Practices

1. **Always deploy to non-production first**: Test the deployment in a development environment before production.
2. **Use consistent naming**: Follow the naming convention for easier management.
3. **Monitor both environments**: Set up monitoring and alerts for both Container App Environments.
4. **Share resources efficiently**: Reuse VNet, DNS zones, and private endpoints to reduce costs.
5. **Test connectivity**: Verify that both environments can access Storage and Cosmos DB via private endpoints.
6. **Document changes**: Keep track of which environment is which and their purposes.

## Cost Considerations

### Additional Costs for Second Environment

- **Container App Environment**: Included in Container Apps pricing
- **Log Analytics Workspace**: Based on data ingestion
- **Container Apps**: Based on vCPU/memory allocation

### No Additional Costs

- **VNet**: Free (shared)
- **DNS Zones**: Already created (shared)
- **Private Endpoints**: Already created (shared)
- **Storage Account**: Same account (shared)
- **Cosmos DB**: Same account (shared)

**Estimated Additional Monthly Cost**: ~$20-30 for the second Container App Environment and apps, depending on usage.

## Next Steps

1. Deploy the first environment with private endpoints
2. Verify the first environment is working
3. Deploy the second environment
4. Test both environments
5. Configure traffic routing if needed (e.g., Azure Front Door, Traffic Manager)
6. Set up monitoring and alerts
7. Document your specific configuration

## Related Documentation

- [PRIVATE_ENDPOINTS.md](PRIVATE_ENDPOINTS.md) - Private endpoints deployment guide
- [ARCHITECTURE_PRIVATE_ENDPOINTS.md](ARCHITECTURE_PRIVATE_ENDPOINTS.md) - Architecture details
- [QUICKSTART_PRIVATE_ENDPOINTS.md](QUICKSTART_PRIVATE_ENDPOINTS.md) - Quick start for existing deployment
- [DEPLOYMENT.md](DEPLOYMENT.md) - General deployment guide
