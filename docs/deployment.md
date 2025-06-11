# Deployment Guide

This guide walks you through deploying the Azure Teams AI Chatbot to Azure.

## Prerequisites

- Azure subscription with appropriate permissions
- Azure CLI installed and logged in
- Python 3.9+ for local development
- Git for source control

## Quick Start (Automated)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wesback/aichatbot.git
   cd aichatbot
   ```

2. **Deploy infrastructure:**
   ```bash
   ./deployment/scripts/deploy-infrastructure.sh -g myapp-dev-rg -e dev
   ```

3. **Deploy application:**
   ```bash
   ./deployment/scripts/deploy-application.sh -g myapp-dev-rg -a myapp-dev-app
   ```

## Manual Deployment

### Step 1: Create Azure Resources

#### Option A: Using Bicep Templates (Recommended)

```bash
# Create resource group
az group create --name myapp-dev-rg --location eastus

# Deploy infrastructure
az deployment group create \
  --resource-group myapp-dev-rg \
  --template-file deployment/bicep/main.bicep \
  --parameters @deployment/bicep/parameters.dev.json \
  --parameters appName=myapp location=eastus
```

#### Option B: Using Azure Portal

1. **Create Resource Group**
2. **Create Azure OpenAI Service**
   - Deploy GPT-3.5-turbo or GPT-4 model
   - Note the endpoint and API key

3. **Create App Service**
   - Choose Python 3.11 runtime
   - Select appropriate pricing tier
   - Enable system-assigned managed identity

4. **Create Azure Key Vault**
   - Grant App Service access to secrets
   - Store OpenAI API key and other secrets

5. **Create Azure Bot Service**
   - Set messaging endpoint to your App Service URL + `/api/messages`
   - Enable Teams channel

### Step 2: Configure Secrets

Store sensitive configuration in Azure Key Vault:

```bash
# Store OpenAI API key
az keyvault secret set \
  --vault-name your-keyvault \
  --name "AZURE-OPENAI-API-KEY" \
  --value "your-openai-api-key"

# Store Bot Framework credentials
az keyvault secret set \
  --vault-name your-keyvault \
  --name "MICROSOFT-APP-ID" \
  --value "your-bot-app-id"

az keyvault secret set \
  --vault-name your-keyvault \
  --name "MICROSOFT-APP-PASSWORD" \
  --value "your-bot-app-password"
```

### Step 3: Deploy Application Code

#### Option A: Using Deployment Script

```bash
./deployment/scripts/deploy-application.sh \
  --resource-group myapp-dev-rg \
  --app-service myapp-dev-app \
  --environment dev
```

#### Option B: Using Azure CLI

```bash
# Prepare deployment package
zip -r deployment.zip . -x "*.git*" "*.pyc" "__pycache__/*" "venv/*"

# Deploy to App Service
az webapp deployment source config-zip \
  --resource-group myapp-dev-rg \
  --name myapp-dev-app \
  --src deployment.zip
```

#### Option C: Using GitHub Actions

1. **Set up secrets in GitHub repository:**
   - `AZURE_CREDENTIALS_DEV`: Service principal credentials
   - `AZURE_WEBAPP_NAME_DEV`: App Service name

2. **Push to repository:**
   The CI/CD pipeline will automatically deploy to development environment.

### Step 4: Configure Bot Framework

1. **Register Bot in Azure:**
   - Go to Azure Portal → Bot Services
   - Create new bot registration
   - Set messaging endpoint: `https://your-app.azurewebsites.net/api/messages`

2. **Get App Credentials:**
   - Copy App ID and generate App Password
   - Store in Key Vault or environment variables

3. **Enable Teams Channel:**
   - In Bot Services, go to Channels
   - Enable Microsoft Teams channel

### Step 5: Create Teams App

1. **Create App Manifest:**
   ```json
   {
     "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
     "manifestVersion": "1.16",
     "version": "1.0.0",
     "id": "your-bot-app-id",
     "packageName": "com.yourcompany.teamschatbot",
     "developer": {
       "name": "Your Company",
       "websiteUrl": "https://yourwebsite.com",
       "privacyUrl": "https://yourwebsite.com/privacy",
       "termsOfUseUrl": "https://yourwebsite.com/terms"
     },
     "icons": {
       "color": "color.png",
       "outline": "outline.png"
     },
     "name": {
       "short": "AI Chatbot",
       "full": "Azure Teams AI Chatbot"
     },
     "description": {
       "short": "AI-powered chatbot for Teams",
       "full": "An intelligent chatbot powered by Azure OpenAI for Microsoft Teams"
     },
     "accentColor": "#FFFFFF",
     "bots": [
       {
         "botId": "your-bot-app-id",
         "scopes": [
           "personal",
           "team",
           "groupchat"
         ],
         "supportsFiles": false,
         "isNotificationOnly": false
       }
     ],
     "permissions": [
       "identity",
       "messageTeamMembers"
     ],
     "validDomains": [
       "your-app.azurewebsites.net"
     ]
   }
   ```

2. **Create App Package:**
   - Create icons (color: 192x192px, outline: 32x32px)
   - Zip manifest.json and icons into app package

