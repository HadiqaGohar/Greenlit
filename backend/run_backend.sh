#!/bin/bash

# 🎬 Greenlit AI Backend Runner
# Quick setup and run script for development

echo "🎬 Greenlit AI Backend Setup & Run"
echo "=================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found! Please create it with your API keys."
    exit 1
fi

# Run the FastAPI server
echo "🚀 Starting Greenlit AI backend server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start uvicorn server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info