#!/bin/bash

# Azure Teams AI Chatbot - Infrastructure Deployment Script
# This script deploys all required Azure resources using Bicep templates

set -e

# Default values
RESOURCE_GROUP_NAME=""
LOCATION="eastus"
ENVIRONMENT="dev"
SUBSCRIPTION_ID=""
APP_NAME="teamschatbot"
SQL_ADMIN_PASSWORD=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --resource-group      Resource group name (required)"
    echo "  -l, --location           Azure location (default: eastus)"
    echo "  -e, --environment        Environment (dev/staging/prod, default: dev)"
    echo "  -s, --subscription       Azure subscription ID (optional)"
    echo "  -n, --app-name          Application name (default: teamschatbot)"
    echo "  -p, --sql-password      SQL admin password (required for prod with SQL)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g myapp-dev-rg -e dev"
    echo "  $0 -g myapp-prod-rg -e prod -p MySecurePassword123!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP_NAME="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -n|--app-name)
            APP_NAME="$2"
            shift 2
            ;;
        -p|--sql-password)
            SQL_ADMIN_PASSWORD="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$RESOURCE_GROUP_NAME" ]]; then
    print_error "Resource group name is required"
    show_usage
    exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Environment must be one of: dev, staging, prod"
    exit 1
fi

# Set subscription if provided
if [[ -n "$SUBSCRIPTION_ID" ]]; then
    print_status "Setting Azure subscription to $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Verify Azure CLI login
print_status "Verifying Azure CLI login..."
if ! az account show >/dev/null 2>&1; then
    print_error "Please login to Azure CLI first: az login"
    exit 1
fi

CURRENT_SUBSCRIPTION=$(az account show --query id -o tsv)
print_status "Using Azure subscription: $CURRENT_SUBSCRIPTION"

# Create resource group if it doesn't exist
print_status "Checking if resource group '$RESOURCE_GROUP_NAME' exists..."
if ! az group show --name "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
    print_status "Creating resource group '$RESOURCE_GROUP_NAME' in '$LOCATION'..."
    az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION"
    print_success "Resource group created successfully"
else
    print_status "Resource group already exists"
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Determine parameters file
PARAMS_FILE="$PROJECT_ROOT/deployment/bicep/parameters.${ENVIRONMENT}.json"
if [[ ! -f "$PARAMS_FILE" ]]; then
    print_error "Parameters file not found: $PARAMS_FILE"
    exit 1
fi

# Prepare deployment parameters
DEPLOYMENT_NAME="${APP_NAME}-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
BICEP_FILE="$PROJECT_ROOT/deployment/bicep/main.bicep"

if [[ ! -f "$BICEP_FILE" ]]; then
    print_error "Bicep template not found: $BICEP_FILE"
    exit 1
fi

# Build deployment command
DEPLOY_CMD="az deployment group create \
    --resource-group $RESOURCE_GROUP_NAME \
    --template-file $BICEP_FILE \
    --parameters @$PARAMS_FILE \
    --parameters appName=$APP_NAME \
    --parameters location=$LOCATION \
    --name $DEPLOYMENT_NAME"

# Add SQL password if provided
if [[ -n "$SQL_ADMIN_PASSWORD" ]]; then
    DEPLOY_CMD="$DEPLOY_CMD --parameters sqlAdminPassword=$SQL_ADMIN_PASSWORD"
elif [[ "$ENVIRONMENT" == "prod" ]]; then
    # Check if SQL is enabled in parameters file
    SQL_ENABLED=$(jq -r '.parameters.enableSqlDatabase.value' "$PARAMS_FILE" 2>/dev/null || echo "false")
    if [[ "$SQL_ENABLED" == "true" ]]; then
        print_error "SQL admin password is required for production environment with SQL enabled"
        print_error "Use -p or --sql-password to provide the password"
        exit 1
    fi
fi

# Deploy infrastructure
print_status "Starting infrastructure deployment..."
print_status "Deployment name: $DEPLOYMENT_NAME"
print_status "Using parameters file: $PARAMS_FILE"

if eval "$DEPLOY_CMD"; then
    print_success "Infrastructure deployment completed successfully!"
else
    print_error "Infrastructure deployment failed"
    exit 1
fi

# Get deployment outputs
print_status "Retrieving deployment outputs..."
OUTPUTS=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs \
    --output json)

if [[ -n "$OUTPUTS" ]]; then
    echo ""
    print_success "Deployment completed successfully!"
    echo ""
    echo "=== DEPLOYMENT OUTPUTS ==="
    
    # Extract and display key outputs
    APP_SERVICE_NAME=$(echo "$OUTPUTS" | jq -r '.appServiceName.value // "N/A"')
    APP_SERVICE_URL=$(echo "$OUTPUTS" | jq -r '.appServiceUrl.value // "N/A"')
    KEY_VAULT_NAME=$(echo "$OUTPUTS" | jq -r '.keyVaultName.value // "N/A"')
    OPENAI_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.openAiEndpoint.value // "N/A"')
    BOT_NAME=$(echo "$OUTPUTS" | jq -r '.botName.value // "N/A"')
    
    echo "App Service Name: $APP_SERVICE_NAME"
    echo "App Service URL: $APP_SERVICE_URL"
    echo "Key Vault Name: $KEY_VAULT_NAME"
    echo "OpenAI Endpoint: $OPENAI_ENDPOINT"
    echo "Bot Name: $BOT_NAME"
    
    echo ""
    echo "=== NEXT STEPS ==="
    echo "1. Deploy the application code to the App Service"
    echo "2. Configure the Bot Framework registration"
    echo "3. Install the Teams app using the manifest"
    echo ""
    echo "Run the application deployment script:"
    echo "./deployment/scripts/deploy-application.sh -g $RESOURCE_GROUP_NAME -a $APP_SERVICE_NAME"
    
else
    print_warning "Could not retrieve deployment outputs"
fi

print_success "Infrastructure deployment script completed!"