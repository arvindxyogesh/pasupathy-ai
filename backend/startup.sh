#!/bin/bash

# Azure App Service startup script for Flask backend
echo "Starting Pasupathy AI Backend..."

# Get port from Azure (default 8000 if not set)
PORT="${PORT:-8000}"
echo "Port: $PORT"

# Navigate to backend directory
cd /home/site/wwwroot/backend

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start Flask app
echo "Starting Flask application on port $PORT..."
python app.py
