#!/usr/bin/env python3
"""
Test script to verify the Azure Teams AI Chatbot deployment
"""
import os
import sys
import requests
import json
from src.config import Config

def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing Configuration...")
    
    config = Config()
    
    # Test basic config
    print(f"  ✓ Flask Environment: {config.flask_env}")
    print(f"  ✓ Log Level: {config.log_level}")
    print(f"  ✓ Port: {config.port}")
    
    # Test Azure OpenAI config
    if config.azure_openai_endpoint:
        print(f"  ✓ Azure OpenAI Endpoint: {config.azure_openai_endpoint}")
        print(f"  ✓ Deployment Name: {config.azure_openai_deployment_name}")
        print(f"  ✓ API Version: {config.azure_openai_api_version}")
        
        if config.azure_openai_api_key:
            print("  ✓ Azure OpenAI API Key: [CONFIGURED]")
        else:
            print("  ⚠️  Azure OpenAI API Key: [NOT CONFIGURED]")
    else:
        print("  ❌ Azure OpenAI Endpoint: [NOT CONFIGURED]")
    
    # Test Bot Framework config
    if config.microsoft_app_id:
        print(f"  ✓ Microsoft App ID: {config.microsoft_app_id}")
        
        if config.microsoft_app_password:
            print("  ✓ Microsoft App Password: [CONFIGURED]")
        else:
            print("  ⚠️  Microsoft App Password: [NOT CONFIGURED - Using Managed Identity]")
    else:
        print("  ❌ Microsoft App ID: [NOT CONFIGURED]")
    
    # Test Key Vault config
    if hasattr(config, '_key_vault_client') and config._key_vault_client:
        print("  ✓ Azure Key Vault: [CONNECTED]")
    else:
        print("  ⚠️  Azure Key Vault: [NOT CONNECTED]")
    
    return config

def test_health_endpoint(base_url):
    """Test the health endpoint."""
    print(f"\n🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"  ✓ Health Check: {health_data['status'].upper()}")
            
            for component, status in health_data['components'].items():
                if status == "ok":
                    print(f"    ✓ {component}: {status}")
                elif "managed_identity" in status:
                    print(f"    ⚠️  {component}: {status}")
                else:
                    print(f"    ❌ {component}: {status}")
        else:
            print(f"  ❌ Health Check Failed: HTTP {response.status_code}")
            print(f"    Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Health Check Failed: {e}")

def test_bot_endpoint(base_url):
    """Test the bot endpoint."""
    print(f"\n🤖 Testing Bot Endpoint...")
    
    try:
        # Test GET (should return 405 Method Not Allowed)
        response = requests.get(f"{base_url}/api/messages", timeout=10)
        
        if response.status_code == 405:
            print("  ✓ Bot endpoint is responding (405 Method Not Allowed - expected)")
        else:
            print(f"  ⚠️  Bot endpoint returned: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Bot endpoint test failed: {e}")

def test_chat_api(base_url):
    """Test the chat API endpoint."""
    print(f"\n💬 Testing Chat API...")
    
    try:
        test_message = {
            "message": "Hello, this is a test message",
            "conversation_id": "test-deployment",
            "user_name": "Deployment Test"
        }
        
        response = requests.post(
            f"{base_url}/api/chat",
            json=test_message,
            timeout=30
        )
        
        if response.status_code == 200:
            chat_data = response.json()
            print("  ✓ Chat API is working")
            print(f"    Response: {chat_data.get('response', 'No response')[:100]}...")
        else:
            print(f"  ❌ Chat API Failed: HTTP {response.status_code}")
            print(f"    Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Chat API test failed: {e}")

def main():
    """Main test function."""
    print("🚀 Azure Teams AI Chatbot Deployment Test")
    print("=" * 50)
    
    # Test configuration
    config = test_configuration()
    
    # Determine base URL
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        # Try to determine from environment or use local
        base_url = os.getenv('APP_URL', 'http://localhost:8000')
    
    print(f"\n🌐 Testing App URL: {base_url}")
    
    # Test endpoints
    test_health_endpoint(base_url)
    test_bot_endpoint(base_url)
    test_chat_api(base_url)
    
    print("\n" + "=" * 50)
    print("✅ Deployment test completed!")
    print("\nNext steps:")
    print("1. If running on Azure, test with the App Service URL")
    print("2. Configure Teams app using the generated manifest")
    print("3. Test bot in Microsoft Teams")

if __name__ == "__main__":
    main()
