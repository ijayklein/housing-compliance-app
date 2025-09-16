#!/bin/bash

echo "🌊 STREAMING CITY PLANNING IMAGE ANALYZER"
echo "=========================================="

# Activate virtual environment
source venv/bin/activate

# Check if API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ Please set your OpenRouter API key first:"
    echo "export OPENROUTER_API_KEY='your-actual-api-key'"
    echo "Get your API key from: https://openrouter.ai/keys"
    echo ""
    echo "Then run: ./run_streaming_analysis.sh"
    exit 1
fi

echo "🔑 API key found"
echo "🎯 Choose analysis mode:"
echo "1) OLD VERSION:Analyze all images in pngs/ directory"
echo "2) NEW VERSION:Analyze all images in pngs/ directory"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo "🧪 Running OLD analysis..."
        python streaming_image_analyzer.py
        ;;
    2)
        echo "🚀 Running NEW analysis..."
        python streaming_image_analyzer_v3.py
        ;;
    *)
        echo "❌ Invalid choice. Please run again and select 1 or 2."
        exit 1
        ;;
esac



