#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Check if API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Please set your OpenRouter API key first:"
    echo "export OPENROUTER_API_KEY='your-actual-api-key'"
    echo "Get your API key from: https://openrouter.ai/keys"
    echo ""
    echo "Then run: ./run_analysis.sh"
    exit 1
fi

# Run the analysis
python analyze_images.py



