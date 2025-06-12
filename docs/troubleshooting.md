# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Azure Teams AI Chatbot.

## Common Issues

### 1. Bot Not Responding in Teams

**Symptoms:**
- Messages sent to the bot in Teams don't receive responses
- Bot appears offline or unavailable

**Possible Causes:**
- Bot Framework configuration issues
- Azure App Service not running
- Incorrect messaging endpoint
- Authentication problems

**Solutions:**

1. **Check App Service Status:**
   ```bash
   az webapp show --resource-group your-rg --name your-app --query state
   ```

2. **Verify Messaging Endpoint:**
   - Go to Azure Portal → Bot Services → your bot
   - Check that messaging endpoint is: `https://your-app.azurewebsites.net/api/messages`
   - Ensure the URL is accessible and returns 405 (Method Not Allowed) for GET requests

3. **Test Health Endpoint:**
   ```bash
   curl https://your-app.azurewebsites.net/health
   ```

4. **Check Application Logs:**
   ```bash
   az webapp log tail --resource-group your-rg --name your-app
   ```

5. **Verify Bot Framework Authentication:**
   - Ensure `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD` are correctly set
   - Check Key Vault secrets if using Key Vault
   - For managed identity issues, see [Bot Framework Authentication Errors](#bot-framework-authentication-errors)

---

### 2. Bot Framework Authentication Errors

**Symptoms:**
- `Bot Framework error: 'access_token'` in logs
- `KeyError: 'access_token'` exceptions
- Bot failing to process incoming messages

**Possible Causes:**
- Managed identity configuration issues
- Missing or invalid app credentials
- MSAL authentication failures

**Solutions:**

1. **For Managed Identity Mode:**
   - The current implementation uses development mode to bypass authentication
   - This is a temporary workaround until proper managed identity credentials are implemented
   - Verify that your App Service has managed identity enabled:
     ```bash
     az webapp identity show --resource-group your-rg --name your-app
     ```

2. **For App ID/Password Mode:**
   - Ensure both `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD` are set
   - Verify credentials are valid by testing them:
     ```bash
     # Test in Azure CLI
     az login --service-principal -u YOUR_APP_ID -p YOUR_APP_PASSWORD --tenant YOUR_TENANT
     ```

3. **Configuration Check:**
   - Review the Bot Framework configuration in your logs
   - Look for messages like "Using Bot Framework development mode" or "Managed Identity mode"
   - Ensure the configuration matches your deployment scenario

4. **Debugging Steps:**
   - Check the health endpoint: `/health`
   - Look for "Authentication configuration error" in API responses
   - Monitor Application Insights for authentication failures

**Note:** The current fix automatically handles the 'access_token' error gracefully, but proper managed identity implementation is recommended for production deployments.

---

### 3. Azure OpenAI API Errors

**Symptoms:**
- "I'm having trouble connecting to my AI service" messages
- 401 Unauthorized errors in logs
- Timeout errors

**Possible Causes:**
- Invalid API key
- Incorrect endpoint URL
- Rate limiting
- Model deployment not available

**Solutions:**

1. **Verify OpenAI Configuration:**
   ```bash
   # Check environment variables
   az webapp config appsettings list --resource-group your-rg --name your-app
   ```

2. **Test API Key:**
   ```bash
   curl -H "api-key: YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        "https://your-openai.openai.azure.com/openai/deployments?api-version=2023-05-15"
   ```

3. **Check Model Deployment:**
   - Verify the deployment name matches your configuration
   - Ensure the model is deployed and running

4. **Monitor Rate Limits:**
   - Check Azure OpenAI metrics in Azure Portal
   - Consider upgrading to higher tier if needed

---

### 4. Key Vault Access Issues

**Symptoms:**
- "Failed to get secret from Key Vault" in logs
- Configuration values not loading from Key Vault

**Possible Causes:**
- Managed identity not configured
- Missing Key Vault access policies
- Incorrect Key Vault URL

**Solutions:**

1. **Verify Managed Identity:**
   ```bash
   az webapp identity show --resource-group your-rg --name your-app
   ```

2. **Check Key Vault Access Policy:**
   ```bash
   az keyvault show --name your-keyvault --resource-group your-rg
   ```

3. **Test Key Vault Access:**
   ```bash
   # From within the App Service (using Kudu console)
   curl -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net"
   ```

4. **Grant Access:**
   ```bash
   # Get App Service principal ID
   PRINCIPAL_ID=$(az webapp identity show --resource-group your-rg --name your-app --query principalId -o tsv)
   
   # Grant Key Vault access
   az keyvault set-policy --name your-keyvault --object-id $PRINCIPAL_ID --secret-permissions get list
   ```

---

### 5. Teams App Installation Issues

**Symptoms:**
- Unable to install Teams app
- "App not found" errors
- Permissions denied

**Solutions:**

1. **Check Teams App Manifest:**
   - Verify bot ID matches your Azure Bot registration
   - Ensure required permissions are specified
   - Validate manifest.json syntax

2. **Upload App to Teams:**
   - Go to Teams Admin Center
   - Upload the app package (.zip file with manifest)
   - Enable the app for your organization

3. **Verify Bot Registration:**
   - Check Azure Bot Services registration
   - Ensure Teams channel is enabled
   - Verify messaging endpoint

---

### 6. Performance Issues

**Symptoms:**
- Slow response times
- Timeouts
- High resource usage

**Solutions:**

1. **Scale App Service:**
   ```bash
   az appservice plan update --resource-group your-rg --name your-plan --sku B2
   ```

2. **Monitor Application Insights:**
   - Check response times and dependencies
   - Identify bottlenecks
   - Set up alerts for performance degradation

3. **Optimize Configuration:**
   - Reduce conversation history length
   - Lower OpenAI token limits
   - Implement caching for frequent requests

---

### 7. Deployment Issues

**Symptoms:**
- Deployment failures
- App not starting after deployment
- Missing dependencies

**Solutions:**

1. **Check Deployment Status:**
   ```bash
   az webapp deployment list-publishing-credentials --resource-group your-rg --name your-app
   ```

2. **Verify Python Requirements:**
   - Ensure all dependencies are in requirements.txt
   - Check for version conflicts
   - Test locally before deploying

3. **Enable Detailed Logging:**
   ```bash
   az webapp log config --resource-group your-rg --name your-app --application-logging true --level information
   ```

4. **Use Deployment Center:**
   - Set up continuous deployment from GitHub
   - Monitor build and deployment logs

---

## Diagnostic Commands

### Health Check Script

```bash
#!/bin/bash
# health-check.sh - Comprehensive health check script

APP_URL="https://your-app.azurewebsites.net"
RG_NAME="your-resource-group"
APP_NAME="your-app-name"

echo "=== Azure Teams AI Chatbot Health Check ==="

# 1. Check App Service status
echo "1. Checking App Service status..."
az webapp show --resource-group $RG_NAME --name $APP_NAME --query state

# 2. Test health endpoint
echo "2. Testing health endpoint..."
curl -s $APP_URL/health | jq .

# 3. Test chat endpoint
echo "3. Testing chat endpoint..."
curl -s -X POST $APP_URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test","conversation_id":"health-check"}' | jq .

# 4. Check recent logs
echo "4. Checking recent logs..."
az webapp log tail --resource-group $RG_NAME --name $APP_NAME --lines 10

echo "=== Health check complete ==="
```

### Configuration Validator

```python
#!/usr/bin/env python3
# validate-config.py - Validate configuration

import os
import requests
from src.config import Config

def validate_config():
    """Validate application configuration."""
    config = Config()
    errors = []
    warnings = []
    
    # Check required OpenAI settings
    if not config.azure_openai_endpoint:
        errors.append("Azure OpenAI endpoint not configured")
    
    if not config.azure_openai_api_key:
        errors.append("Azure OpenAI API key not configured")
    
    # Check Bot Framework settings
    if not config.microsoft_app_id:
        warnings.append("Microsoft App ID not configured")
    
    if not config.microsoft_app_password:
        warnings.append("Microsoft App Password not configured")
    
    # Test OpenAI connectivity
    if config.azure_openai_endpoint and config.azure_openai_api_key:
        try:
            headers = {
                'api-key': config.azure_openai_api_key,
                'Content-Type': 'application/json'
            }
            url = f"{config.azure_openai_endpoint}/openai/deployments?api-version=2023-05-15"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                errors.append(f"OpenAI API test failed: {response.status_code}")
        except Exception as e:
            errors.append(f"OpenAI connectivity test failed: {e}")
    
    # Print results
    print("=== Configuration Validation ===")
    
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration is valid")
    
    return len(errors) == 0

if __name__ == "__main__":
    validate_config()
```

## Getting Help

### Log Analysis

**Key log patterns to look for:**

- `Error calling Azure OpenAI` - OpenAI service issues
- `Failed to get secret` - Key Vault access problems
- `Bot Framework error` - Teams integration issues
- `Rate limit reached` - API rate limiting

### Application Insights Queries

If you have Application Insights enabled, use these KQL queries:

```kql
// Find recent errors
traces
| where timestamp > ago(1h)
| where severityLevel >= 3
| order by timestamp desc

// Monitor response times
requests
| where timestamp > ago(1h)
| summarize avg(duration) by bin(timestamp, 5m)
| order by timestamp desc

// Track conversation metrics
customEvents
| where name == "ConversationMessage"
| summarize count() by bin(timestamp, 1h)
```

### Support Channels

1. **GitHub Issues:** Report bugs and feature requests
2. **Azure Support:** For Azure service-specific issues
3. **Microsoft Bot Framework:** For Teams integration issues
4. **OpenAI Support:** For AI model-related questions

### Self-Service Tools

1. **Azure Resource Health:** Check Azure service status
2. **Bot Framework Emulator:** Test bot locally
3. **Application Insights Live Metrics:** Real-time monitoring
4. **Azure Monitor:** Set up alerts and dashboards