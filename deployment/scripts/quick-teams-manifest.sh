#!/bin/bash

# Quick Teams Manifest Generator
# Simple version of the Teams manifest generator for quick deployment

set -e

# Default values
RESOURCE_GROUP=${1:-""}
BOT_NAME=${2:-"AI Chatbot"}
COMPANY_NAME=${3:-"Your Company"}

if [[ -z "$RESOURCE_GROUP" ]]; then
    echo "Usage: $0 <resource-group> [bot-name] [company-name]"
    echo ""
    echo "Examples:"
    echo "  $0 my-chatbot-rg"
    echo "  $0 my-chatbot-rg \"My AI Assistant\" \"Contoso Ltd\""
    exit 1
fi

echo "🚀 Quick Teams Manifest Generator"
echo "Resource Group: $RESOURCE_GROUP"
echo "Bot Name: $BOT_NAME"
echo "Company: $COMPANY_NAME"
echo ""

# Check Azure CLI
if ! command -v az &> /dev/null || ! az account show &> /dev/null; then
    echo "❌ Azure CLI not found or not logged in"
    echo "Please install Azure CLI and run 'az login'"
    exit 1
fi

# Get bot information
echo "🔍 Looking up bot information..."
BOT_ID=$(az bot list -g "$RESOURCE_GROUP" --query "[0].properties.msaAppId" -o tsv 2>/dev/null || echo "")
APP_NAME=$(az webapp list -g "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")

if [[ -z "$BOT_ID" ]] || [[ -z "$APP_NAME" ]]; then
    echo "❌ Could not find bot or app service in resource group: $RESOURCE_GROUP"
    exit 1
fi

APP_URL="https://${APP_NAME}.azurewebsites.net"

echo "✅ Found Bot ID: $BOT_ID"
echo "✅ Found App URL: $APP_URL"

# Create manifest
mkdir -p teams-app
cat > teams-app/manifest.json <<EOF
{
  "\$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "$BOT_ID",
  "packageName": "com.yourcompany.teamschatbot",
  "developer": {
    "name": "$COMPANY_NAME",
    "websiteUrl": "https://yourwebsite.com",
    "privacyUrl": "https://yourwebsite.com/privacy",
    "termsOfUseUrl": "https://yourwebsite.com/terms"
  },
  "icons": {
    "color": "color.png",
    "outline": "outline.png"
  },
  "name": {
    "short": "$BOT_NAME",
    "full": "$BOT_NAME"
  },
  "description": {
    "short": "AI-powered chatbot for Teams",
    "full": "An intelligent chatbot powered by Azure OpenAI for Microsoft Teams"
  },
  "accentColor": "#0078D4",
  "bots": [
    {
      "botId": "$BOT_ID",
      "scopes": ["personal", "team", "groupchat"],
      "supportsFiles": false,
      "isNotificationOnly": false
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": ["$APP_NAME.azurewebsites.net"]
}
EOF

# Create simple icons using base64 encoded minimal PNG data
echo "🎨 Creating minimal icons..."

# Create a simple color icon (blue square with "AI")
python3 -c "
import base64
# Minimal PNG data for a 192x192 blue square
png_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA+1zBAIAAAAASUVORK5CYII=')
with open('teams-app/color.png', 'wb') as f:
    f.write(png_data)
" 2>/dev/null || echo "⚠️  Could not create color icon with Python"

# Create outline icon
python3 -c "
import base64
# Minimal PNG data for a 32x32 transparent square
png_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA+1zBAIAAAAASUVORK5CYII=')
with open('teams-app/outline.png', 'wb') as f:
    f.write(png_data)
" 2>/dev/null || echo "⚠️  Could not create outline icon with Python"

# Create quick installation guide
cat > teams-app/README.md <<EOF
# Quick Teams Installation

## Upload to Teams
1. Go to Microsoft Teams
2. Click "Apps" in the left sidebar
3. Click "Manage your apps" (bottom left)
4. Click "Upload an app" → "Upload a custom app"
5. Select the manifest.json file from this folder

## Test the Bot
- Search for "$BOT_NAME" in Teams
- Start a conversation
- Try: /help, /clear, /summary

## Bot Details
- Bot ID: $BOT_ID
- Bot URL: $APP_URL
- Health Check: $APP_URL/health

Note: Replace the PNG icon files with proper 192x192 (color) and 32x32 (outline) icons for production use.
EOF

echo ""
echo "✅ Teams manifest created successfully!"
echo ""
echo "📁 Files created in ./teams-app/:"
echo "   - manifest.json (Teams app manifest)"
echo "   - color.png (placeholder icon)"
echo "   - outline.png (placeholder icon)"
echo "   - README.md (installation instructions)"
echo ""
echo "🚀 Next steps:"
echo "   1. Upload manifest.json to Microsoft Teams"
echo "   2. Test the bot by searching for '$BOT_NAME'"
echo "   3. Replace icon files for production use"
echo ""
echo "🔗 Quick test: curl $APP_URL/health"
