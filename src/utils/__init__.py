"""Utility functions for the Azure Teams chatbot."""
import logging
import re
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def setup_logging(log_level: str = "INFO", log_format: str = None) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom logging format
        
    Returns:
        Configured logger instance
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("chatbot.log")
        ]
    )
    
    return logging.getLogger(__name__)


def generate_conversation_id(prefix: str = "conv") -> str:
    """
    Generate a unique conversation ID.
    
    Args:
        prefix: Prefix for the conversation ID
        
    Returns:
        Unique conversation ID
    """
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def sanitize_user_input(text: str, max_length: int = 4000) -> str:
    """
    Sanitize user input by removing potentially harmful content.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove potential HTML/XML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove potential script injections
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    return text


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp: Datetime object to format
        format_str: Format string for datetime formatting
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime(format_str)


def calculate_duration(start_time: datetime, end_time: datetime = None) -> Dict[str, Any]:
    """
    Calculate duration between two timestamps.
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp (defaults to now)
        
    Returns:
        Dictionary with duration information
    """
    if end_time is None:
        end_time = datetime.now()
    
    duration = end_time - start_time
    
    total_seconds = duration.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    return {
        "total_seconds": total_seconds,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "formatted": f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    }


def validate_conversation_id(conversation_id: str) -> bool:
    """
    Validate conversation ID format.
    
    Args:
        conversation_id: Conversation ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not conversation_id:
        return False
    
    # Allow alphanumeric characters, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, conversation_id)) and len(conversation_id) <= 100


def extract_mention(text: str, bot_name: str = "assistant") -> tuple[str, bool]:
    """
    Extract bot mention from text and return clean text.
    
    Args:
        text: Input text that may contain bot mention
        bot_name: Name of the bot to look for
        
    Returns:
        Tuple of (clean_text, was_mentioned)
    """
    if not text:
        return "", False
    
    # Look for @bot_name or similar patterns
    mention_patterns = [
        rf'@{re.escape(bot_name)}\s*',
        rf'@{re.escape(bot_name.lower())}\s*',
        rf'@{re.escape(bot_name.upper())}\s*',
        r'@assistant\s*',
        r'@bot\s*'
    ]
    
    was_mentioned = False
    clean_text = text
    
    for pattern in mention_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            was_mentioned = True
            clean_text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
            break
    
    return clean_text, was_mentioned


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    if max_length <= len(suffix):
        return suffix[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data in text for logging.
    
    Args:
        text: Text that may contain sensitive data
        
    Returns:
        Text with sensitive data masked
    """
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  '***@***.***', text)
    
    # Mask phone numbers (basic patterns)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '***-***-****', text)
    
    # Mask credit card numbers (basic pattern)
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 
                  '****-****-****-****', text)
    
    # Mask API keys (common patterns)
    text = re.sub(r'\b[A-Za-z0-9]{32,}\b', '***API_KEY***', text)
    
    return text


def create_adaptive_card(title: str, content: str, actions: list = None) -> Dict[str, Any]:
    """
    Create a basic adaptive card structure.
    
    Args:
        title: Card title
        content: Card content
        actions: List of card actions
        
    Returns:
        Adaptive card dictionary
    """
    card = {
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "text": title,
                "size": "Medium",
                "weight": "Bolder"
            },
            {
                "type": "TextBlock",
                "text": content,
                "wrap": True
            }
        ]
    }
    
    if actions:
        card["actions"] = actions
    
    return card


def is_rate_limited(last_request_time: datetime, min_interval_seconds: int = 1) -> bool:
    """
    Check if request should be rate limited.
    
    Args:
        last_request_time: Timestamp of last request
        min_interval_seconds: Minimum interval between requests
        
    Returns:
        True if should be rate limited, False otherwise
    """
    if not last_request_time:
        return False
    
    time_since_last = datetime.now() - last_request_time
    return time_since_last.total_seconds() < min_interval_seconds


def health_check_azure_openai(endpoint: str, api_key: str) -> Dict[str, Any]:
    """
    Perform a health check on Azure OpenAI service.
    
    Args:
        endpoint: Azure OpenAI endpoint
        api_key: API key
        
    Returns:
        Health check result
    """
    try:
        # This is a basic check - in a real implementation, you might
        # want to make a simple API call to verify connectivity
        if not endpoint or not api_key:
            return {"status": "unhealthy", "error": "Missing configuration"}
        
        # Basic URL validation
        if not endpoint.startswith("https://"):
            return {"status": "unhealthy", "error": "Invalid endpoint URL"}
        
        return {"status": "healthy"}
    
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


class RetryHelper:
    """Helper class for implementing retry logic."""
    
    @staticmethod
    def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Attempt number (0-based)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            
        Returns:
            Delay in seconds
        """
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)
    
    @staticmethod
    def should_retry(exception: Exception, attempt: int, max_attempts: int = 3) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            exception: Exception that occurred
            attempt: Current attempt number (0-based)
            max_attempts: Maximum number of attempts
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= max_attempts - 1:
            return False
        
        # Add specific exception handling logic here
        # For example, retry on network errors but not on authentication errors
        
        return True