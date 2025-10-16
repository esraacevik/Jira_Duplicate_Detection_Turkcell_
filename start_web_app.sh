#!/bin/bash

# =============================================
# Bug Report Web Application Starter
# =============================================

echo "=================================="
echo "🚀 BUG REPORT WEB APPLICATION"
echo "=================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📥 Installing Flask dependencies..."
    pip install flask flask-cors
fi

# Start API server
echo ""
echo "=================================="
echo "🔥 Starting API Server..."
echo "=================================="
echo ""

python api_server.py

