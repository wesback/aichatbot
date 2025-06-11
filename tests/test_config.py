"""Test configuration for the Azure Teams chatbot."""
import pytest
import os
from unittest.mock import patch, MagicMock
from src.config import Config


class TestConfig:
    """Test configuration management."""
    
    def test_config_initialization(self):
        """Test configuration initialization."""
        config = Config()
        assert config is not None
    
    @patch.dict(os.environ, {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_API_KEY': 'test-key',
        'MICROSOFT_APP_ID': 'test-app-id',
        'MICROSOFT_APP_PASSWORD': 'test-password'
    })
    def test_config_environment_variables(self):
        """Test configuration reads from environment variables."""
        config = Config()
        
        assert config.azure_openai_endpoint == 'https://test.openai.azure.com/'
        assert config.azure_openai_api_key == 'test-key'
        assert config.microsoft_app_id == 'test-app-id'
        assert config.microsoft_app_password == 'test-password'
    
    def test_config_defaults(self):
        """Test configuration default values."""
        config = Config()
        
        assert config.azure_openai_api_version == '2024-02-15-preview'
        assert config.azure_openai_deployment_name == 'gpt-35-turbo'
        assert config.port == 3978
        assert config.max_conversation_history == 10
        assert config.openai_max_tokens == 1000
        assert config.openai_temperature == 0.7
    
    @patch('src.config.SecretClient')
    @patch('src.config.DefaultAzureCredential')
    @patch.dict(os.environ, {'AZURE_KEY_VAULT_URL': 'https://test-kv.vault.azure.net/'})
    def test_key_vault_initialization(self, mock_credential, mock_secret_client):
        """Test Key Vault client initialization."""
        mock_credential.return_value = MagicMock()
        mock_secret_client.return_value = MagicMock()
        
        config = Config()
        
        mock_credential.assert_called_once()
        mock_secret_client.assert_called_once()
    
    @patch('src.config.SecretClient')
    @patch.dict(os.environ, {'AZURE_KEY_VAULT_URL': 'https://test-kv.vault.azure.net/'})
    def test_get_secret_from_key_vault(self, mock_secret_client):
        """Test getting secret from Key Vault."""
        # Setup mock
        mock_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.value = 'secret-value'
        mock_client.get_secret.return_value = mock_secret
        mock_secret_client.return_value = mock_client
        
        config = Config()
        result = config.get_secret('test-key')
        
        assert result == 'secret-value'
        mock_client.get_secret.assert_called_once_with('test-key')
    
    @patch.dict(os.environ, {'TEST_ENV_VAR': 'env-value'})
    def test_get_secret_fallback_to_env(self):
        """Test getting secret falls back to environment variable."""
        config = Config()
        result = config.get_secret('TEST_ENV_VAR')
        
        assert result == 'env-value'
    
    def test_get_secret_default_value(self):
        """Test getting secret returns default value when not found."""
        config = Config()
        result = config.get_secret('NON_EXISTENT_KEY', 'default-value')
        
        assert result == 'default-value'