3. **Install in Teams:**
   - Upload app package to Teams
   - Install for your organization or specific teams

## Environment-Specific Configurations

### Development Environment

```bash
# Use minimal resources for cost savings
./deployment/scripts/deploy-infrastructure.sh \
  -g myapp-dev-rg \
  -e dev \
  -l eastus
```

Configuration:
- App Service: B1 (Basic)
- OpenAI: Standard tier
- SQL Database: Disabled
- Application Insights: Enabled

### Staging Environment

```bash
./deployment/scripts/deploy-infrastructure.sh \
  -g myapp-staging-rg \
  -e staging \
  -l eastus
```

Configuration:
- App Service: S1 (Standard)
- OpenAI: Standard tier
- SQL Database: Enabled (Basic)
- Application Insights: Enabled

### Production Environment

```bash
./deployment/scripts/deploy-infrastructure.sh \
  -g myapp-prod-rg \
  -e prod \
  -l eastus \
  -p "YourSecureSQLPassword123!"
```

Configuration:
- App Service: P1v2 (Premium)
- OpenAI: Standard tier (higher capacity)
- SQL Database: Enabled (Standard)
- Application Insights: Enabled
- Advanced monitoring and alerting

## Post-Deployment Configuration

### 1. Verify Deployment

```bash
# Test health endpoint
curl https://your-app.azurewebsites.net/health

# Test chat endpoint
curl -X POST https://your-app.azurewebsites.net/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","conversation_id":"test"}'
```

### 2. Configure Monitoring

1. **Set up Application Insights alerts:**
   - Response time > 5 seconds
   - Error rate > 5%
   - Availability < 95%

2. **Create Log Analytics queries:**
   - Monitor conversation volumes
   - Track error patterns
   - Analyze usage metrics

### 3. Security Configuration

1. **Enable HTTPS only:**
   ```bash
   az webapp update --resource-group myapp-prod-rg --name myapp-prod-app --https-only true
   ```

2. **Configure CORS (if needed):**
   ```bash
   az webapp cors add --resource-group myapp-prod-rg --name myapp-prod-app --allowed-origins https://teams.microsoft.com
   ```

3. **Set up IP restrictions (optional):**
   ```bash
   az webapp config access-restriction add \
     --resource-group myapp-prod-rg \
     --name myapp-prod-app \
     --ip-address 0.0.0.0/0 \
     --priority 100
   ```

## Continuous Deployment

### GitHub Actions Setup

1. **Create Service Principal:**
   ```bash
   az ad sp create-for-rbac \
     --name "myapp-github-actions" \
     --role contributor \
     --scopes /subscriptions/your-subscription-id/resourceGroups/myapp-dev-rg \
     --sdk-auth
   ```

2. **Add Secrets to GitHub:**
   - `AZURE_CREDENTIALS_DEV`: Service principal JSON
   - `AZURE_WEBAPP_NAME_DEV`: App Service name
   - Repeat for staging and production

3. **Configure Environments:**
   - Create GitHub environments: development, staging, production
   - Set up protection rules for production deployments

### Azure DevOps Setup

1. **Create Service Connection**
2. **Set up Build Pipeline**
3. **Create Release Pipeline**
4. **Configure Environment Gates**

## Scaling and Optimization

### Horizontal Scaling

```bash
# Scale out App Service
az appservice plan update \
  --resource-group myapp-prod-rg \
  --name myapp-prod-plan \
  --number-of-workers 3

# Enable auto-scaling
az monitor autoscale create \
  --resource-group myapp-prod-rg \
  --resource myapp-prod-app \
  --resource-type Microsoft.Web/sites \
  --name myapp-autoscale \
  --min-count 2 \
  --max-count 5 \
  --count 2
```

### Performance Optimization

1. **Enable Application Insights Profiler**
2. **Configure Redis Cache (optional)**
3. **Optimize conversation memory settings**
4. **Implement request caching**

## Maintenance

### Regular Tasks

1. **Monitor costs and usage**
2. **Review and rotate secrets**
3. **Update dependencies**
4. **Review logs and metrics**
5. **Test disaster recovery procedures**

### Backup and Recovery

```bash
# Backup App Service configuration
az webapp config backup create \
  --resource-group myapp-prod-rg \
  --webapp-name myapp-prod-app \
  --backup-name backup-$(date +%Y%m%d) \
  --storage-account-url "https://yourstorageaccount.blob.core.windows.net/backups"
```

## Troubleshooting

For common deployment issues, see the [Troubleshooting Guide](troubleshooting.md).

### Quick Diagnostics

```bash
# Check App Service logs
az webapp log tail --resource-group myapp-dev-rg --name myapp-dev-app

# Monitor resource usage
az monitor metrics list \
  --resource /subscriptions/your-sub/resourceGroups/myapp-dev-rg/providers/Microsoft.Web/sites/myapp-dev-app \
  --metric "CpuPercentage,MemoryPercentage"

# Test bot endpoint
curl -X POST https://your-app.azurewebsites.net/api/messages \
  -H "Authorization: Bearer fake-token" \
  -d '{}'
```