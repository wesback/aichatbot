#!/bin/bash

# Azure Teams AI Chatbot - Teams Manifest Generator Script
# This script generates a Teams manifest.json file for deploying the bot to Microsoft Teams

set -e

# Default values
RESOURCE_GROUP_NAME=""
ENVIRONMENT="dev"
OUTPUT_DIR="./teams-app"
BOT_ID=""
APP_SERVICE_URL=""
COMPANY_NAME="Your Company"
WEBSITE_URL="https://yourwebsite.com"
PRIVACY_URL="https://yourwebsite.com/privacy"
TERMS_URL="https://yourwebsite.com/terms"
BOT_NAME="AI Chatbot"
BOT_DESCRIPTION_SHORT="AI-powered chatbot for Teams"
BOT_DESCRIPTION_FULL="An intelligent chatbot powered by Azure OpenAI for Microsoft Teams"
PACKAGE_NAME=""
VERSION="1.0.0"

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
    echo "  -g, --resource-group NAME    Azure resource group name (required)"
    echo "  -e, --environment ENV        Environment name (dev, staging, prod) [default: dev]"
    echo "  -o, --output-dir DIR         Output directory for Teams app package [default: ./teams-app]"
    echo "  -b, --bot-id ID              Bot App ID (if known, will skip Azure query)"
    echo "  -u, --app-url URL            App Service URL (if known, will skip Azure query)"
    echo "  -c, --company-name NAME      Company name [default: Your Company]"
    echo "  -w, --website-url URL        Company website URL [default: https://yourwebsite.com]"
    echo "  -p, --privacy-url URL        Privacy policy URL [default: https://yourwebsite.com/privacy]"
    echo "  -t, --terms-url URL          Terms of use URL [default: https://yourwebsite.com/terms]"
    echo "  -n, --bot-name NAME          Bot display name [default: AI Chatbot]"
    echo "  -s, --short-desc TEXT        Short description [default: AI-powered chatbot for Teams]"
    echo "  -f, --full-desc TEXT         Full description [default: An intelligent chatbot...]"
    echo "  --package-name NAME          Package name (auto-generated if not provided)"
    echo "  --version VERSION            App version [default: 1.0.0]"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g my-chatbot-rg"
    echo "  $0 -g my-chatbot-rg -e prod -c \"Contoso Ltd\" -w \"https://contoso.com\""
    echo "  $0 -g my-chatbot-rg -b \"12345678-1234-1234-1234-123456789012\" -u \"https://my-app.azurewebsites.net\""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP_NAME="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -b|--bot-id)
            BOT_ID="$2"
            shift 2
            ;;
        -u|--app-url)
            APP_SERVICE_URL="$2"
            shift 2
            ;;
        -c|--company-name)
            COMPANY_NAME="$2"
            shift 2
            ;;
        -w|--website-url)
            WEBSITE_URL="$2"
            shift 2
            ;;
        -p|--privacy-url)
            PRIVACY_URL="$2"
            shift 2
            ;;
        -t|--terms-url)
            TERMS_URL="$2"
            shift 2
            ;;
        -n|--bot-name)
            BOT_NAME="$2"
            shift 2
            ;;
        -s|--short-desc)
            BOT_DESCRIPTION_SHORT="$2"
            shift 2
            ;;
        -f|--full-desc)
            BOT_DESCRIPTION_FULL="$2"
            shift 2
            ;;
        --package-name)
            PACKAGE_NAME="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
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

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed or not in PATH"
    exit 1
fi

if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure CLI. Please run 'az login'"
    exit 1
fi

