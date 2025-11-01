# Infrastructure (Bicep) Documentation

This directory contains all Azure infrastructure-as-code (Bicep) templates for deploying the Visionary Lab application.

## Quick Reference

### Main Templates

| File | Purpose |
|------|---------|
| `main.bicep` | Main orchestration template - deploys all resources |
| `main.parameters.json` | Parameter values for deployment |

### Modules

#### Core Infrastructure
| Module | Description |
|--------|-------------|
| `containerAppEnv.bicep` | Azure Container Apps Environment |
| `containerApp.bicep` | Individual Container App (backend/frontend) |
| `containerRegistry.bicep` | Azure Container Registry for Docker images |
| `storageAccount.bicep` | Azure Storage Account for images/videos |
| `storageAccountContainer.bicep` | Blob container within storage account |
| `cosmosDB.bicep` | Azure Cosmos DB for metadata storage |

#### Networking (Private Endpoints)
| Module | Description |
|--------|-------------|
| `virtualNetwork.bicep` | Virtual Network with subnets |
| `privateDnsZone.bicep` | Private DNS Zone (reusable) |
| `storagePrivateEndpoint.bicep` | Private endpoint for Storage |
| `cosmosPrivateEndpoint.bicep` | Private endpoint for Cosmos DB |

#### Security & Access
| Module | Description |
|--------|-------------|
| `cosmosRoleAssignment.bicep` | RBAC for Cosmos DB access |
| `storageRoleAssignment.bicep` | RBAC for Storage access |
| `openAiDeployment.bicep` | Azure OpenAI deployment configuration |

## Deployment Modes

### Public Endpoints (Default)
Deploys with public access to Storage and Cosmos DB:

```bash
azd up
# or
az deployment group create \
  --resource-group <rg-name> \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json
```

**Resources created:**
- Container Apps Environment
- Container Registry
- Storage Account (public access)
- Cosmos DB (public access)
- 2 Container Apps (backend, frontend)
- Log Analytics Workspace

### Private Endpoints (Secure)
Deploys with private network connectivity:

```bash
azd up --parameters enablePrivateEndpoints=true
# or
az deployment group create \
  --resource-group <rg-name> \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters enablePrivateEndpoints=true
```

**Additional resources created:**
- Virtual Network (10.0.0.0/16)
- 2 Subnets (Container Apps, Private Endpoints)
- 2 Private Endpoints (Storage, Cosmos DB)
- 2 Private DNS Zones
- DNS Zone Links
- Storage: public access disabled
- Cosmos DB: public access disabled

## Key Parameters

### Required Parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `environmentName` | Environment name (used in resource naming) | `prod`, `dev` |
| `location` | Azure region | `eastus`, `westus` |
| `LLM_AOAI_RESOURCE` | Azure OpenAI resource name for LLM | `myopenai` |
| `LLM_DEPLOYMENT` | LLM deployment name | `gpt-4o` |
| `LLM_AOAI_API_KEY` | LLM API key | `abc123...` |
| `IMAGEGEN_AOAI_RESOURCE` | Azure OpenAI resource for image gen | `myopenai` |
| `IMAGEGEN_DEPLOYMENT` | Image generation deployment name | `gpt-image-1` |
| `IMAGEGEN_AOAI_API_KEY` | Image gen API key | `xyz789...` |
| `SORA_AOAI_RESOURCE` | Azure OpenAI resource for Sora | `myopenai` |
| `SORA_DEPLOYMENT` | Sora deployment name | `sora` |
| `SORA_AOAI_API_KEY` | Sora API key | `def456...` |

### Optional Parameters (Private Endpoints)
| Parameter | Default | Description |
|-----------|---------|-------------|
| `enablePrivateEndpoints` | `false` | Enable private endpoints |
| `vnetName` | `vnet-{environmentName}` | Virtual Network name |
| `vnetAddressPrefix` | `10.0.0.0/16` | VNet address space |
| `containerAppsSubnetPrefix` | `10.0.0.0/23` | Container Apps subnet |
| `privateEndpointsSubnetPrefix` | `10.0.2.0/24` | Private endpoints subnet |

## Resource Naming Convention

Resources are named using the pattern: `{type}-{environmentName}`

Examples:
- Container App Environment: `cae-prod`
- Backend Container App: `ca-backend-prod`
- Storage Account: `st{uniqueString}`
- Cosmos DB: `{prefix}-visionary-lab-cosmos`
- VNet: `vnet-prod`

## Architecture Flow

