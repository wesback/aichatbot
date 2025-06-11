"""Test configuration and fixtures."""
import pytest
import os
from unittest.mock import patch

# Set test environment variables
os.environ['FLASK_ENV'] = 'testing'
os.environ['LOG_LEVEL'] = 'DEBUG'

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch('src.config.config') as mock:
        mock.azure_openai_endpoint = 'https://test.openai.azure.com/'
        mock.azure_openai_api_key = 'test-key'
        mock.azure_openai_deployment_name = 'test-deployment'
        mock.microsoft_app_id = 'test-app-id'
        mock.microsoft_app_password = 'test-password'
        mock.max_conversation_history = 10
        mock.openai_max_tokens = 1000
        mock.openai_temperature = 0.7
        yield mock