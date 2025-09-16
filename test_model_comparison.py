#!/usr/bin/env python3
"""
Test Different Models with Complex Prompt
"""

import os
from pathlib import Path
from streaming_image_analyzer_v1 import StreamingImageAnalyzer

def test_model(model_name, image_path, api_key):
    """Test a specific model with the complex prompt."""
    print(f"\n🧪 Testing {model_name}...")
    
    # Create temporary analyzer instance
    analyzer = StreamingImageAnalyzer(api_key)
    analyzer.model = model_name
    
    try:
        assessment = analyzer.analyze_image(image_path)
        
        if "error" in assessment:
            print(f"❌ {model_name}: Analysis failed - {assessment['error']}")
            return False
        
        analysis = assessment.get("analysis", {})
        if "page_analysis" in analysis:
            page_analysis = analysis["page_analysis"]
            text_content = page_analysis.get("text_content", "")
            
            if text_content and text_content != "PARSE_ERROR":
                print(f"✅ {model_name}: SUCCESS!")
                
                # Show metrics
                visual_elements = len(page_analysis.get("visual_elements", []))
                tech_specs = len(page_analysis.get("technical_specifications", []))
                conditions = len(page_analysis.get("conditions_and_qualifiers", {}).get("conditions", []))
                qualifiers = len(page_analysis.get("conditions_and_qualifiers", {}).get("qualifiers", []))
                
                print(f"   📊 Visual elements: {visual_elements}")
                print(f"   📊 Technical specs: {tech_specs}")
                print(f"   📊 Conditions: {conditions}")
                print(f"   📊 Qualifiers: {qualifiers}")
                
                sample = text_content[:100].replace('\n', ' ')
                print(f"   📄 Sample: {sample}...")
                return True
            else:
                print(f"❌ {model_name}: Parse error - {text_content}")
                if "raw_response" in analysis:
                    raw = analysis["raw_response"][:100]
                    print(f"   🔍 Raw response: {raw}...")
                return False
        else:
            print(f"❌ {model_name}: Unexpected structure")
            return False
            
    except Exception as e:
        print(f"❌ {model_name}: Exception - {e}")
        return False

def main():
    print("🔬 MODEL COMPARISON TEST")
    print("=" * 40)
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key or len(api_key) < 50:
        print("❌ Need valid API key")
        return
    
    # Test with Page_08 (was failing)
    test_image = Path("pngs/Page_08.png")
    if not test_image.exists():
        print(f"❌ {test_image} not found")
        return
    
    print(f"🎯 Testing with: {test_image.name}")
    print(f"📋 Complex prompt with conditions/qualifiers schema")
    
    # Models to test (in order of preference)
    models_to_test = [
        "openai/gpt-4o",                    # Best OpenAI model
        "openai/gpt-4.1-mini",             # Current model (having issues)
        "anthropic/claude-3.5-sonnet",     # Excellent for complex tasks
        "google/gemini-2.5-pro",           # Good for detailed analysis
        "google/gemini-2.5-flash"          # Faster alternative
    ]
    
    results = {}
    
    for model in models_to_test:
        try:
            success = test_model(model, test_image, api_key)
            results[model] = success
        except Exception as e:
            print(f"❌ {model}: Failed to test - {e}")
            results[model] = False
    
    print(f"\n📊 RESULTS SUMMARY:")
    print("=" * 40)
    
    successful_models = []
    failed_models = []
    
    for model, success in results.items():
        if success:
            print(f"✅ {model}")
            successful_models.append(model)
        else:
            print(f"❌ {model}")
            failed_models.append(model)
    
    print(f"\n🎯 RECOMMENDATIONS:")
    if successful_models:
        print(f"✅ Use one of these models for your complex schema:")
        for model in successful_models:
            print(f"   • {model}")
    else:
        print(f"⚠️  All models had issues. Consider simplifying the prompt.")
    
    if "openai/gpt-4.1-mini" in failed_models:
        print(f"\n💡 GPT-4.1-mini is struggling with your complex prompt.")
        print(f"   Consider upgrading to GPT-4o or Claude-3.5-Sonnet for better results.")

if __name__ == "__main__":
    main()