```
main.bicep
├── Virtual Network (if enablePrivateEndpoints=true)
├── Private DNS Zones (if enablePrivateEndpoints=true)
├── Storage Account
│   ├── Storage Container
│   └── Private Endpoint (if enablePrivateEndpoints=true)
├── Cosmos DB
│   └── Private Endpoint (if enablePrivateEndpoints=true)
├── Container Registry
├── Container App Environment (VNet integrated if enablePrivateEndpoints=true)
│   ├── Backend Container App
│   └── Frontend Container App
├── RBAC Assignments
│   ├── Cosmos DB Role
│   └── Storage Role
└── OpenAI Deployments (references)
```

## Validation

Before deployment, validate templates:

```bash
# Validate main template
az bicep build --file infra/main.bicep

# Run validation script
./validate-deployment.sh
```

## Outputs

After deployment, main.bicep outputs:

| Output | Description |
|--------|-------------|
| `AZURE_LOCATION` | Deployment location |
| `AZURE_CONTAINER_ENVIRONMENT_NAME` | Container App Environment ID |
| `AZURE_CONTAINER_REGISTRY_ENDPOINT` | Container Registry login server |
| `BACKEND_URI` | Backend application URL |
| `FRONTEND_URI` | Frontend application URL |
| `AZURE_STORAGE_ACCOUNT_NAME` | Storage account name |
| `AZURE_BLOB_SERVICE_URL` | Blob service endpoint |
| `COSMOS_DB_ENDPOINT` | Cosmos DB endpoint |
| `COSMOS_DB_DATABASE_NAME` | Database name |
| `COSMOS_DB_CONTAINER_NAME` | Container name |

## Security Features

### Authentication
- **Managed Identity**: All service-to-service authentication uses managed identities
- **RBAC**: Role-based access control for Storage and Cosmos DB
- **No Secrets**: No connection strings or keys stored in environment variables

### Network Security
- **Private Endpoints**: Optional private-only connectivity
- **VNet Integration**: Container Apps can be VNet-integrated
- **Private DNS**: Automatic DNS resolution for private endpoints
- **TLS 1.2**: Minimum TLS version enforced

## Customization

### Custom VNet Address Space

```bash
azd up \
  --parameters enablePrivateEndpoints=true \
  --parameters vnetAddressPrefix="172.16.0.0/16" \
  --parameters containerAppsSubnetPrefix="172.16.0.0/23" \
  --parameters privateEndpointsSubnetPrefix="172.16.2.0/24"
```

### Reuse Existing Resources

Set `deployNew: false` in module parameters to reuse existing resources:
- Storage Account: `deployNew: false` in storageAccount.bicep
- Cosmos DB: `deployNew: false` in cosmosDB.bicep
- Container Registry: `deployNew: false` in containerRegistry.bicep

## Troubleshooting

### Common Issues

**Error: "Subnet size too small"**
- Container Apps subnet must be /23 or larger
- Increase subnet size in parameters

**Error: "CIDR overlap"**
- Check for conflicts with existing VNets
- Use different address space

**Error: "Private endpoint not approved"**
- Private endpoints auto-approve for same subscription
- Check permissions if manual approval required

### Debug Commands

```bash
# Check deployment status
az deployment group show \
  --resource-group <rg-name> \
  --name <deployment-name>

# View deployment operations
az deployment operation group list \
  --resource-group <rg-name> \
  --name <deployment-name>

# Check specific resource
az resource show --ids <resource-id>
```

## Documentation

- **[PRIVATE_ENDPOINTS.md](../PRIVATE_ENDPOINTS.md)** - Private endpoints deployment guide
- **[ARCHITECTURE_PRIVATE_ENDPOINTS.md](../ARCHITECTURE_PRIVATE_ENDPOINTS.md)** - Architecture details
- **[QUICKSTART_PRIVATE_ENDPOINTS.md](../QUICKSTART_PRIVATE_ENDPOINTS.md)** - Quick start guide
- **[DEPLOYMENT.md](../DEPLOYMENT.md)** - General deployment guide

## Cost Estimation

### Base Deployment (Public Endpoints)
- Container Apps: ~$50-100/month
- Storage Account: ~$10-20/month
- Cosmos DB: ~$25-50/month
- Container Registry: ~$5/month
- Log Analytics: ~$10/month
- **Total**: ~$100-185/month

### Additional Cost (Private Endpoints)
- Private Endpoints: ~$15/month
- Private DNS Zones: ~$1/month
- VNet: Free
- **Additional**: ~$16/month

## Support

For issues:
1. Check [PRIVATE_ENDPOINTS.md](../PRIVATE_ENDPOINTS.md) troubleshooting section
2. Validate templates: `az bicep build --file infra/main.bicep`
3. Review deployment logs in Azure Portal
4. Check Container App logs for runtime issues

## Version History

- **v1.1** - Added private endpoints support
- **v1.0** - Initial public endpoint deployment
