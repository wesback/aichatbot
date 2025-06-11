# API Documentation

This document describes the REST API endpoints provided by the Azure Teams AI Chatbot.

## Base URL

```
https://your-app-name.azurewebsites.net
```

## Authentication

Most endpoints do not require authentication for testing purposes. In production, you may want to implement API key authentication.

## Endpoints

### Health Check

Check the health status of the application and its dependencies.

**GET** `/health`

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "service": "Azure Teams AI Chatbot",
  "version": "1.0.0",
  "components": {
    "flask": "ok",
    "bot_framework": "ok|not_configured",
    "azure_openai": "ok|not_configured",
    "configuration": "ok|incomplete"
  }
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Degraded or unhealthy

---

### Chat

Send a message to the AI chatbot and receive a response.

**POST** `/api/chat`

**Request Body:**
```json
{
  "message": "Hello, how can you help me?",
  "conversation_id": "optional-conversation-id",
  "user_name": "Optional User Name"
}
```

**Response:**
```json
{
  "response": "Hello! I'm here to help you with various tasks...",
  "conversation_id": "conv-abc123"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (missing message)
- `500` - Internal server error

---

### Clear Conversation

Clear the conversation history for a specific conversation.

**POST** `/api/conversation/{conversation_id}/clear`

**Response:**
```json
{
  "status": "cleared",
  "conversation_id": "conv-abc123"
}
```

**Status Codes:**
- `200` - Success
- `500` - Internal server error

---

### Conversation Summary

Get a summary of a conversation including message counts and participants.

**GET** `/api/conversation/{conversation_id}/summary`

**Response:**
```json
{
  "message_count": 15,
  "user_messages": 8,
  "assistant_messages": 7,
  "participants": ["John Doe", "Jane Smith"],
  "start_time": 1640995200.0,
  "last_activity": 1640998800.0
}
```

**Status Codes:**
- `200` - Success
- `500` - Internal server error

---

### Bot Framework Messages

Handle Bot Framework messaging for Teams integration.

**POST** `/api/messages`

This endpoint is used by the Microsoft Bot Framework to send activities to the bot. It expects Bot Framework Activity objects.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:** Bot Framework Activity JSON

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` - Success
- `401` - Unauthorized (invalid Bot Framework authentication)
- `500` - Internal server error

---

### Web Interface

Access the web-based testing interface.

**GET** `/`

Returns an HTML page with a simple chat interface for testing the bot.

## Error Handling

All endpoints return error responses in the following format:

```json
{
  "error": "Error description"
}
```

Common error scenarios:
- Missing required parameters
- Invalid conversation IDs
- Azure OpenAI service unavailable
- Bot Framework authentication failures

## Rate Limiting

The chatbot implements rate limiting to prevent abuse:
- Default: 60 requests per minute per conversation
- Rate limit headers are not currently exposed in responses
- Exceeded limits result in delayed responses rather than errors

## Conversation Management

### Conversation IDs

- Conversation IDs are automatically generated if not provided
- IDs must be alphanumeric with hyphens and underscores only
- Maximum length: 100 characters
- Example: `conv-abc123`, `user_session_456`

### Message History

- Each conversation maintains a history of messages
- Default maximum: 10 messages per conversation (configurable)
- System messages are preserved when trimming history
- History is stored in memory and not persisted across restarts

## Usage Examples

### Basic Chat

```bash
curl -X POST https://your-app.azurewebsites.net/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is artificial intelligence?",
    "conversation_id": "my-conversation",
    "user_name": "John Doe"
  }'
```

### Health Check

```bash
curl https://your-app.azurewebsites.net/health
```

### Clear Conversation

```bash
curl -X POST https://your-app.azurewebsites.net/api/conversation/my-conversation/clear
```

### Get Conversation Summary

```bash
curl https://your-app.azurewebsites.net/api/conversation/my-conversation/summary
```

## SDK Integration

### JavaScript/TypeScript

```javascript
class ChatbotClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async sendMessage(message, conversationId, userName) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        user_name: userName,
      }),
    });
    return response.json();
  }

  async clearConversation(conversationId) {
    const response = await fetch(`${this.baseUrl}/api/conversation/${conversationId}/clear`, {
      method: 'POST',
    });
    return response.json();
  }
}

// Usage
const client = new ChatbotClient('https://your-app.azurewebsites.net');
const result = await client.sendMessage('Hello!', 'conv-123', 'John');
console.log(result.response);
```

### Python

```python
import requests

class ChatbotClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def send_message(self, message, conversation_id=None, user_name=None):
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
                "user_name": user_name,
            }
        )
        return response.json()

    def clear_conversation(self, conversation_id):
        response = requests.post(
            f"{self.base_url}/api/conversation/{conversation_id}/clear"
        )
        return response.json()

# Usage
client = ChatbotClient("https://your-app.azurewebsites.net")
result = client.send_message("Hello!", "conv-123", "John")
print(result["response"])
```