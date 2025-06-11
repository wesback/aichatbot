"""Test Flask application endpoints."""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from app import app


class TestFlaskApplication:
    """Test Flask application endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_home_endpoint(self, client):
        """Test home endpoint returns web interface."""
        response = client.get('/')
        
        assert response.status_code == 200
        assert b'Azure Teams AI Chatbot' in response.data
        assert b'Test the Chatbot:' in response.data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        
        assert response.status_code in [200, 503]  # May be degraded due to missing config
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'service' in data
        assert 'components' in data
        assert data['service'] == 'Azure Teams AI Chatbot'
    
    @patch('src.services.openai_service.openai_service')
    def test_chat_endpoint_success(self, mock_openai_service, client):
        """Test chat endpoint with successful response."""
        # Setup mock
        mock_openai_service.get_chat_response = AsyncMock(return_value="Test response")
        
        response = client.post('/api/chat', 
                             json={
                                 'message': 'Hello',
                                 'conversation_id': 'test-conv',
                                 'user_name': 'Test User'
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['response'] == 'Test response'
        assert data['conversation_id'] == 'test-conv'
    
    def test_chat_endpoint_missing_message(self, client):
        """Test chat endpoint with missing message."""
        response = client.post('/api/chat', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Message is required' in data['error']
    
    def test_chat_endpoint_invalid_json(self, client):
        """Test chat endpoint with invalid JSON."""
        response = client.post('/api/chat', 
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    @patch('src.services.openai_service.openai_service')
    def test_clear_conversation_endpoint(self, mock_openai_service, client):
        """Test clear conversation endpoint."""
        mock_openai_service.clear_conversation = MagicMock()
        
        response = client.post('/api/conversation/test-conv/clear')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'cleared'
        assert data['conversation_id'] == 'test-conv'
        mock_openai_service.clear_conversation.assert_called_once_with('test-conv')
    
    @patch('src.services.openai_service.openai_service')
    def test_conversation_summary_endpoint(self, mock_openai_service, client):
        """Test conversation summary endpoint."""
        mock_summary = {
            'message_count': 5,
            'user_messages': 3,
            'assistant_messages': 2,
            'participants': ['Test User']
        }
        mock_openai_service.get_conversation_summary.return_value = mock_summary
        
        response = client.get('/api/conversation/test-conv/summary')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == mock_summary
        mock_openai_service.get_conversation_summary.assert_called_once_with('test-conv')
    
    def test_not_found_endpoint(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    @patch('app.adapter')
    def test_messages_endpoint_bot_framework(self, mock_adapter, client):
        """Test Bot Framework messages endpoint."""
        mock_adapter.process_activity = AsyncMock()
        
        activity_data = {
            'type': 'message',
            'text': 'Hello bot',
            'from': {'id': 'user123', 'name': 'Test User'},
            'conversation': {'id': 'conv123'},
            'recipient': {'id': 'bot123', 'name': 'Test Bot'}
        }
        
        response = client.post('/api/messages',
                             json=activity_data,
                             headers={'Authorization': 'Bearer test-token'})
        
        # The endpoint should process the activity
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'


class TestHealthCheckDetails:
    """Test detailed health check functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('src.config.config')
    def test_health_check_healthy_config(self, mock_config, client):
        """Test health check with complete configuration."""
        mock_config.azure_openai_endpoint = 'https://test.openai.azure.com/'
        mock_config.azure_openai_api_key = 'test-key'
        mock_config.microsoft_app_id = 'test-app-id'
        mock_config.microsoft_app_password = 'test-password'
        
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['components']['azure_openai'] == 'ok'
        assert data['components']['configuration'] == 'ok'
    
    @patch('src.config.config')
    def test_health_check_degraded_config(self, mock_config, client):
        """Test health check with incomplete configuration."""
        mock_config.azure_openai_endpoint = ''
        mock_config.azure_openai_api_key = ''
        mock_config.microsoft_app_id = ''
        mock_config.microsoft_app_password = ''
        
        response = client.get('/health')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['status'] == 'degraded'