"""Test utility functions."""
import pytest
from datetime import datetime, timedelta
from src.utils import (
    generate_conversation_id,
    sanitize_user_input,
    format_timestamp,
    calculate_duration,
    validate_conversation_id,
    extract_mention,
    truncate_text,
    mask_sensitive_data,
    create_adaptive_card,
    is_rate_limited,
    RetryHelper
)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_generate_conversation_id(self):
        """Test conversation ID generation."""
        conv_id1 = generate_conversation_id("test")
        conv_id2 = generate_conversation_id("test")
        
        assert conv_id1.startswith("test-")
        assert conv_id2.startswith("test-")
        assert conv_id1 != conv_id2  # Should be unique
        assert len(conv_id1.split("-")[1]) == 8  # UUID part should be 8 chars
    
    def test_sanitize_user_input(self):
        """Test user input sanitization."""
        # Test basic sanitization
        result = sanitize_user_input("  Hello   World  ")
        assert result == "Hello World"
        
        # Test HTML removal
        result = sanitize_user_input("Hello <script>alert('xss')</script> World")
        assert result == "Hello  World"
        
        # Test JavaScript removal
        result = sanitize_user_input("Hello javascript:alert('xss') World")
        assert result == "Hello  World"
        
        # Test length limit
        long_text = "A" * 5000
        result = sanitize_user_input(long_text, max_length=100)
        assert len(result) == 100
        
        # Test empty input
        result = sanitize_user_input("")
        assert result == ""
        
        # Test None input
        result = sanitize_user_input(None)
        assert result == ""
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        test_time = datetime(2023, 12, 25, 10, 30, 45)
        
        # Default format
        result = format_timestamp(test_time)
        assert result == "2023-12-25 10:30:45"
        
        # Custom format
        result = format_timestamp(test_time, "%Y-%m-%d")
        assert result == "2023-12-25"
    
    def test_calculate_duration(self):
        """Test duration calculation."""
        start_time = datetime(2023, 12, 25, 10, 0, 0)
        end_time = datetime(2023, 12, 25, 11, 30, 45)
        
        duration = calculate_duration(start_time, end_time)
        
        assert duration["total_seconds"] == 5445.0  # 1 hour 30 minutes 45 seconds
        assert duration["hours"] == 1
        assert duration["minutes"] == 30
        assert duration["seconds"] == 45
        assert duration["formatted"] == "01:30:45"
    
    def test_validate_conversation_id(self):
        """Test conversation ID validation."""
        # Valid IDs
        assert validate_conversation_id("conv-123") is True
        assert validate_conversation_id("user_456") is True
        assert validate_conversation_id("abc123") is True
        
        # Invalid IDs
        assert validate_conversation_id("") is False
        assert validate_conversation_id(None) is False
        assert validate_conversation_id("conv@123") is False  # Special characters
        assert validate_conversation_id("a" * 101) is False  # Too long
    
    def test_extract_mention(self):
        """Test bot mention extraction."""
        # Test mention extraction
        text, mentioned = extract_mention("@assistant hello there")
        assert text == "hello there"
        assert mentioned is True
        
        # Test no mention
        text, mentioned = extract_mention("hello there")
        assert text == "hello there"
        assert mentioned is False
        
        # Test case insensitive
        text, mentioned = extract_mention("@ASSISTANT hello")
        assert text == "hello"
        assert mentioned is True
        
        # Test with custom bot name
        text, mentioned = extract_mention("@mybot help me", "mybot")
        assert text == "help me"
        assert mentioned is True
    
    def test_truncate_text(self):
        """Test text truncation."""
        # Test no truncation needed
        result = truncate_text("Hello", 10)
        assert result == "Hello"
        
        # Test truncation
        result = truncate_text("Hello World", 8)
        assert result == "Hello..."
        assert len(result) == 8
        
        # Test with custom suffix
        result = truncate_text("Hello World", 8, " (more)")
        assert result == " (more)"  # Suffix is longer than max length
        
        # Test empty text
        result = truncate_text("", 10)
        assert result == ""
    
    def test_mask_sensitive_data(self):
        """Test sensitive data masking."""
        # Test email masking
        result = mask_sensitive_data("Contact me at user@example.com for help")
        assert "***@***.***" in result
        assert "user@example.com" not in result
        
        # Test phone masking
        result = mask_sensitive_data("Call me at 123-456-7890")
        assert "***-***-****" in result
        assert "123-456-7890" not in result
        
        # Test API key masking
        result = mask_sensitive_data("API key: abcd1234567890abcd1234567890abcd")
        assert "***API_KEY***" in result
    
    def test_create_adaptive_card(self):
        """Test adaptive card creation."""
        card = create_adaptive_card("Test Title", "Test Content")
        
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.3"
        assert len(card["body"]) == 2
        assert card["body"][0]["text"] == "Test Title"
        assert card["body"][1]["text"] == "Test Content"
        
        # Test with actions
        actions = [{"type": "Action.Submit", "title": "Submit"}]
        card = create_adaptive_card("Title", "Content", actions)
        assert "actions" in card
        assert card["actions"] == actions
    
    def test_is_rate_limited(self):
        """Test rate limiting check."""
        now = datetime.now()
        
        # No previous request
        assert is_rate_limited(None) is False
        
        # Recent request (should be limited)
        recent = now - timedelta(seconds=0.5)
        assert is_rate_limited(recent, min_interval_seconds=1) is True
        
        # Old request (should not be limited)
        old = now - timedelta(seconds=2)
        assert is_rate_limited(old, min_interval_seconds=1) is False


class TestRetryHelper:
    """Test retry helper functionality."""
    
    def test_calculate_backoff(self):
        """Test exponential backoff calculation."""
        # Test increasing delays
        delay1 = RetryHelper.calculate_backoff(0, base_delay=1.0)
        delay2 = RetryHelper.calculate_backoff(1, base_delay=1.0)
        delay3 = RetryHelper.calculate_backoff(2, base_delay=1.0)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0
        
        # Test max delay limit
        delay_max = RetryHelper.calculate_backoff(10, base_delay=1.0, max_delay=5.0)
        assert delay_max == 5.0
    
    def test_should_retry(self):
        """Test retry decision logic."""
        exception = Exception("Test error")
        
        # Should retry on early attempts
        assert RetryHelper.should_retry(exception, 0, max_attempts=3) is True
        assert RetryHelper.should_retry(exception, 1, max_attempts=3) is True
        
        # Should not retry on last attempt
        assert RetryHelper.should_retry(exception, 2, max_attempts=3) is False