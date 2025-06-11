"""Data models for the Azure Teams chatbot."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class Message:
    """Represents a conversation message."""
    role: str  # 'user', 'assistant', or 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Represents a conversation with message history."""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    participants: List[str] = field(default_factory=list)
    
    def add_message(self, message: Message):
        """Add a message to the conversation."""
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        if message.user_name and message.user_name not in self.participants:
            self.participants.append(message.user_name)
    
    def get_message_count(self) -> int:
        """Get total message count."""
        return len(self.messages)
    
    def get_user_message_count(self) -> int:
        """Get count of user messages."""
        return len([msg for msg in self.messages if msg.role == 'user'])
    
    def get_assistant_message_count(self) -> int:
        """Get count of assistant messages."""
        return len([msg for msg in self.messages if msg.role == 'assistant'])


@dataclass
class ChatRequest:
    """Represents a chat request from the API."""
    message: str
    conversation_id: str
    user_name: Optional[str] = None
    system_message: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@dataclass
class ChatResponse:
    """Represents a chat response from the API."""
    response: str
    conversation_id: str
    message_count: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationSummary:
    """Represents a conversation summary."""
    conversation_id: str
    message_count: int
    user_messages: int
    assistant_messages: int
    participants: List[str]
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    
    @classmethod
    def from_conversation(cls, conversation: Conversation) -> 'ConversationSummary':
        """Create a summary from a conversation object."""
        duration = None
        if conversation.messages:
            start_time = conversation.created_at
            end_time = conversation.last_activity
            duration = (end_time - start_time).total_seconds() / 60
        
        return cls(
            conversation_id=conversation.id,
            message_count=conversation.get_message_count(),
            user_messages=conversation.get_user_message_count(),
            assistant_messages=conversation.get_assistant_message_count(),
            participants=conversation.participants.copy(),
            start_time=conversation.created_at,
            last_activity=conversation.last_activity,
            duration_minutes=duration
        )


@dataclass
class BotConfiguration:
    """Represents bot configuration settings."""
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment: str
    microsoft_app_id: str
    microsoft_app_password: str
    max_conversation_history: int = 10
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.7
    rate_limit_requests_per_minute: int = 60
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.azure_openai_endpoint:
            errors.append("Azure OpenAI endpoint is required")
        
        if not self.azure_openai_api_key:
            errors.append("Azure OpenAI API key is required")
        
        if not self.azure_openai_deployment:
            errors.append("Azure OpenAI deployment name is required")
        
        if not self.microsoft_app_id:
            errors.append("Microsoft App ID is required")
        
        if not self.microsoft_app_password:
            errors.append("Microsoft App Password is required")
        
        if self.max_conversation_history < 1:
            errors.append("Max conversation history must be at least 1")
        
        if self.openai_max_tokens < 1:
            errors.append("OpenAI max tokens must be at least 1")
        
        if not 0 <= self.openai_temperature <= 2:
            errors.append("OpenAI temperature must be between 0 and 2")
        
        if self.rate_limit_requests_per_minute < 1:
            errors.append("Rate limit must be at least 1 request per minute")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0