#!/bin/bash

# Azure Teams AI Chatbot - Application Deployment Script
# This script deploys the Python application to Azure App Service

set -e

# Default values
RESOURCE_GROUP_NAME=""
APP_SERVICE_NAME=""
ENVIRONMENT="dev"
BUILD_LOCALLY=false

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
    echo "  -a, --app-service         App Service name (required)"
    echo "  -e, --environment         Environment (dev/staging/prod, default: dev)"
    echo "  -b, --build-locally       Build locally instead of using Oryx (default: false)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g myapp-dev-rg -a myapp-dev-app"
    echo "  $0 -g myapp-prod-rg -a myapp-prod-app -e prod -b"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP_NAME="$2"
            shift 2
            ;;
        -a|--app-service)
            APP_SERVICE_NAME="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--build-locally)
            BUILD_LOCALLY=true
            shift
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

if [[ -z "$APP_SERVICE_NAME" ]]; then
    print_error "App Service name is required"
    show_usage
    exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Environment must be one of: dev, staging, prod"
    exit 1
fi

# Verify Azure CLI login
print_status "Verifying Azure CLI login..."
if ! az account show >/dev/null 2>&1; then
    print_error "Please login to Azure CLI first: az login"
    exit 1
fi

# Verify App Service exists
print_status "Verifying App Service '$APP_SERVICE_NAME' exists..."
if ! az webapp show --resource-group "$RESOURCE_GROUP_NAME" --name "$APP_SERVICE_NAME" >/dev/null 2>&1; then
    print_error "App Service '$APP_SERVICE_NAME' not found in resource group '$RESOURCE_GROUP_NAME'"
    exit 1
fi

# Create .env file for the environment
print_status "Creating environment configuration..."
ENV_FILE=".env.${ENVIRONMENT}"

cat > "$ENV_FILE" <<EOF
# Azure Teams AI Chatbot - ${ENVIRONMENT^^} Environment Configuration
FLASK_ENV=${ENVIRONMENT}
LOG_LEVEL=INFO
PORT=8000

# Azure OpenAI Configuration (will be set via App Service configuration)
# AZURE_OPENAI_ENDPOINT=
# AZURE_OPENAI_API_KEY=
# AZURE_OPENAI_DEPLOYMENT_NAME=

# Bot Framework Configuration (will be set via Key Vault)
# MICROSOFT_APP_ID=
# MICROSOFT_APP_PASSWORD=

# Azure Key Vault (will be set via App Service configuration)
# AZURE_KEY_VAULT_URL=

# Application Configuration
MAX_CONVERSATION_HISTORY=10
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# Conversation Configuration
MAX_CONVERSATION_HISTORY=20
OPENAI_MAX_TOKENS=1500
OPENAI_TEMPERATURE=0.7
EOF

print_success "Environment configuration created: $ENV_FILE"

# Prepare deployment package
print_status "Preparing deployment package..."

# Create temporary deployment directory
DEPLOY_DIR=$(mktemp -d)
print_status "Using temporary directory: $DEPLOY_DIR"

# Copy application files
cp -r src/ "$DEPLOY_DIR/"
cp app.py "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"
cp "$ENV_FILE" "$DEPLOY_DIR/.env"
cp README.md "$DEPLOY_DIR/" 2>/dev/null || true

# Create startup script for App Service
cat > "$DEPLOY_DIR/startup.sh" <<'EOF'
#!/bin/bash

# Azure App Service startup script for Python Flask application
echo "Starting Azure Teams AI Chatbot..."

# Set default port if not provided
export PORT=${PORT:-8000}

# Install dependencies if requirements.txt has changed
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start the application with Gunicorn
echo "Starting application on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --preload app:app
EOF

chmod +x "$DEPLOY_DIR/startup.sh"

# If building locally, install dependencies
if [[ "$BUILD_LOCALLY" == true ]]; then
    print_status "Building application locally..."
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    
    print_success "Local build completed"
fi

# Create zip package for deployment
DEPLOY_ZIP="$DEPLOY_DIR/deployment.zip"
print_status "Creating deployment package..."

cd "$DEPLOY_DIR"
zip -r deployment.zip . -x "*.pyc" "__pycache__/*" "*.log" ".env.*"
cd - > /dev/null

# Deploy to App Service
print_status "Deploying application to App Service '$APP_SERVICE_NAME'..."

az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$APP_SERVICE_NAME" \
    --src "$DEPLOY_ZIP"

if [[ $? -eq 0 ]]; then
    print_success "Application deployed successfully!"
else
    print_error "Application deployment failed"
    exit 1
fi

# Configure App Service settings
print_status "Configuring App Service settings..."

# Set startup command
az webapp config set \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$APP_SERVICE_NAME" \
    --startup-file "startup.sh"

# Set additional app settings
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$APP_SERVICE_NAME" \
    --settings \
        FLASK_ENV="$ENVIRONMENT" \
        LOG_LEVEL="INFO" \
        PORT="8000" \
        PYTHONPATH="/home/site/wwwroot"

print_success "App Service configuration completed"

# Get App Service URL
APP_URL=$(az webapp show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$APP_SERVICE_NAME" \
    --query defaultHostName \
    --output tsv)

# Wait for deployment to complete
print_status "Waiting for deployment to complete..."
sleep 30

# Test health endpoint
print_status "Testing application health..."
HEALTH_URL="https://${APP_URL}/health"

for i in {1..5}; do
    if curl -s -f "$HEALTH_URL" >/dev/null 2>&1; then
        print_success "Application is healthy and responding"
        break
    else
        if [[ $i -eq 5 ]]; then
            print_warning "Health check failed - application may still be starting"
        else
            print_status "Health check attempt $i/5 failed, retrying..."
            sleep 10
        fi
    fi
done

# Clean up temporary files
rm -rf "$DEPLOY_DIR"
rm -f "$ENV_FILE"

echo ""
print_success "Application deployment completed successfully!"
echo ""
echo "=== DEPLOYMENT SUMMARY ==="
echo "App Service Name: $APP_SERVICE_NAME"
echo "App Service URL: https://${APP_URL}"
echo "Health Check URL: https://${APP_URL}/health"
echo "Bot Endpoint: https://${APP_URL}/api/messages"
echo "Web Interface: https://${APP_URL}/"
echo ""
echo "=== NEXT STEPS ==="
echo "1. Configure Bot Framework App ID and Password in Key Vault"
echo "2. Test the bot using the Bot Framework Emulator"
echo "3. Install the Teams app using the manifest"
echo "4. Monitor application logs: az webapp log tail -g $RESOURCE_GROUP_NAME -n $APP_SERVICE_NAME"

print_success "Application deployment script completed!"