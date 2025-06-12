"""Main Flask application with REST API endpoints for the chatbot."""
import logging
import asyncio
from typing import Dict, Any
from flask import Flask, request, jsonify, render_template_string
from botbuilder.core import (
    BotFrameworkAdapter, 
    BotFrameworkAdapterSettings,
    TurnContext
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity
from src.bot.teams_bot import TeamsBot
from src.services.openai_service import openai_service
from src.config import config
import json

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Bot Framework adapter settings - Support both Managed Identity and App Password
if config.microsoft_app_id and config.microsoft_app_password:
    # Traditional App ID/Password authentication
    logger.info("Using Bot Framework App ID/Password authentication")
    settings = BotFrameworkAdapterSettings(
        app_id=config.microsoft_app_id,
        app_password=config.microsoft_app_password
    )
else:
    # Managed Identity authentication (for Azure deployment)
    logger.info("Using Bot Framework Managed Identity authentication")
    settings = BotFrameworkAdapterSettings(
        app_id="",  # Empty for managed identity
        app_password=""  # Empty for managed identity
    )

# Validate Bot Framework configuration
if not config.microsoft_app_id and not config.microsoft_app_password:
    logger.warning("Bot Framework credentials not configured. Using Managed Identity mode for Azure deployment.")
elif config.microsoft_app_id and not config.microsoft_app_password:
    logger.warning("MICROSOFT_APP_PASSWORD is not configured but MICROSOFT_APP_ID is set. This may cause authentication issues.")
elif not config.microsoft_app_id and config.microsoft_app_password:
    logger.warning("MICROSOFT_APP_ID is not configured but MICROSOFT_APP_PASSWORD is set. This may cause authentication issues.")

# Create Bot Framework adapter
adapter = BotFrameworkAdapter(settings)

# Create bot instance
bot = TeamsBot()

# Error handler for Bot Framework
async def on_error(context: TurnContext, error: Exception):
    """
    Error handler for the Bot Framework adapter.
    
    Args:
        context: The turn context
        error: The exception that occurred
    """
    logger.error(f"Bot Framework error: {error}")
    
    # Send a message to the user
    await context.send_activity("Sorry, an error occurred. Please try again.")


adapter.on_turn_error = on_error


@app.route("/")
def home():
    """Simple web interface for testing the chatbot."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Azure Teams AI Chatbot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .chat-container {
                border: 1px solid #ddd;
                border-radius: 8px;
                height: 400px;
                overflow-y: auto;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #fafafa;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 8px;
                max-width: 80%;
            }
            .user-message {
                background-color: #007acc;
                color: white;
                margin-left: auto;
                text-align: right;
            }
            .bot-message {
                background-color: #e9ecef;
                color: #333;
            }
            .input-container {
                display: flex;
                gap: 10px;
            }
            #messageInput {
                flex: 1;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
            }
            #sendButton {
                padding: 12px 24px;
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            #sendButton:hover {
                background-color: #005a9e;
            }
            #sendButton:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .status {
                text-align: center;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }
            .loading {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            .error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .feature-list {
                margin: 20px 0;
            }
            .feature-list ul {
                list-style-type: none;
                padding: 0;
            }
            .feature-list li {
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            .feature-list li:before {
                content: "✓ ";
                color: #28a745;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Azure Teams AI Chatbot</h1>
            
            <div class="feature-list">
                <h3>Features:</h3>
                <ul>
                    <li>Azure OpenAI GPT integration</li>
                    <li>Microsoft Teams compatibility</li>
                    <li>Conversation memory</li>
                    <li>Error handling and retry logic</li>
                    <li>Rate limiting</li>
                </ul>
            </div>
            
            <h3>Test the Chatbot:</h3>
            <div class="chat-container" id="chatContainer">
                <div class="message bot-message">
                    👋 Hello! I'm your AI assistant. Type a message below to start chatting!
                </div>
            </div>
            
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Type your message here..." 
                       onkeypress="if(event.key==='Enter') sendMessage()">
                <button id="sendButton" onclick="sendMessage()">Send</button>
            </div>
            
            <div id="status"></div>
            
            <div style="margin-top: 30px; text-align: center; color: #666;">
                <p><strong>For Teams integration:</strong> Install the bot in Microsoft Teams using the Bot Framework registration.</p>
            </div>
        </div>

        <script>
            let conversationId = 'web-' + Math.random().toString(36).substr(2, 9);
            
            function addMessage(content, isUser = false) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + (isUser ? 'user-message' : 'bot-message');
                messageDiv.textContent = content;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            function showStatus(message, type = '') {
                const statusDiv = document.getElementById('status');
                statusDiv.textContent = message;
                statusDiv.className = 'status ' + type;
                if (type === '') {
                    setTimeout(() => {
                        statusDiv.textContent = '';
                        statusDiv.className = 'status';
                    }, 3000);
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const sendButton = document.getElementById('sendButton');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Add user message to chat
                addMessage(message, true);
                
                // Clear input and disable send button
                input.value = '';
                sendButton.disabled = true;
                showStatus('Thinking...', 'loading');
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            conversation_id: conversationId,
                            user_name: 'Web User'
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        addMessage(data.response);
                        showStatus('');
                    } else {
                        addMessage('Error: ' + (data.error || 'Unknown error occurred'));
                        showStatus('Error sending message', 'error');
                    }
                } catch (error) {
                    addMessage('Error: Failed to connect to the chatbot service');
                    showStatus('Connection error', 'error');
                }
                
                sendButton.disabled = false;
                input.focus();
            }
            
            // Focus on input when page loads
            document.getElementById('messageInput').focus();
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/api/messages", methods=["POST"])
def messages():
    """
    Bot Framework messaging endpoint for Teams integration.
    
    Returns:
        JSON response with status
    """
    try:
        # Get the activity from the request
        activity = Activity().deserialize(request.json)
        auth_header = request.headers.get("Authorization", "")
        
        # Process the activity
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        task = loop.create_task(
            adapter.process_activity(activity, auth_header, bot.on_turn)
        )
        loop.run_until_complete(task)
        loop.close()
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing Bot Framework message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Direct chat API endpoint for web interface and external integrations.
    
    Expected JSON payload:
    {
        "message": "User message",
        "conversation_id": "unique_conversation_id",
        "user_name": "User Name (optional)"
    }
    
    Returns:
        JSON response with AI response
    """
    try:
        data = request.get_json()
        
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400
        
        message = data["message"]
        conversation_id = data.get("conversation_id", f"api-{request.remote_addr}")
        user_name = data.get("user_name", "API User")
        
        # Get response from OpenAI service
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(
            openai_service.get_chat_response(
                message=message,
                conversation_id=conversation_id,
                user_name=user_name
            )
        )
        loop.close()
        
        return jsonify({
            "response": response,
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/conversation/<conversation_id>/clear", methods=["POST"])
def clear_conversation(conversation_id: str):
    """
    Clear conversation history for a specific conversation.
    
    Args:
        conversation_id: The conversation ID to clear
        
    Returns:
        JSON response with status
    """
    try:
        openai_service.clear_conversation(conversation_id)
        return jsonify({"status": "cleared", "conversation_id": conversation_id})
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/conversation/<conversation_id>/summary", methods=["GET"])
def conversation_summary(conversation_id: str):
    """
    Get conversation summary and statistics.
    
    Args:
        conversation_id: The conversation ID to summarize
        
    Returns:
        JSON response with conversation summary
    """
    try:
        summary = openai_service.get_conversation_summary(conversation_id)
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON response with health status
    """
    try:
        health_status = {
            "status": "healthy",
            "service": "Azure Teams AI Chatbot",
            "version": "1.0.0",
            "components": {
                "flask": "ok",
                "bot_framework": "ok",
                "azure_openai": "ok" if config.azure_openai_endpoint else "not_configured",
                "configuration": "ok" if config.microsoft_app_id else "incomplete"
            }
        }
        
        # Check if critical configuration is missing
        if not config.azure_openai_endpoint or not config.azure_openai_api_key:
            health_status["status"] = "degraded"
            health_status["components"]["azure_openai"] = "not_configured"
        
        if not config.microsoft_app_id or not config.microsoft_app_password:
            health_status["status"] = "degraded"
            health_status["components"]["bot_framework"] = "not_configured"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Configure Application Insights if available
    if config.appinsights_connection_string:
        try:
            from applicationinsights.flask.ext import AppInsights
            appinsights = AppInsights(app)
            logger.info("Application Insights initialized")
        except ImportError:
            logger.warning("Application Insights library not available")
    
    # Start the Flask application
    logger.info(f"Starting Azure Teams AI Chatbot on port {config.port}")
    app.run(
        host="0.0.0.0",
        port=config.port,
        debug=(config.flask_env == "development")
    )