print_status "Starting Teams manifest generation..."
echo "Resource Group: $RESOURCE_GROUP_NAME"
echo "Environment: $ENVIRONMENT"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Get deployment outputs from Azure if not provided
if [[ -z "$BOT_ID" ]] || [[ -z "$APP_SERVICE_URL" ]]; then
    print_status "Retrieving deployment information from Azure..."
    
    # Find the most recent deployment
    DEPLOYMENT_NAME=$(az deployment group list \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --query "[?properties.provisioningState=='Succeeded'] | sort_by(@, &properties.timestamp) | [-1].name" \
        --output tsv 2>/dev/null || echo "")
    
    if [[ -z "$DEPLOYMENT_NAME" ]]; then
        print_warning "No successful deployments found. Trying to get resources directly..."
        
        # Try to find bot service directly
        if [[ -z "$BOT_ID" ]]; then
            BOT_RESOURCE=$(az bot show --resource-group "$RESOURCE_GROUP_NAME" --name "*-bot" \
                --query "{id:properties.msaAppId}" --output tsv 2>/dev/null || echo "")
            if [[ -n "$BOT_RESOURCE" ]]; then
                BOT_ID="$BOT_RESOURCE"
                print_status "Found Bot ID: $BOT_ID"
            fi
        fi
        
        # Try to find app service directly
        if [[ -z "$APP_SERVICE_URL" ]]; then
            APP_SERVICE_NAME=$(az webapp list --resource-group "$RESOURCE_GROUP_NAME" \
                --query "[0].name" --output tsv 2>/dev/null || echo "")
            if [[ -n "$APP_SERVICE_NAME" ]]; then
                APP_SERVICE_URL="https://${APP_SERVICE_NAME}.azurewebsites.net"
                print_status "Found App Service URL: $APP_SERVICE_URL"
            fi
        fi
    else
        print_status "Found deployment: $DEPLOYMENT_NAME"
        
        # Get outputs from deployment
        DEPLOYMENT_OUTPUTS=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --name "$DEPLOYMENT_NAME" \
            --query "properties.outputs" \
            --output json 2>/dev/null || echo "{}")
        
        if [[ "$DEPLOYMENT_OUTPUTS" != "{}" ]]; then
            if [[ -z "$BOT_ID" ]]; then
                BOT_ID=$(echo "$DEPLOYMENT_OUTPUTS" | jq -r '.botId.value // empty' 2>/dev/null || echo "")
                if [[ -n "$BOT_ID" ]]; then
                    print_status "Retrieved Bot ID from deployment: $BOT_ID"
                fi
            fi
            
            if [[ -z "$APP_SERVICE_URL" ]]; then
                APP_SERVICE_URL=$(echo "$DEPLOYMENT_OUTPUTS" | jq -r '.appServiceUrl.value // empty' 2>/dev/null || echo "")
                if [[ -n "$APP_SERVICE_URL" ]]; then
                    print_status "Retrieved App Service URL from deployment: $APP_SERVICE_URL"
                fi
            fi
        fi
    fi
fi

# Validate required information
if [[ -z "$BOT_ID" ]]; then
    print_error "Bot ID could not be retrieved or provided. Please specify with --bot-id"
    exit 1
fi

if [[ -z "$APP_SERVICE_URL" ]]; then
    print_error "App Service URL could not be retrieved or provided. Please specify with --app-url"
    exit 1
fi

