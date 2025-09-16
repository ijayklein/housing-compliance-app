#!/bin/bash

# Housing Compliance Web Application Startup Script

echo "🌐 Starting Housing Compliance Web Application..."
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📥 Installing Flask..."
    pip install Flask==3.0.0
fi

# Check if reverse_compliance_validator.py exists
if [ ! -f "reverse_compliance_validator.py" ]; then
    echo "❌ reverse_compliance_validator.py not found!"
    echo "   This file is required for the validation engine."
    exit 1
fi

# Check if rules extraction directory exists
if [ ! -d "rules_extraction_v3_20250916_161035" ]; then
    echo "❌ Rules extraction directory not found!"
    echo "   Please ensure the rules have been extracted."
    exit 1
fi

echo "🚀 Starting Flask application..."
echo "📍 Access the application at: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
