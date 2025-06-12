"""Configuration management for the Azure Teams chatbot."""
import os
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

# Load environment variables from .env files in priority order
def load_environment_files():
    """Load environment variables from .env files in priority order."""
    env_files = [
        '.env',           # Primary .env file (user-created)
        '.env.local',     # Local development overrides
        '.env.dev',       # Development environment
        '.env.development'  # Alternative development name
    ]
    
    loaded_files = []
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            loaded_files.append(env_file)
    
    # Use basic logging since the logger isn't set up yet
    if not loaded_files:
        print(f"WARNING: No .env files found. Checked: {', '.join(env_files)}")
        print("WARNING: Please create a .env file with your configuration. See .env.example for reference.")
    else:
        print(f"INFO: Successfully loaded environment from: {', '.join(loaded_files)}")

load_environment_files()

logger = logging.getLogger(__name__)


class Config:
    """Application configuration class with Azure Key Vault integration."""
    
    def __init__(self):
        """Initialize configuration with environment variables and Key Vault."""
        self._key_vault_client = None
        self._init_key_vault()
        
    def _init_key_vault(self):
        """Initialize Azure Key Vault client if URL is provided."""
        key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')
        if key_vault_url:
            try:
                credential = DefaultAzureCredential()
                self._key_vault_client = SecretClient(
                    vault_url=key_vault_url,
                    credential=credential
                )
                logger.info("Azure Key Vault client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Key Vault client: {e}")
                self._key_vault_client = None
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value, first trying Key Vault, then environment variables.
        
        Args:
            key: The secret key name
            default: Default value if secret is not found
            
        Returns:
            The secret value or default
        """
        # Try Key Vault first
        if self._key_vault_client:
            try:
                secret = self._key_vault_client.get_secret(key)
                return secret.value
            except Exception as e:
                logger.debug(f"Failed to get secret '{key}' from Key Vault: {e}")
        
        # Fall back to environment variables
        value = os.getenv(key, default)
        
        # Check for placeholder values that need to be replaced
        if value and self._is_placeholder_value(value):
            logger.warning(f"Configuration '{key}' contains placeholder value. Please update your .env file with actual credentials.")
            return default  # Treat placeholder as missing
        
        return value
    
    def _is_placeholder_value(self, value: str) -> bool:
        """Check if a value is a placeholder that needs to be replaced."""
        if not value:
            return False
        
        placeholder_indicators = [
            'your-',
            'replace-',
            'example-',
            'placeholder',
            'TODO',
            'CHANGEME',
            'your_',
            'REPLACE_'
        ]
        
        return any(indicator in value.lower() for indicator in placeholder_indicators)
    
    def validate_critical_config(self) -> dict:
        """
        Validate critical configuration and return status information.
        
        Returns:
            Dictionary with validation results and helpful messages
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "missing_configs": []
        }
        
        # Critical OpenAI configuration
        if not self.azure_openai_endpoint:
            validation_results["errors"].append("AZURE_OPENAI_ENDPOINT is not configured")
            validation_results["missing_configs"].append("AZURE_OPENAI_ENDPOINT")
            validation_results["valid"] = False
            
        if not self.azure_openai_api_key:
            validation_results["errors"].append("AZURE_OPENAI_API_KEY is not configured")
            validation_results["missing_configs"].append("AZURE_OPENAI_API_KEY")
            validation_results["valid"] = False
        
        # Bot Framework configuration (optional for web-only usage)
        if not self.microsoft_app_id or not self.microsoft_app_password:
            validation_results["warnings"].append(
                "Bot Framework credentials (MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD) are not configured. "
                "Teams integration will not work, but the web interface will still function."
            )
        
        # Add helpful setup message if there are missing configs
        if validation_results["missing_configs"]:
            validation_results["setup_help"] = (
                f"To fix these issues:\n"
                f"1. Copy .env.example to .env\n"
                f"2. Replace placeholder values with your actual credentials\n"
                f"3. Missing: {', '.join(validation_results['missing_configs'])}\n"
                f"4. See README.md for detailed setup instructions"
            )
        
        return validation_results
    
    # Azure OpenAI Configuration
    @property
    def azure_openai_endpoint(self) -> str:
        """Azure OpenAI service endpoint."""
        return self.get_secret('AZURE_OPENAI_ENDPOINT', '')
    
    @property
    def azure_openai_api_key(self) -> str:
        """Azure OpenAI API key."""
        return self.get_secret('AZURE_OPENAI_API_KEY', '')
    
    @property
    def azure_openai_api_version(self) -> str:
        """Azure OpenAI API version."""
        return self.get_secret('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
    
    @property
    def azure_openai_deployment_name(self) -> str:
        """Azure OpenAI deployment name."""
        return self.get_secret('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-35-turbo')
    
    # Bot Framework Configuration
    @property
    def microsoft_app_id(self) -> str:
        """Microsoft Bot Framework App ID."""
        return self.get_secret('MICROSOFT_APP_ID', '')
    
    @property
    def microsoft_app_password(self) -> str:
        """Microsoft Bot Framework App Password."""
        return self.get_secret('MICROSOFT_APP_PASSWORD', '')
    
    # Application Configuration
    @property
    def flask_env(self) -> str:
        """Flask environment."""
        return self.get_secret('FLASK_ENV', 'production')
    
    @property
    def log_level(self) -> str:
        """Logging level."""
        return self.get_secret('LOG_LEVEL', 'INFO')
    
    @property
    def port(self) -> int:
        """Application port."""
        return int(self.get_secret('PORT', '3978'))
    
    # Database Configuration (Optional)
    @property
    def database_url(self) -> str:
        """Database connection URL."""
        return self.get_secret('DATABASE_URL', 'sqlite:///chatbot.db')
    
    # Application Insights
    @property
    def appinsights_instrumentation_key(self) -> str:
        """Application Insights instrumentation key."""
        return self.get_secret('APPINSIGHTS_INSTRUMENTATION_KEY', '')
    
    @property
    def appinsights_connection_string(self) -> str:
        """Application Insights connection string."""
        return self.get_secret('APPLICATIONINSIGHTS_CONNECTION_STRING', '')
    
    # Conversation Configuration
    @property
    def max_conversation_history(self) -> int:
        """Maximum number of messages to keep in conversation history."""
        return int(self.get_secret('MAX_CONVERSATION_HISTORY', '10'))
    
    @property
    def openai_max_tokens(self) -> int:
        """Maximum tokens for OpenAI requests."""
        return int(self.get_secret('OPENAI_MAX_TOKENS', '1000'))
    
    @property
    def openai_temperature(self) -> float:
        """Temperature setting for OpenAI requests."""
        return float(self.get_secret('OPENAI_TEMPERATURE', '0.7'))


# Global configuration instance
config = Config()