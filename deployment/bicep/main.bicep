// Main Bicep template for Azure Teams AI Chatbot infrastructure
// This template deploys all required Azure resources

targetScope = 'resourceGroup'

@description('Name of the application')
param appName string = 'teamschatbot'

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('SKU for App Service Plan')
@allowed(['F1', 'B1', 'B2', 'S1', 'S2', 'P1v2', 'P2v2'])
param appServicePlanSku string = 'B1'

@description('Azure OpenAI region')
param openAiLocation string = 'eastus'

@description('OpenAI SKU')
@allowed(['S0'])
param openAiSku string = 'S0'

@description('GPT model deployment name')
param gptDeploymentName string = 'gpt-35-turbo'

@description('GPT model name')
param gptModelName string = 'gpt-35-turbo'

@description('GPT model version')
param gptModelVersion string = '0613'

@description('GPT deployment capacity')
param gptDeploymentCapacity int = 30

@description('Enable Application Insights')
param enableAppInsights bool = true

@description('Enable Azure SQL Database')
param enableSqlDatabase bool = false

@description('SQL Admin username')
param sqlAdminUsername string = 'chatbotadmin'

@description('SQL Admin password')
@secure()
param sqlAdminPassword string = ''

// Variables
var resourcePrefix = '${appName}-${environment}'
var keyVaultName = '${take(appName, 8)}-${take(environment, 3)}-kv-${take(uniqueString(resourceGroup().id), 6)}'
var appServicePlanName = '${resourcePrefix}-plan'
var appServiceName = '${resourcePrefix}-app'
var openAiName = '${resourcePrefix}-openai'
var botName = '${resourcePrefix}-bot'
var appInsightsName = '${resourcePrefix}-insights'
var sqlServerName = '${resourcePrefix}-sql'
var sqlDatabaseName = '${resourcePrefix}-db'

// Tags
var commonTags = {
  Application: appName
  Environment: environment
  ManagedBy: 'Bicep'
}

// Key Vault for storing secrets
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: commonTags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Azure OpenAI Service
resource openAiService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: openAiLocation
  tags: commonTags
  kind: 'OpenAI'
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
  sku: {
    name: openAiSku
  }
}

// GPT Model Deployment
resource gptDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAiService
  name: gptDeploymentName
  properties: {
    model: {
      format: 'OpenAI'
      name: gptModelName
      version: gptModelVersion
    }
  }
  sku: {
    name: 'Standard'
    capacity: gptDeploymentCapacity
  }
}

// Application Insights (optional)
resource appInsights 'Microsoft.Insights/components@2020-02-02' = if (enableAppInsights) {
  name: appInsightsName
  location: location
  tags: commonTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
  }
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: commonTags
  sku: {
    name: appServicePlanSku
  }
  properties: {
    reserved: true // Required for Linux
  }
  kind: 'linux'
}

// App Service
resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceName
  location: location
  tags: commonTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: appServicePlanSku != 'F1'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAiService.properties.endpoint
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
          value: gptDeploymentName
        }
        {
          name: 'AZURE_KEY_VAULT_URL'
          value: keyVault.properties.vaultUri
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
      ]
    }
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
  }
}

// Update App Service configuration with Bot App ID after Bot Service is created
resource appServiceConfigUpdate 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: appService
  name: 'appsettings'
  properties: {
    AZURE_OPENAI_ENDPOINT: openAiService.properties.endpoint
    AZURE_OPENAI_DEPLOYMENT_NAME: gptDeploymentName
    AZURE_OPENAI_API_VERSION: '2024-02-15-preview'
    AZURE_KEY_VAULT_URL: keyVault.properties.vaultUri
    MICROSOFT_APP_ID: botService.properties.msaAppId
    SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
    ENABLE_ORYX_BUILD: 'true'
  }
}

// SQL Server (optional)
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = if (enableSqlDatabase && !empty(sqlAdminPassword)) {
  name: sqlServerName
  location: location
  tags: commonTags
  properties: {
    administratorLogin: sqlAdminUsername
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    publicNetworkAccess: 'Enabled'
  }
}

// SQL Database (optional)
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = if (enableSqlDatabase && !empty(sqlAdminPassword)) {
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  tags: commonTags
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648 // 2GB
  }
}

// SQL Firewall rule to allow Azure services
resource sqlFirewallRule 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = if (enableSqlDatabase && !empty(sqlAdminPassword)) {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Azure Bot Service
resource botService 'Microsoft.BotService/botServices@2022-09-15' = {
  name: botName
  location: 'global'
  tags: commonTags
  sku: {
    name: 'F0'
  }
  kind: 'azurebot'
  properties: {
    displayName: '${appName} ${environment} Bot'
    endpoint: 'https://${appService.properties.defaultHostName}/api/messages'
    msaAppId: appService.identity.principalId
    msaAppType: 'SystemAssignedMSI'
    msaAppMSIResourceId: appService.id
    msaAppTenantId: subscription().tenantId
  }
}

// Teams channel for the bot
resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = {
  parent: botService
  name: 'MsTeamsChannel'
  properties: {
    channelName: 'MsTeamsChannel'
    properties: {
      enableCalling: false
      isEnabled: true
    }
  }
}

// Key Vault role assignment for App Service
resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, appService.id, 'Key Vault Secrets User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Cognitive Services role assignment for App Service
resource cognitiveServicesRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: openAiService
  name: guid(openAiService.id, appService.id, 'Cognitive Services OpenAI User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Cognitive Services OpenAI User
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Store OpenAI API key in Key Vault
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-API-KEY'
  properties: {
    value: openAiService.listKeys().key1
  }
  dependsOn: [
    keyVaultRoleAssignment
  ]
}

// Store Bot Framework App ID in Key Vault (for consistency)
resource microsoftAppIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'MICROSOFT-APP-ID'
  properties: {
    value: botService.properties.msaAppId
  }
  dependsOn: [
    keyVaultRoleAssignment
  ]
}

// Note: MICROSOFT_APP_PASSWORD is not needed for Managed Identity authentication
// The bot is configured with msaAppType: 'SystemAssignedMSI' which uses the App Service's managed identity

// Store SQL connection string in Key Vault (if SQL is enabled)
resource sqlConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (enableSqlDatabase && !empty(sqlAdminPassword)) {
  parent: keyVault
  name: 'DATABASE-URL'
  properties: {
    value: 'mssql+pyodbc://${sqlAdminUsername}:${sqlAdminPassword}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${sqlDatabaseName}?driver=ODBC+Driver+18+for+SQL+Server'
  }
  dependsOn: [
    keyVaultRoleAssignment
  ]
}

// Store Application Insights connection string in Key Vault (if enabled)
resource appInsightsConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (enableAppInsights) {
  parent: keyVault
  name: 'APPLICATIONINSIGHTS-CONNECTION-STRING'
  properties: {
    value: appInsights.properties.ConnectionString
  }
  dependsOn: [
    keyVaultRoleAssignment
  ]
}

// Outputs
output resourceGroupName string = resourceGroup().name
output appServiceName string = appService.name
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output keyVaultName string = keyVault.name
output keyVaultUrl string = keyVault.properties.vaultUri
output openAiEndpoint string = openAiService.properties.endpoint
output botName string = botService.name
output botId string = botService.properties.msaAppId
output appInsightsConnectionString string = enableAppInsights ? appInsights.properties.ConnectionString : ''
output sqlServerName string = enableSqlDatabase ? sqlServer.name : ''
output sqlDatabaseName string = enableSqlDatabase ? sqlDatabase.name : ''
