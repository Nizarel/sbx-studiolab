#!/bin/bash
# Deployment script for second Container App Environment
# This script demonstrates the deployment scenarios described in the problem statement

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Second Container App Environment Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
RESOURCE_GROUP="rg-sbuxstudio"
ENVIRONMENT_NAME="sbuxstudio"
SUBSCRIPTION_ID="b6e08f96-9a62-46d0-b276-8dc80e6bc02a"
TENANT_ID="16b3c013-d300-468d-ac64-7eda0820b6d3"

# Check if running in the correct directory
if [ ! -f "infra/main.bicep" ]; then
    echo -e "${RED}Error: Please run this script from the repository root directory${NC}"
    exit 1
fi

# Function to display menu
display_menu() {
    echo -e "${YELLOW}Select deployment scenario:${NC}"
    echo "1. Deploy FIRST environment with private endpoints (creates VNet, DNS, etc.)"
    echo "2. Deploy SECOND environment (reuses existing VNet, DNS, Storage, Cosmos)"
    echo "3. Test with deployNew=false (no changes, validation only)"
    echo "4. Update resources in-place (allows modifications to existing resources)"
    echo "5. Exit"
    echo ""
}

# Function to set Azure context
set_azure_context() {
    echo -e "${GREEN}Setting Azure context...${NC}"
    az account set --subscription "$SUBSCRIPTION_ID"
    echo -e "${GREEN}Using subscription: $SUBSCRIPTION_ID${NC}"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        echo -e "${RED}Error: Azure CLI is not installed${NC}"
        exit 1
    fi
    
    # Check if logged in
    if ! az account show &> /dev/null; then
        echo -e "${RED}Error: Not logged in to Azure. Please run 'az login' first${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Prerequisites OK${NC}"
    echo ""
}

# Scenario 1: First deployment with private endpoints
scenario_1() {
    echo -e "${GREEN}Scenario 1: Deploying first environment with private endpoints${NC}"
    echo -e "${YELLOW}This will create:${NC}"
    echo "  - Virtual Network: vnet-$ENVIRONMENT_NAME"
    echo "  - Container App Environment: cae-$ENVIRONMENT_NAME"
    echo "  - Container Apps: ca-backend-$ENVIRONMENT_NAME, ca-frontend-$ENVIRONMENT_NAME"
    echo "  - Private Endpoints and DNS Zones"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infra/main.bicep \
        --parameters infra/main.parameters.json \
        --parameters enablePrivateEndpoints=true \
        --parameters environmentName="$ENVIRONMENT_NAME" \
        --parameters deployNewVNet=true \
        --parameters deployNewDnsZones=true \
        --parameters deployNewPrivateEndpoints=true \
        --parameters deploySecondEnvironment=false
    
    echo -e "${GREEN}✓ Deployment complete!${NC}"
}

# Scenario 2: Second environment deployment
scenario_2() {
    echo -e "${GREEN}Scenario 2: Deploying second environment${NC}"
    echo -e "${YELLOW}This will create:${NC}"
    echo "  - Container App Environment: cae-${ENVIRONMENT_NAME}2"
    echo "  - Container Apps: ca-backend-${ENVIRONMENT_NAME}2, ca-frontend-${ENVIRONMENT_NAME}2"
    echo "  - Reuses existing VNet, DNS zones, Storage, Cosmos DB"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infra/main.bicep \
        --parameters infra/main.parameters.json \
        --parameters enablePrivateEndpoints=true \
        --parameters environmentName="$ENVIRONMENT_NAME" \
        --parameters deployNewVNet=false \
        --parameters deployNewDnsZones=false \
        --parameters deployNewPrivateEndpoints=false \
        --parameters deploySecondEnvironment=true
    
    echo -e "${GREEN}✓ Deployment complete!${NC}"
    echo ""
    echo -e "${YELLOW}New Container App URLs:${NC}"
    az containerapp show \
        --name "ca-frontend-${ENVIRONMENT_NAME}2" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv 2>/dev/null | xargs -I {} echo "Frontend: https://{}"
}

# Scenario 3: Test with deployNew=false
scenario_3() {
    echo -e "${GREEN}Scenario 3: Testing with deployNew=false (validation only)${NC}"
    echo -e "${YELLOW}This will validate the template without making changes${NC}"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    az deployment group validate \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infra/main.bicep \
        --parameters infra/main.parameters.json \
        --parameters enablePrivateEndpoints=true \
        --parameters environmentName="$ENVIRONMENT_NAME" \
        --parameters deployNewVNet=false \
        --parameters deployNewDnsZones=false \
        --parameters deployNewPrivateEndpoints=false
    
    echo -e "${GREEN}✓ Validation complete!${NC}"
}

# Scenario 4: Update resources in-place
scenario_4() {
    echo -e "${GREEN}Scenario 4: Update resources in-place${NC}"
    echo -e "${YELLOW}This will update existing resources${NC}"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infra/main.bicep \
        --parameters infra/main.parameters.json \
        --parameters enablePrivateEndpoints=true \
        --parameters environmentName="$ENVIRONMENT_NAME" \
        --parameters deployNewVNet=false \
        --parameters deployNewDnsZones=false \
        --parameters deployNewPrivateEndpoints=false \
        --parameters deploySecondEnvironment=false
    
    echo -e "${GREEN}✓ Deployment complete!${NC}"
}

# Main script
main() {
    check_prerequisites
    set_azure_context
    
    while true; do
        display_menu
        read -p "Enter your choice [1-5]: " choice
        
        case $choice in
            1)
                scenario_1
                ;;
            2)
                scenario_2
                ;;
            3)
                scenario_3
                ;;
            4)
                scenario_4
                ;;
            5)
                echo -e "${GREEN}Exiting...${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option. Please try again.${NC}"
                ;;
        esac
        
        echo ""
        echo -e "${YELLOW}Press Enter to continue...${NC}"
        read
    done
}

# Run main function
main
