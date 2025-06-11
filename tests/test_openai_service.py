"""Test OpenAI service integration."""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.openai_service import (
    ConversationMemory, 
    RateLimiter, 
    AzureOpenAIService
)


class TestConversationMemory:
    """Test conversation memory functionality."""
    
    def test_memory_initialization(self):
        """Test memory initialization."""
        memory = ConversationMemory(max_history=5)
        assert memory.max_history == 5
        assert memory._conversations == {}
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        memory = ConversationMemory()
        
        memory.add_message("conv1", "user", "Hello", {"user_name": "John"})
        
        conversation = memory.get_conversation("conv1")
        assert len(conversation) == 1
        assert conversation[0]["role"] == "user"
        assert conversation[0]["content"] == "Hello"
        assert conversation[0]["user_name"] == "John"
    
    def test_conversation_history_limit(self):
        """Test conversation history limit."""
        memory = ConversationMemory(max_history=3)
        
        # Add system message
        memory.set_system_message("conv1", "You are a helpful assistant")
        
        # Add more messages than the limit
        for i in range(5):
            memory.add_message("conv1", "user", f"Message {i}")
            memory.add_message("conv1", "assistant", f"Response {i}")
        
        conversation = memory.get_conversation("conv1")
        
        # Should have system message + limited history
        assert len(conversation) <= 3
        
        # System message should be preserved
        system_messages = [msg for msg in conversation if msg["role"] == "system"]
        assert len(system_messages) == 1
    
    def test_clear_conversation(self):
        """Test clearing conversation."""
        memory = ConversationMemory()
        
        memory.add_message("conv1", "user", "Hello")
        assert len(memory.get_conversation("conv1")) == 1
        
        memory.clear_conversation("conv1")
        assert len(memory.get_conversation("conv1")) == 0
    
    def test_set_system_message(self):
        """Test setting system message."""
        memory = ConversationMemory()
        
        memory.set_system_message("conv1", "You are a helpful assistant")
        
        conversation = memory.get_conversation("conv1")
        assert len(conversation) == 1
        assert conversation[0]["role"] == "system"
        assert conversation[0]["content"] == "You are a helpful assistant"
    
    def test_system_message_replacement(self):
        """Test system message is replaced when set again."""
        memory = ConversationMemory()
        
        memory.set_system_message("conv1", "First system message")
        memory.add_message("conv1", "user", "Hello")
        memory.set_system_message("conv1", "Second system message")
        
        conversation = memory.get_conversation("conv1")
        system_messages = [msg for msg in conversation if msg["role"] == "system"]
        
        assert len(system_messages) == 1
        assert system_messages[0]["content"] == "Second system message"


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_requests_per_minute=60)
        assert limiter.max_requests == 60
        assert limiter.requests == []
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests(self):
        """Test rate limiter allows requests under limit."""
        limiter = RateLimiter(max_requests_per_minute=60)
        
        # Should not wait for first request
        await limiter.wait_if_needed()
        assert len(limiter.requests) == 1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excess_requests(self):
        """Test rate limiter blocks excess requests."""
        limiter = RateLimiter(max_requests_per_minute=2)
        
        # First two requests should be allowed
        await limiter.wait_if_needed()
        await limiter.wait_if_needed()
        
        # Third request should be blocked (but we won't wait in test)
        assert len(limiter.requests) == 2


