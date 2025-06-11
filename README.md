# Azure Teams AI Chatbot

A production-ready Azure Teams chatbot with Azure OpenAI integration, built using the Microsoft Bot Framework and deployed on Azure App Service.

## Features

- **Azure OpenAI Integration**: GPT-3.5-turbo and GPT-4 support with conversation memory
- **Microsoft Teams**: Native Teams integration with rich cards and file attachments
- **Web Interface**: REST API and simple web interface for testing
- **Azure Services**: Key Vault for secrets, App Service for hosting, Bot Services for Teams
- **Production Ready**: Comprehensive logging, monitoring, error handling, and deployment automation

## Quick Start

### Prerequisites

- Python 3.9+
- Azure subscription
- Teams admin access for bot registration

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/wesback/aichatbot.git
cd aichatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables (see Configuration section)

4. Run the application:
```bash
python app.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo

# Bot Framework Configuration
MICROSOFT_APP_ID=your-bot-app-id
MICROSOFT_APP_PASSWORD=your-bot-app-password

# Azure Key Vault (Optional)
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# Application Configuration
FLASK_ENV=development
LOG_LEVEL=INFO
```

### Azure Key Vault Integration

For production deployments, secrets are automatically retrieved from Azure Key Vault using managed identity.

## Architecture

```
├── src/
│   ├── bot/           # Teams Bot Framework integration
│   ├── services/      # Azure OpenAI and external services
│   ├── models/        # Data models and DTOs
│   ├── config/        # Configuration management
│   └── utils/         # Utility functions and helpers
├── deployment/        # Infrastructure as Code
├── tests/            # Unit and integration tests
└── docs/             # Additional documentation
```

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /api/messages` - Bot Framework messaging endpoint
- `POST /api/chat` - Direct chat API for web interface
- `GET /` - Simple web interface for testing

## Deployment

### Azure Resources

The solution requires the following Azure resources:

- Azure OpenAI Service
- Azure App Service
- Azure Bot Services
- Azure Key Vault
- Application Insights

### Automated Deployment

Use the provided Bicep templates and scripts:

```bash
# Deploy infrastructure
./deployment/scripts/deploy-infrastructure.sh

# Deploy application
./deployment/scripts/deploy-application.sh
```

### Manual Deployment

1. Create Azure resources using the Azure portal or CLI
2. Configure Key Vault with required secrets
3. Deploy the application to App Service
4. Register the bot with Azure Bot Services
5. Install the Teams app using the manifest

## Teams Integration

### Features

- Direct messages and channel mentions
- Rich adaptive cards
- File attachment handling
- Conversation context management
- Teams-specific event handling

### Installation

1. Deploy the bot to Azure
2. Register with Azure Bot Services
3. Configure Teams channel
4. Install the Teams app using the provided manifest

## Monitoring and Logging

- Application Insights integration for telemetry
- Structured logging throughout the application
- Performance monitoring and alerting
- Error tracking and notification

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
flake8 src/ tests/
```

### Local Bot Testing

Use the Bot Framework Emulator for local testing:

1. Download the Bot Framework Emulator
2. Start the local application
3. Connect to `http://localhost:3978/api/messages`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:

1. Check the [troubleshooting guide](docs/troubleshooting.md)
2. Review the [API documentation](docs/api.md)
3. Open an issue on GitHub

## Security

- All secrets stored in Azure Key Vault
- Managed identity for Azure service authentication
- HTTPS enforcement
- Bot Framework authentication validation