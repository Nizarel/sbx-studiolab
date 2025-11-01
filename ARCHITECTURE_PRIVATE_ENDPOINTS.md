# Private Endpoint Architecture Summary

## Overview

This document provides a quick reference for the private endpoint architecture implemented in this repository.

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure Subscription                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Virtual Network (VNet)                                     │ │
│  │  Address Space: 10.0.0.0/16 (customizable)                 │ │
│  │                                                              │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │  Container Apps Subnet                               │   │ │
│  │  │  Address: 10.0.0.0/23                                │   │ │
│  │  │  Delegation: Microsoft.App/environments              │   │ │
│  │  │                                                       │   │ │
│  │  │  ┌──────────────────────────────────────┐            │   │ │
│  │  │  │  Container App Environment            │            │   │ │
│  │  │  │  - Backend Container App              │            │   │ │
│  │  │  │  - Frontend Container App             │            │   │ │
│  │  │  │  - Managed Identities enabled         │            │   │ │
│  │  │  └──────────────────────────────────────┘            │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  │                                                              │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │  Private Endpoints Subnet                            │   │ │
│  │  │  Address: 10.0.2.0/24                                │   │ │
│  │  │  Private Endpoint Network Policies: Disabled         │   │ │
│  │  │                                                       │   │ │
│  │  │  ┌──────────────────┐  ┌──────────────────┐         │   │ │
│  │  │  │  PE: Storage     │  │  PE: Cosmos DB   │         │   │ │
│  │  │  │  (Blob Service)  │  │  (SQL API)       │         │   │ │
│  │  │  │  Private IP      │  │  Private IP      │         │   │ │
│  │  │  └──────────────────┘  └──────────────────┘         │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  │                                                              │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │  Private DNS Zones (linked to VNet)                  │   │ │
│  │  │  - privatelink.blob.core.windows.net                 │   │ │
│  │  │  - privatelink.documents.azure.com                   │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────┐         ┌────────────────┐                  │
│  │  Storage        │         │  Cosmos DB     │                  │
│  │  Account        │         │  Account       │                  │
│  │                 │         │                │                  │
│  │  Public Access: │         │  Public Access:│                  │
│  │  DISABLED       │         │  DISABLED      │                  │
│  └────────────────┘         └────────────────┘                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Traffic Flow

### With Private Endpoints Enabled

1. **Container App → Storage Account (Blob)**
   - Traffic routes through VNet via Private Endpoint
   - DNS resolves to private IP (10.0.2.x)
   - No public internet traversal
   - Uses Managed Identity for authentication

2. **Container App → Cosmos DB**
   - Traffic routes through VNet via Private Endpoint
   - DNS resolves to private IP (10.0.2.x)
   - No public internet traversal
   - Uses Managed Identity for authentication

3. **External User → Container Apps**
   - Ingress remains public via Container Apps default domain
   - Only data services are private

### Without Private Endpoints (Default)

1. **Container App → Storage Account**
   - Traffic goes over Azure backbone (not internet)
   - Uses public endpoint with Azure AD authentication
   - Storage has public network access enabled

2. **Container App → Cosmos DB**
   - Traffic goes over Azure backbone (not internet)
   - Uses public endpoint with Azure AD authentication
   - Cosmos DB has public network access enabled

## Deployment Parameter: enablePrivateEndpoints

### When `enablePrivateEndpoints = false` (Default)
- ❌ No VNet created
- ❌ No Private Endpoints
- ❌ No Private DNS Zones
- ✅ Storage: Public access enabled
- ✅ Cosmos DB: Public access enabled
- ✅ Container Apps: No VNet integration
- ✅ Simpler deployment, lower cost

### When `enablePrivateEndpoints = true`
- ✅ VNet with two subnets created
- ✅ Private Endpoints for Storage and Cosmos DB
- ✅ Private DNS Zones with VNet links
- ✅ Storage: Public access disabled
- ✅ Cosmos DB: Public access disabled
- ✅ Container Apps: VNet integrated
- ✅ Enhanced security, compliance ready

## Key Resources Created (Private Endpoints Enabled)

