#!/usr/bin/env python3
"""
Configuration Validator for Azure Teams AI Chatbot
Validates configuration and tests connectivity to Azure services.
"""
import os
import sys
import requests
import logging
from src.config import Config

def setup_logging():
    """Set up logging for the validator."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def validate_config():
    """Validate application configuration."""
    logger = setup_logging()
    config = Config()
    errors = []
    warnings = []
    
    logger.info("=== Azure Teams AI Chatbot Configuration Validation ===")
    
    # Check Azure OpenAI settings
    logger.info("Checking Azure OpenAI configuration...")
    if not config.azure_openai_endpoint:
        errors.append("Azure OpenAI endpoint not configured")
    else:
        logger.info(f"✅ Azure OpenAI endpoint: {config.azure_openai_endpoint}")
    
    if not config.azure_openai_api_key:
        errors.append("Azure OpenAI API key not configured")
    else:
        logger.info("✅ Azure OpenAI API key is configured")
    
    if not config.azure_openai_deployment_name:
        warnings.append("Azure OpenAI deployment name not configured")
    else:
        logger.info(f"✅ Azure OpenAI deployment: {config.azure_openai_deployment_name}")
    
    # Check Bot Framework settings
    logger.info("Checking Bot Framework configuration...")
    if not config.microsoft_app_id:
        warnings.append("Microsoft App ID not configured - using Managed Identity mode")
        logger.info("ℹ️  Microsoft App ID not configured - this is expected for Managed Identity deployment")
    else:
        logger.info(f"✅ Microsoft App ID: {config.microsoft_app_id}")
    
    if not config.microsoft_app_password:
        warnings.append("Microsoft App Password not configured - using Managed Identity mode")
        logger.info("ℹ️  Microsoft App Password not configured - this is expected for Managed Identity deployment")
    else:
        logger.info("✅ Microsoft App Password is configured")
    
    # Check Key Vault configuration
    logger.info("Checking Azure Key Vault configuration...")
    if hasattr(config, '_key_vault_client') and config._key_vault_client:
        logger.info("✅ Key Vault client initialized successfully")
    else:
        warnings.append("Key Vault client not initialized - secrets will be read from environment variables")
    
    # Test Azure OpenAI connectivity
    if config.azure_openai_endpoint and config.azure_openai_api_key:
        logger.info("Testing Azure OpenAI connectivity...")
        try:
            headers = {
                'api-key': config.azure_openai_api_key,
                'Content-Type': 'application/json'
            }
            url = f"{config.azure_openai_endpoint.rstrip('/')}/openai/deployments?api-version=2023-05-15"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Azure OpenAI connectivity test successful")
                deployments = response.json().get('data', [])
                if deployments:
                    logger.info(f"Available deployments: {[d.get('id') for d in deployments]}")
                else:
                    warnings.append("No deployments found in Azure OpenAI service")
            else:
                errors.append(f"Azure OpenAI API test failed: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
        except requests.exceptions.RequestException as e:
            errors.append(f"Azure OpenAI connectivity test failed: {e}")
    
    # Environment analysis
    logger.info("Environment analysis...")
    env_vars = {
        'AZURE_OPENAI_ENDPOINT': os.getenv('AZURE_OPENAI_ENDPOINT'),
        'AZURE_OPENAI_API_KEY': '***' if os.getenv('AZURE_OPENAI_API_KEY') else None,
        'AZURE_OPENAI_DEPLOYMENT_NAME': os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
        'MICROSOFT_APP_ID': os.getenv('MICROSOFT_APP_ID'),
        'MICROSOFT_APP_PASSWORD': '***' if os.getenv('MICROSOFT_APP_PASSWORD') else None,
        'AZURE_KEY_VAULT_URL': os.getenv('AZURE_KEY_VAULT_URL'),
        'FLASK_ENV': os.getenv('FLASK_ENV'),
    }
    
    logger.info("Environment variables status:")
    for key, value in env_vars.items():
        status = "✅ Set" if value else "❌ Not set"
        logger.info(f"  {key}: {status}")
    
    # Print results summary
    print("\n" + "="*60)
    print("CONFIGURATION VALIDATION SUMMARY")
    print("="*60)
    
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not errors:
        if not warnings:
            print("✅ Configuration is fully valid")
        else:
            print("✅ Configuration is valid with warnings")
        
        # Provide guidance for Managed Identity
        if not config.microsoft_app_id and not config.microsoft_app_password:
            print("\nℹ️  MANAGED IDENTITY MODE DETECTED")
            print("Your application is configured for Azure Managed Identity authentication.")
            print("This is the recommended approach for Azure deployments.")
            print("Make sure your Azure Bot Service is configured with msaAppType: 'SystemAssignedMSI'")
    else:
        print("❌ Configuration has errors that need to be resolved")
        return False
    
    print("="*60)
    return True

if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
