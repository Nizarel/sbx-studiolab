#!/bin/bash
# Pre-deployment validation script for private endpoints
# This script validates the Bicep templates and checks prerequisites

set -e

echo "=========================================="
echo "Private Endpoints Pre-Deployment Validation"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Azure CLI is installed
echo "Checking prerequisites..."
if ! command -v az &> /dev/null; then
    echo -e "${RED}✗ Azure CLI is not installed${NC}"
    echo "  Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
else
    echo -e "${GREEN}✓ Azure CLI installed${NC}"
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo -e "${RED}✗ Not logged in to Azure${NC}"
    echo "  Run: az login"
    exit 1
else
    echo -e "${GREEN}✓ Logged in to Azure${NC}"
    SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    echo "  Subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"
fi

echo ""
echo "Validating Bicep templates..."

# Validate main.bicep
if az bicep build --file infra/main.bicep --stdout > /dev/null 2>&1; then
    echo -e "${GREEN}✓ main.bicep is valid${NC}"
else
    echo -e "${RED}✗ main.bicep has errors${NC}"
    echo "  Run: az bicep build --file infra/main.bicep"
    exit 1
fi

# Validate individual modules
MODULES=(
    "infra/modules/virtualNetwork.bicep"
    "infra/modules/privateDnsZone.bicep"
    "infra/modules/storagePrivateEndpoint.bicep"
    "infra/modules/cosmosPrivateEndpoint.bicep"
    "infra/modules/storageAccount.bicep"
    "infra/modules/cosmosDB.bicep"
)

ALL_VALID=true
for module in "${MODULES[@]}"; do
    if [ -f "$module" ]; then
        if az bicep build --file "$module" --stdout > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $(basename $module) is valid${NC}"
        else
            echo -e "${RED}✗ $(basename $module) has errors${NC}"
            ALL_VALID=false
        fi
    else
        echo -e "${RED}✗ $(basename $module) not found${NC}"
        ALL_VALID=false
    fi
done

if [ "$ALL_VALID" = false ]; then
    exit 1
fi

echo ""
echo "Checking required files..."

REQUIRED_FILES=(
    "infra/main.bicep"
    "infra/main.parameters.json"
    "PRIVATE_ENDPOINTS.md"
    "QUICKSTART_PRIVATE_ENDPOINTS.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        echo -e "${RED}✗ $file not found${NC}"
        exit 1
    fi
done

echo ""
echo "Checking network configuration..."

# Check if parameters are set correctly
ENABLE_PE=$(grep -A 2 "enablePrivateEndpoints" infra/main.parameters.json | grep "value" | awk '{print $2}' | tr -d '",')

if [ "$ENABLE_PE" = "true" ]; then
    echo -e "${YELLOW}⚠ Private endpoints are ENABLED in parameters file${NC}"
    echo "  This will create VNet and private endpoints"
    echo "  Additional cost: ~\$15-20/month"
elif [ "$ENABLE_PE" = "false" ]; then
    echo -e "${GREEN}✓ Private endpoints are DISABLED in parameters file${NC}"
    echo "  To enable, set to true or use --parameters enablePrivateEndpoints=true"
else
    echo -e "${RED}✗ Could not determine enablePrivateEndpoints value${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ All validations passed!${NC}"
echo "=========================================="
echo ""
echo "Ready to deploy!"
echo ""
echo "Deployment options:"
echo ""
echo "1. Deploy with private endpoints (recommended for production):"
echo "   azd up --parameters enablePrivateEndpoints=true"
echo ""
echo "2. Deploy with public endpoints (default, lower cost):"
echo "   azd up"
echo ""
echo "3. Deploy with Azure CLI:"
echo "   az deployment group create \\"
echo "     --resource-group <your-rg> \\"
echo "     --template-file infra/main.bicep \\"
echo "     --parameters infra/main.parameters.json \\"
echo "     --parameters enablePrivateEndpoints=true"
echo ""
echo "For detailed instructions, see:"
echo "- QUICKSTART_PRIVATE_ENDPOINTS.md (for rg-sbuxstudio scenario)"
echo "- PRIVATE_ENDPOINTS.md (comprehensive guide)"
echo ""
