# Teams Manifest Generation Scripts

This directory contains scripts to automatically generate Microsoft Teams app manifests for deploying your Azure Teams AI Chatbot to Microsoft Teams.

## Scripts Overview

### 1. `generate-teams-manifest.sh` (Full Featured)
A comprehensive script with extensive customization options for production deployments.

**Features:**
- Automatic Azure resource discovery
- Extensive customization options
- Icon generation (with ImageMagick support)
- Complete app package creation
- Detailed installation instructions
- Environment-specific configurations

**Usage:**
```bash
# Basic usage - discovers all settings from Azure
./deployment/scripts/generate-teams-manifest.sh -g my-resource-group

# Production deployment with custom settings
./deployment/scripts/generate-teams-manifest.sh \
  -g my-chatbot-prod-rg \
  -e prod \
  -c "Contoso Corporation" \
  -w "https://contoso.com" \
  -n "Contoso AI Assistant" \
  -s "Enterprise AI chatbot" \
  -f "Advanced AI assistant for enterprise Teams collaboration"

# Quick deployment with known bot ID and URL
./deployment/scripts/generate-teams-manifest.sh \
  -g my-resource-group \
  -b "12345678-1234-1234-1234-123456789012" \
  -u "https://my-app.azurewebsites.net"
```

**Options:**
- `-g, --resource-group NAME` - Azure resource group name (required)
- `-e, --environment ENV` - Environment (dev/staging/prod) [default: dev]
- `-o, --output-dir DIR` - Output directory [default: ./teams-app]
- `-b, --bot-id ID` - Bot App ID (auto-discovered if not provided)
- `-u, --app-url URL` - App Service URL (auto-discovered if not provided)
- `-c, --company-name NAME` - Company name [default: Your Company]
- `-w, --website-url URL` - Company website URL
- `-p, --privacy-url URL` - Privacy policy URL
- `-t, --terms-url URL` - Terms of use URL
- `-n, --bot-name NAME` - Bot display name [default: AI Chatbot]
- `-s, --short-desc TEXT` - Short description
- `-f, --full-desc TEXT` - Full description
- `--package-name NAME` - Package name (auto-generated if not provided)
- `--version VERSION` - App version [default: 1.0.0]

### 2. `quick-teams-manifest.sh` (Simple & Fast)
A streamlined script for quick development and testing deployments.

**Features:**
- Minimal configuration required
- Fast execution
- Auto-discovery of Azure resources
- Basic icon generation
- Simple installation guide

**Usage:**
```bash
# Quick generation with just resource group
./deployment/scripts/quick-teams-manifest.sh my-resource-group

# With custom bot name and company
./deployment/scripts/quick-teams-manifest.sh my-resource-group "My AI Bot" "My Company"
```

## Prerequisites

### Required
- **Azure CLI** - Installed and authenticated (`az login`)
- **jq** - JSON processor (for parsing Azure outputs)
- **bash** - Shell environment
- **Deployed Azure resources** - Bot service and app service must exist

### Optional (for enhanced features)
- **ImageMagick** - For automatic icon generation from SVG
- **zip** - For creating app packages
- **Python 3** - For basic icon creation fallback