| Resource Type | Name Pattern | Purpose |
|--------------|--------------|---------|
| Virtual Network | `vnet-{environmentName}` | Network isolation |
| Subnet | `snet-containerApps` | Container Apps delegation |
| Subnet | `snet-privateEndpoints` | Private endpoint NICs |
| Private Endpoint | `pe-{storageAccountName}` | Storage private connectivity |
| Private Endpoint | `pe-{cosmosAccountName}` | Cosmos DB private connectivity |
| Private DNS Zone | `privatelink.blob.core.windows.net` | Storage DNS resolution |
| Private DNS Zone | `privatelink.documents.azure.com` | Cosmos DB DNS resolution |
| DNS Zone Link | Auto-generated | Links DNS zones to VNet |
| DNS Zone Group | `default` | Auto-registers private IPs in DNS |

## Security Posture Comparison

| Aspect | Public Endpoints | Private Endpoints |
|--------|-----------------|-------------------|
| Storage Access | Public (Azure AD auth) | Private only (VNet + Azure AD) |
| Cosmos DB Access | Public (Azure AD auth) | Private only (VNet + Azure AD) |
| Network Isolation | Azure backbone only | Full VNet isolation |
| Internet Exposure | Public endpoints available | No internet exposure |
| Compliance | Standard | Enhanced (private-only) |
| Cost | Lower | ~$15-20/month additional |

## RBAC Permissions

Both configurations use **Managed Identity** with RBAC:

- **Storage Account**: `Storage Blob Data Contributor` role assigned to backend Container App
- **Cosmos DB**: Custom SQL Role (Data Contributor) assigned to backend Container App

No keys or connection strings are stored in environment variables.

## DNS Resolution Example

### With Private Endpoints

```bash
# Storage Account DNS lookup
$ nslookup stpp37s7tza4fqc.blob.core.windows.net

Name:    stpp37s7tza4fqc.privatelink.blob.core.windows.net
Address: 10.0.2.4  # Private IP within VNet
Aliases: stpp37s7tza4fqc.blob.core.windows.net

# Cosmos DB DNS lookup
$ nslookup pp37s-visionary-lab-cosmos.documents.azure.com

Name:    pp37s-visionary-lab-cosmos.privatelink.documents.azure.com
Address: 10.0.2.5  # Private IP within VNet
Aliases: pp37s-visionary-lab-cosmos.documents.azure.com
```

### Without Private Endpoints

```bash
# Storage Account DNS lookup
$ nslookup stpp37s7tza4fqc.blob.core.windows.net

Name:    blob.ams20prdstr01a.store.core.windows.net
Address: 52.239.xxx.xxx  # Public IP
Aliases: stpp37s7tza4fqc.blob.core.windows.net

# Cosmos DB DNS lookup
$ nslookup pp37s-visionary-lab-cosmos.documents.azure.com

Name:    pp37s-visionary-lab-cosmos.documents.azure.com
Address: 20.118.xxx.xxx  # Public IP
```

## Migration Checklist

When migrating from public to private endpoints:

- [ ] Review and plan VNet address space (avoid conflicts)
- [ ] Test in non-production environment first
- [ ] Schedule maintenance window (brief service interruption expected)
- [ ] Run deployment with `enablePrivateEndpoints=true`
- [ ] Verify private endpoints are created
- [ ] Verify DNS zones are linked to VNet
- [ ] Test application functionality (image generation, gallery, etc.)
- [ ] Monitor Container App logs for connectivity issues
- [ ] Verify managed identity RBAC permissions are working
- [ ] Update documentation with new architecture

## Troubleshooting Quick Reference

| Issue | Check | Fix |
|-------|-------|-----|
| Can't connect to Storage | `az network private-endpoint show` | Verify PE exists and is approved |
| Can't connect to Cosmos DB | `az network private-endpoint show` | Verify PE exists and is approved |
| DNS not resolving to private IP | `az network private-dns zone show` | Verify DNS zone linked to VNet |
| Container Apps deployment fails | Check subnet delegation | Ensure delegation to `Microsoft.App/environments` |
| CIDR conflict error | Review existing VNets | Choose non-overlapping address space |

## References

- [Azure Private Link Documentation](https://docs.microsoft.com/azure/private-link/)
- [Container Apps VNet Integration](https://docs.microsoft.com/azure/container-apps/vnet-custom)
- [Private Endpoints for Storage](https://docs.microsoft.com/azure/storage/common/storage-private-endpoints)
- [Private Endpoints for Cosmos DB](https://docs.microsoft.com/azure/cosmos-db/how-to-configure-private-endpoints)