# Generate package name if not provided
if [[ -z "$PACKAGE_NAME" ]]; then
    COMPANY_CLEAN=$(echo "$COMPANY_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    PACKAGE_NAME="com.${COMPANY_CLEAN}.teamschatbot"
fi

# Extract domain from app service URL for valid domains
VALID_DOMAIN=$(echo "$APP_SERVICE_URL" | sed -n 's|https\?://\([^/]*\).*|\1|p')

print_status "Using the following information:"
echo "  Bot ID: $BOT_ID"
echo "  App Service URL: $APP_SERVICE_URL"
echo "  Valid Domain: $VALID_DOMAIN"
echo "  Package Name: $PACKAGE_NAME"
echo ""

# Create output directory
print_status "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Generate the Teams manifest
print_status "Generating Teams manifest.json..."

cat > "$OUTPUT_DIR/manifest.json" <<EOF
{
  "\$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "$VERSION",
  "id": "$BOT_ID",
  "packageName": "$PACKAGE_NAME",
  "developer": {
    "name": "$COMPANY_NAME",
    "websiteUrl": "$WEBSITE_URL",
    "privacyUrl": "$PRIVACY_URL",
    "termsOfUseUrl": "$TERMS_URL"
  },
  "icons": {
    "color": "color.png",
    "outline": "outline.png"
  },
  "name": {
    "short": "$BOT_NAME",
    "full": "$BOT_NAME - $ENVIRONMENT"
  },
  "description": {
    "short": "$BOT_DESCRIPTION_SHORT",
    "full": "$BOT_DESCRIPTION_FULL"
  },
  "accentColor": "#0078D4",
  "bots": [
    {
      "botId": "$BOT_ID",
      "scopes": [
        "personal",
        "team",
        "groupchat"
      ],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "supportsCalling": false,
      "supportsVideo": false
    }
  ],
  "permissions": [
    "identity",
    "messageTeamMembers"
  ],
  "validDomains": [
    "$VALID_DOMAIN"
  ],
  "webApplicationInfo": {
    "id": "$BOT_ID",
    "resource": "$APP_SERVICE_URL"
  }
}
EOF

# Create placeholder icon files if they don't exist
if [[ ! -f "$OUTPUT_DIR/color.png" ]]; then
    print_status "Creating placeholder color icon..."
    
    # Create a simple SVG and convert to PNG (requires ImageMagick or create basic file)
    cat > "$OUTPUT_DIR/color.svg" <<'EOF'
<svg width="192" height="192" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="192" fill="#0078D4"/>
  <circle cx="96" cy="96" r="60" fill="white"/>
  <text x="96" y="106" text-anchor="middle" font-family="Arial, sans-serif" font-size="40" fill="#0078D4">AI</text>
</svg>
EOF

    # Try to convert SVG to PNG using ImageMagick
    if command -v convert &> /dev/null; then
        convert "$OUTPUT_DIR/color.svg" -resize 192x192 "$OUTPUT_DIR/color.png" 2>/dev/null || {
            print_warning "Could not convert SVG to PNG. Please replace $OUTPUT_DIR/color.svg with a 192x192 PNG file."
        }
        rm -f "$OUTPUT_DIR/color.svg"
    else
        print_warning "ImageMagick not found. Please convert $OUTPUT_DIR/color.svg to a 192x192 PNG file manually."
    fi
fi

if [[ ! -f "$OUTPUT_DIR/outline.png" ]]; then
    print_status "Creating placeholder outline icon..."
    
    cat > "$OUTPUT_DIR/outline.svg" <<'EOF'
<svg width="32" height="32" xmlns="http://www.w3.org/2000/svg">
  <rect width="32" height="32" fill="transparent" stroke="#424242" stroke-width="2"/>
  <circle cx="16" cy="16" r="10" fill="transparent" stroke="#424242" stroke-width="2"/>
  <text x="16" y="20" text-anchor="middle" font-family="Arial, sans-serif" font-size="8" fill="#424242">AI</text>
</svg>
EOF

    # Try to convert SVG to PNG using ImageMagick
    if command -v convert &> /dev/null; then
        convert "$OUTPUT_DIR/outline.svg" -resize 32x32 "$OUTPUT_DIR/outline.png" 2>/dev/null || {
            print_warning "Could not convert SVG to PNG. Please replace $OUTPUT_DIR/outline.svg with a 32x32 PNG file."
        }
        rm -f "$OUTPUT_DIR/outline.svg"
    else
        print_warning "ImageMagick not found. Please convert $OUTPUT_DIR/outline.svg to a 32x32 PNG file manually."
    fi
fi

# Create app package
print_status "Creating Teams app package..."
cd "$OUTPUT_DIR"

# Create zip file
if command -v zip &> /dev/null; then
    zip -q "${BOT_NAME// /-}-${ENVIRONMENT}-${VERSION}.zip" manifest.json *.png 2>/dev/null || {
        print_warning "Some icon files may be missing. Please ensure color.png and outline.png exist."
        zip -q "${BOT_NAME// /-}-${ENVIRONMENT}-${VERSION}.zip" manifest.json
    }
    PACKAGE_FILE="${BOT_NAME// /-}-${ENVIRONMENT}-${VERSION}.zip"
else
    print_warning "zip command not found. Please create a zip file manually with manifest.json and icon files."
    PACKAGE_FILE="(manual zip creation required)"
fi

cd - > /dev/null

# Create installation instructions
print_status "Creating installation instructions..."
cat > "$OUTPUT_DIR/INSTALLATION.md" <<EOF
# Teams App Installation Instructions

## Files Generated
- \`manifest.json\` - Teams app manifest
- \`color.png\` - 192x192 color icon (placeholder)
- \`outline.png\` - 32x32 outline icon (placeholder)
- \`${PACKAGE_FILE}\` - Complete app package

## Bot Information
- **Bot ID:** $BOT_ID
- **App Service URL:** $APP_SERVICE_URL
- **Environment:** $ENVIRONMENT
- **Package Name:** $PACKAGE_NAME

## Installation Steps

### Option 1: Teams Admin Center (Recommended for Organizations)
1. Go to [Teams Admin Center](https://admin.teams.microsoft.com/)
2. Navigate to **Teams apps** > **Manage apps**
3. Click **Upload** and select the \`${PACKAGE_FILE}\` file
4. Review and approve the app for your organization
5. Users can then install the app from the Teams app store

### Option 2: Sideloading (for Testing)
1. In Microsoft Teams, go to **Apps**
2. Click **Manage your apps** (bottom left)
3. Click **Upload an app** > **Upload a custom app**
4. Select the \`${PACKAGE_FILE}\` file
5. Click **Add** to install the bot

### Option 3: Manual Upload
1. Extract the zip file if needed
2. In Teams, go to **Apps** > **Manage your apps**
3. Click **Upload an app** > **Upload a custom app**
4. Upload the manifest.json file directly

## Post-Installation

### Testing the Bot
1. Search for "$BOT_NAME" in Teams
2. Start a conversation with the bot
3. Try these commands:
   - \`/help\` - Show help information
   - \`/clear\` - Clear conversation history
   - \`/summary\` - Show conversation summary
   - Send any message to test AI responses

### Troubleshooting
- Ensure the bot service is running: $APP_SERVICE_URL/health
- Check bot endpoint: $APP_SERVICE_URL/api/messages
- Verify Azure Bot Service registration in the Azure portal
- Review application logs for any errors

## Customization

### Icons
Replace the placeholder icon files with your custom icons:
- \`color.png\` - 192x192 pixels, full color app icon
- \`outline.png\` - 32x32 pixels, monochrome outline icon

### Manifest Updates
If you need to update the manifest:
1. Edit \`manifest.json\`
2. Update the version number
3. Recreate the zip package
4. Re-upload to Teams

## Security Notes
- The bot only has access to conversations where it's explicitly added
- All communication goes through the secure Bot Framework
- Bot credentials are managed through Azure Key Vault
- The app follows Microsoft Teams security guidelines

For more information, see the deployment documentation.
EOF

# Generate environment-specific notes
if [[ "$ENVIRONMENT" == "dev" ]]; then
    cat >> "$OUTPUT_DIR/INSTALLATION.md" <<EOF

## Development Environment Notes
- This is a development build
- Bot responses may include debug information
- Consider using sideloading for testing
- Monitor application logs for debugging: \`az webapp log tail -g $RESOURCE_GROUP_NAME -n \$(az webapp list -g $RESOURCE_GROUP_NAME --query "[0].name" -o tsv)\`
EOF
elif [[ "$ENVIRONMENT" == "prod" ]]; then
    cat >> "$OUTPUT_DIR/INSTALLATION.md" <<EOF

## Production Environment Notes
- This is a production build
- Use Teams Admin Center for organization-wide deployment
- Ensure proper governance and approval processes
- Monitor performance and usage through Application Insights
EOF
fi

print_success "Teams manifest generation completed!"
echo ""
echo "=== TEAMS APP PACKAGE SUMMARY ==="
echo "Output Directory: $OUTPUT_DIR"
echo "Manifest File: $OUTPUT_DIR/manifest.json"
echo "App Package: $OUTPUT_DIR/$PACKAGE_FILE"
echo "Installation Guide: $OUTPUT_DIR/INSTALLATION.md"
echo ""
echo "=== NEXT STEPS ==="
echo "1. Review the generated manifest.json"
echo "2. Replace placeholder icons with your custom icons (if desired)"
echo "3. Upload the app package to Microsoft Teams"
echo "4. Test the bot functionality"
echo ""
echo "=== QUICK TEST ==="
echo "Bot Health Check: curl $APP_SERVICE_URL/health"
echo "Bot Endpoint Test: curl -X GET $APP_SERVICE_URL/api/messages (should return 405)"
echo ""

print_success "Teams manifest generation script completed!"
