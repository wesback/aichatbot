"""Azure OpenAI service integration with conversation memory and error handling."""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from src.config import config

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history and context for chatbot interactions."""
    
    def __init__(self, max_history: int = None):
        """
        Initialize conversation memory.
        
        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.max_history = max_history or config.max_conversation_history
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_message(self, conversation_id: str, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add a message to conversation history.
        
        Args:
            conversation_id: Unique identifier for the conversation
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional message metadata
        """
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        
        if metadata:
            message.update(metadata)
        
        self._conversations[conversation_id].append(message)
        
        # Trim history if it exceeds max_history
        if len(self._conversations[conversation_id]) > self.max_history:
            # Keep system messages and trim user/assistant messages
            system_messages = [msg for msg in self._conversations[conversation_id] if msg["role"] == "system"]
            other_messages = [msg for msg in self._conversations[conversation_id] if msg["role"] != "system"]
            
            # Keep the most recent messages
            other_messages = other_messages[-(self.max_history - len(system_messages)):]
            
            self._conversations[conversation_id] = system_messages + other_messages
    
    def get_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a given conversation ID.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            List of messages in the conversation
        """
        return self._conversations.get(conversation_id, [])
    
    def clear_conversation(self, conversation_id: str):
        """
        Clear conversation history for a given conversation ID.
        
        Args:
            conversation_id: Unique identifier for the conversation
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
    
    def set_system_message(self, conversation_id: str, content: str):
        """
        Set or update the system message for a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            content: System message content
        """
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        
        # Remove existing system messages
        self._conversations[conversation_id] = [
            msg for msg in self._conversations[conversation_id] 
            if msg["role"] != "system"
        ]
        
        # Add new system message at the beginning
        system_message = {
            "role": "system",
            "content": content,
            "timestamp": time.time()
        }
        self._conversations[conversation_id].insert(0, system_message)


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum requests allowed per minute
        """
        self.max_requests = max_requests_per_minute
        self.requests = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = 60 - (now - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)


class AzureOpenAIService:
    """Service class for Azure OpenAI integration with error handling and retry logic."""
    
    def __init__(self):
        """Initialize Azure OpenAI service."""
        self.client = AzureOpenAI(
            api_key=config.azure_openai_api_key,
            api_version=config.azure_openai_api_version,
            azure_endpoint=config.azure_openai_endpoint
        )
        self.deployment_name = config.azure_openai_deployment_name
        self.memory = ConversationMemory()
        self.rate_limiter = RateLimiter()
        
        # Default system message
        self.default_system_message = (
            "You are a helpful AI assistant integrated with Microsoft Teams. "
            "Provide clear, concise, and professional responses. "
            "If you're unsure about something, be honest about it. "
            "Format your responses appropriately for Teams chat."
        )
    
    async def get_chat_response(
        self,
        message: str,
        conversation_id: str,
        user_name: str = None,
        system_message: str = None,
        max_retries: int = 3
    ) -> str:
        """
        Get a chat response from Azure OpenAI.
        
        Args:
            message: User message
            conversation_id: Unique conversation identifier
            user_name: Name of the user (optional)
            system_message: Custom system message (optional)
            max_retries: Maximum number of retry attempts
            
        Returns:
            AI response message
        """
        # Set system message if provided or use default
        if system_message or conversation_id not in [conv_id for conv_id in self.memory._conversations.keys()]:
            self.memory.set_system_message(
                conversation_id, 
                system_message or self.default_system_message
            )
        
        # Add user message to conversation
        user_display_name = f" ({user_name})" if user_name else ""
        self.memory.add_message(conversation_id, "user", message, {"user_name": user_name})
        
        # Get conversation history
        conversation_history = self.memory.get_conversation(conversation_id)
        
        # Prepare messages for OpenAI API
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                await self.rate_limiter.wait_if_needed()
                
                logger.info(f"Sending request to Azure OpenAI (attempt {attempt + 1})")
                
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages,
                    max_tokens=config.openai_max_tokens,
                    temperature=config.openai_temperature,
                    top_p=0.9,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                
                assistant_message = response.choices[0].message.content
                
                # Add assistant response to conversation
                self.memory.add_message(conversation_id, "assistant", assistant_message)
                
                logger.info("Successfully received response from Azure OpenAI")
                return assistant_message
                
            except Exception as e:
                logger.error(f"Error calling Azure OpenAI (attempt {attempt + 1}): {e}")
                
                if attempt == max_retries - 1:
                    # Last attempt failed
                    error_message = (
                        "I'm sorry, I'm having trouble connecting to my AI service right now. "
                        "Please try again in a moment."
                    )
                    self.memory.add_message(conversation_id, "assistant", error_message)
                    return error_message
                
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retry")
                await asyncio.sleep(wait_time)
        
        # This should never be reached, but just in case
        return "I'm sorry, I encountered an unexpected error. Please try again."
    
    def clear_conversation(self, conversation_id: str):
        """
        Clear conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
        """
        self.memory.clear_conversation(conversation_id)
        logger.info(f"Cleared conversation history for {conversation_id}")
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation summary and statistics.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Dictionary with conversation summary
        """
        conversation = self.memory.get_conversation(conversation_id)
        
        if not conversation:
            return {"message_count": 0, "participants": []}
        
        user_messages = [msg for msg in conversation if msg["role"] == "user"]
        assistant_messages = [msg for msg in conversation if msg["role"] == "assistant"]
        
        participants = list(set([
            msg.get("user_name", "Unknown") 
            for msg in user_messages 
            if msg.get("user_name")
        ]))
        
        return {
            "message_count": len(conversation),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "participants": participants,
            "start_time": min(msg["timestamp"] for msg in conversation) if conversation else None,
            "last_activity": max(msg["timestamp"] for msg in conversation) if conversation else None
        }


# Global service instance
openai_service = AzureOpenAIService()