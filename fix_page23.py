#!/usr/bin/env python3
"""
Fix Page_23 Analysis - Handle Oversized Image
"""

import os
from pathlib import Path
from streaming_image_analyzer import StreamingImageAnalyzer

def main():
    """Fix Page_23 analysis using the improved analyzer with resizing."""
    print("🔧 FIXING PAGE_23 ANALYSIS")
    print("=" * 40)
    
    # Get OpenRouter API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set your OpenRouter API key:")
        print("export OPENROUTER_API_KEY='your-actual-api-key'")
        print("Get your API key from: https://openrouter.ai/keys")
        return
    
    # Check if Page_23 exists
    page_23_path = Path("pngs/Page_23.png")
    if not page_23_path.exists():
        print(f"❌ Error: {page_23_path} not found")
        return
    
    # Show original problem
    from PIL import Image
    with Image.open(page_23_path) as img:
        width, height = img.size
        print(f"📋 Image: {page_23_path.name}")
        print(f"📏 Original size: {width}x{height} pixels")
        print(f"⚠️  Exceeds 8000px limit (max dimension: {max(width, height)})")
    
    # Create analyzer with resizing capability
    analyzer = StreamingImageAnalyzer(api_key)
    
    print(f"\n🚀 Analyzing Page_23 with automatic resizing...")
    print(f"🔧 Using model: {analyzer.model}")
    
    try:
        # Analyze with automatic resizing
        assessment = analyzer.analyze_image(page_23_path)
        
        # Save the result
        analyzer.save_assessment(assessment)
        
        # Check results
        if "error" in assessment:
            print(f"❌ Analysis failed: {assessment['error']}")
        else:
            print("✅ Analysis completed successfully!")
            
            # Show sample content
            analysis = assessment.get("analysis", {})
            if "page_analysis" in analysis:
                page_analysis = analysis["page_analysis"]
                text_content = page_analysis.get("text_content", "")
                
                if text_content and text_content != "PARSE_ERROR":
                    # Show sample text
                    sample = text_content[:200].replace('\n', ' ').strip()
                    if len(sample) > 200:
                        sample += "..."
                    print(f"📄 Sample content: {sample}")
                    
                    # Show visual elements count
                    visual_elements = page_analysis.get("visual_elements", [])
                    print(f"🖼️  Visual elements found: {len(visual_elements)}")
                    
                    # Show technical specs count
                    tech_specs = page_analysis.get("technical_specifications", [])
                    print(f"📊 Technical specifications: {len(tech_specs)}")
                    
                    print(f"💾 Results saved in: {analyzer.output_dir}")
                    
                else:
                    print(f"⚠️  Analysis returned parse error: {text_content}")
                    if "raw_response" in analysis:
                        raw_response = analysis["raw_response"][:200]
                        print(f"🔍 Raw response preview: {raw_response}...")
            else:
                print(f"❌ Unexpected analysis structure")
                print(f"🔍 Assessment keys: {list(assessment.keys())}")
                
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    main()



