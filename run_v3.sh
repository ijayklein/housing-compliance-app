#!/bin/bash

# Script to run the improved streaming image analyzer v3
# with proper virtual environment activation

echo "🚀 Starting Streaming Image Analyzer v3 (Enhanced JSON Parsing)"
echo "=" * 60

# Activate virtual environment
source venv/bin/activate

# Check if API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ Error: OPENROUTER_API_KEY environment variable not set"
    echo ""
    echo "Please set your OpenRouter API key first:"
    echo "export OPENROUTER_API_KEY='your-actual-api-key'"
    echo ""
    echo "Get your API key from: https://openrouter.ai/keys"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ API key found"
echo "🔧 Key improvements in v3:"
echo "   • Increased token limit: 4000 → 8000"
echo "   • Better JSON truncation handling"
echo "   • Simplified schema for efficiency"
echo "   • Enhanced error recovery"
echo ""

# Run the analyzer
python streaming_image_analyzer_v3.py

echo ""
echo "🎯 Analysis complete! Check the output directory for results."