class TestAzureOpenAIService:
    """Test Azure OpenAI service functionality."""
    
    @patch('src.services.openai_service.AzureOpenAI')
    @patch('src.config.config')
    def test_service_initialization(self, mock_config, mock_azure_openai):
        """Test service initialization."""
        mock_config.azure_openai_api_key = 'test-key'
        mock_config.azure_openai_api_version = 'test-version'
        mock_config.azure_openai_endpoint = 'https://test.openai.azure.com/'
        mock_config.azure_openai_deployment_name = 'test-deployment'
        
        service = AzureOpenAIService()
        
        assert service.deployment_name == 'test-deployment'
        assert service.memory is not None
        assert service.rate_limiter is not None
        mock_azure_openai.assert_called_once()
    
    @patch('src.services.openai_service.AzureOpenAI')
    @patch('src.config.config')
    @pytest.mark.asyncio
    async def test_get_chat_response_success(self, mock_config, mock_azure_openai):
        """Test successful chat response."""
        # Setup mocks
        mock_config.azure_openai_api_key = 'test-key'
        mock_config.azure_openai_api_version = 'test-version'
        mock_config.azure_openai_endpoint = 'https://test.openai.azure.com/'
        mock_config.azure_openai_deployment_name = 'test-deployment'
        mock_config.openai_max_tokens = 1000
        mock_config.openai_temperature = 0.7
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client
        
        service = AzureOpenAIService()
        
        response = await service.get_chat_response(
            message="Hello",
            conversation_id="test-conv",
            user_name="Test User"
        )
        
        assert response == "Test response"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.services.openai_service.AzureOpenAI')
    @patch('src.config.config')
    @pytest.mark.asyncio
    async def test_get_chat_response_with_retry(self, mock_config, mock_azure_openai):
        """Test chat response with retry logic."""
        # Setup mocks
        mock_config.azure_openai_api_key = 'test-key'
        mock_config.azure_openai_api_version = 'test-version'
        mock_config.azure_openai_endpoint = 'https://test.openai.azure.com/'
        mock_config.azure_openai_deployment_name = 'test-deployment'
        mock_config.openai_max_tokens = 1000
        mock_config.openai_temperature = 0.7
        
        mock_client = MagicMock()
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client.chat.completions.create.side_effect = [
            Exception("API Error"),
            mock_response
        ]
        mock_azure_openai.return_value = mock_client
        
        service = AzureOpenAIService()
        
        response = await service.get_chat_response(
            message="Hello",
            conversation_id="test-conv",
            user_name="Test User",
            max_retries=2
        )
        
        assert response == "Test response"
        assert mock_client.chat.completions.create.call_count == 2
    
    @patch('src.services.openai_service.AzureOpenAI')
    @patch('src.config.config')
    def test_clear_conversation(self, mock_config, mock_azure_openai):
        """Test clearing conversation."""
        mock_config.azure_openai_api_key = 'test-key'
        mock_config.azure_openai_api_version = 'test-version'
        mock_config.azure_openai_endpoint = 'https://test.openai.azure.com/'
        mock_config.azure_openai_deployment_name = 'test-deployment'
        
        service = AzureOpenAIService()
        
        # Add a message
        service.memory.add_message("test-conv", "user", "Hello")
        assert len(service.memory.get_conversation("test-conv")) == 1
        
        # Clear conversation
        service.clear_conversation("test-conv")
        assert len(service.memory.get_conversation("test-conv")) == 0
    
    @patch('src.services.openai_service.AzureOpenAI')
    @patch('src.config.config')
    def test_get_conversation_summary(self, mock_config, mock_azure_openai):
        """Test getting conversation summary."""
        mock_config.azure_openai_api_key = 'test-key'
        mock_config.azure_openai_api_version = 'test-version'
        mock_config.azure_openai_endpoint = 'https://test.openai.azure.com/'
        mock_config.azure_openai_deployment_name = 'test-deployment'
        
        service = AzureOpenAIService()
        
        # Add some messages
        service.memory.add_message("test-conv", "user", "Hello", {"user_name": "John"})
        service.memory.add_message("test-conv", "assistant", "Hi there!")
        service.memory.add_message("test-conv", "user", "How are you?", {"user_name": "John"})
        
        summary = service.get_conversation_summary("test-conv")
        
        assert summary["message_count"] == 3
        assert summary["user_messages"] == 2
        assert summary["assistant_messages"] == 1
        assert "John" in summary["participants"]