### Installation of Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install azure-cli jq imagemagick zip python3
```

**macOS (with Homebrew):**
```bash
brew install azure-cli jq imagemagick zip python3
```

**Windows (with Chocolatey):**
```bash
choco install azure-cli jq imagemagick zip python3
```

## Generated Files

Both scripts create a `teams-app` directory (or custom output directory) containing:

### Core Files
- **`manifest.json`** - Teams app manifest file
- **`color.png`** - 192x192 color icon (placeholder or generated)
- **`outline.png`** - 32x32 outline icon (placeholder or generated)

### Additional Files (full script)
- **`[BotName]-[Environment]-[Version].zip`** - Complete app package
- **`INSTALLATION.md`** - Detailed installation and configuration guide
- **`*.svg`** - Intermediate SVG files (if ImageMagick not available)

### Additional Files (quick script)
- **`README.md`** - Simple installation instructions

## Installation in Microsoft Teams

### Method 1: Upload Manifest File
1. Open Microsoft Teams
2. Go to **Apps** in the left sidebar
3. Click **Manage your apps** (bottom left)
4. Click **Upload an app** → **Upload a custom app**
5. Select the `manifest.json` file
6. Click **Add** to install

### Method 2: Upload App Package (if zip created)
1. Follow steps 1-4 above
2. Select the `.zip` file instead of `manifest.json`
3. Teams will automatically extract and install

### Method 3: Teams Admin Center (Organization-wide)
1. Go to [Teams Admin Center](https://admin.teams.microsoft.com/)
2. Navigate to **Teams apps** → **Manage apps**
3. Click **Upload** and select the app package
4. Review and approve for organization
5. Users can install from the Teams app store

## Customization

### Icons
Replace the generated placeholder icons with your custom icons:
- **Color icon**: 192x192 pixels, PNG format, full color
- **Outline icon**: 32x32 pixels, PNG format, monochrome/transparent

### Manifest Properties
Edit the generated `manifest.json` to customize:
- App name and description
- Supported scopes (personal, team, groupchat)
- Permissions
- Valid domains
- Developer information

### Bot Capabilities
The manifest includes these default bot capabilities:
- Personal conversations
- Team conversations
- Group chat conversations
- Text message support
- Identity permissions

## Troubleshooting

### Common Issues

**1. "Bot ID not found"**
- Ensure Azure Bot Service is deployed
- Check resource group name
- Verify Azure CLI authentication
- Try providing Bot ID manually with `-b` option

**2. "App Service URL not found"**
- Ensure Azure App Service is deployed and running
- Check resource group name
- Try providing URL manually with `-u` option

**3. "Azure CLI authentication failed"**
- Run `az login` to authenticate
- Verify subscription access with `az account show`
- Check resource group permissions

**4. "Icon generation failed"**
- Install ImageMagick: `sudo apt install imagemagick` (Ubuntu)
- Or manually create PNG icons and replace the generated ones

**5. "Teams app installation failed"**
- Verify Bot ID matches Azure Bot Service registration
- Check that App Service is accessible at the specified URL
- Ensure the manifest.json syntax is valid
- Verify bot messaging endpoint: `https://your-app.azurewebsites.net/api/messages`

### Validation Commands

**Test bot health:**
```bash
curl https://your-app.azurewebsites.net/health
```

**Test bot endpoint (should return 405 Method Not Allowed):**
```bash
curl -X GET https://your-app.azurewebsites.net/api/messages
```

**Validate Azure resources:**
```bash
# Check bot service
az bot show -g your-resource-group -n your-bot-name

# Check app service
az webapp show -g your-resource-group -n your-app-name

# Check deployment outputs
az deployment group show -g your-resource-group -n your-deployment-name --query properties.outputs
```

**Validate manifest JSON:**
```bash
# Check JSON syntax
cat teams-app/manifest.json | jq .

# Validate specific fields
cat teams-app/manifest.json | jq '.bots[0].botId'
```

## Security Considerations

- Bot ID is public information (included in manifest)
- App Service URL is public (Teams needs to reach the bot)
- Use HTTPS for all URLs
- Implement proper authentication in your bot service
- Store sensitive secrets in Azure Key Vault
- Follow Microsoft Teams security guidelines

## Next Steps

After generating and installing the Teams manifest:

1. **Test the bot** - Start a conversation and verify responses
2. **Monitor logs** - Check Azure App Service logs for any issues
3. **Customize icons** - Replace placeholder icons with branded ones
4. **Update manifest** - Modify descriptions, permissions as needed
5. **Deploy to organization** - Use Teams Admin Center for wide deployment

## Support

For issues with these scripts:
1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Review the generated `INSTALLATION.md` or `README.md` files
4. Check Azure resource deployment status
5. Consult the main project documentation

For Teams-specific issues:
- [Microsoft Teams developer documentation](https://docs.microsoft.com/en-us/microsoftteams/platform/)
- [Teams app manifest reference](https://docs.microsoft.com/en-us/microsoftteams/platform/resources/schema/manifest-schema)
- [Bot Framework documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
