#!/bin/bash
# Azure App Service startup script for Python Flask app

# Activate virtual environment if it exists
if [ -d "antenv" ]; then
    source antenv/bin/activate
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Start the Flask app with gunicorn for production
export FLASK_ENV=production
gunicorn app:app --bind=0.0.0.0:8000
