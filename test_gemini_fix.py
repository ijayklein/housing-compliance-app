#!/usr/bin/env python3
"""
Test Gemini Parse Error Fix
"""

import os
from pathlib import Path
from streaming_image_analyzer import StreamingImageAnalyzer

def main():
    print("🔧 TESTING GEMINI PARSE ERROR FIX")
    print("=" * 40)
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key or len(api_key) < 50:
        print("❌ Need valid API key")
        return
    
    # Test with Page_08 (had parse error)
    page_08 = Path("pngs/Page_08.png")
    if not page_08.exists():
        print(f"❌ {page_08} not found")
        return
    
    analyzer = StreamingImageAnalyzer(api_key)
    print(f"🎯 Testing {page_08.name} with Gemini model: {analyzer.model}")
    print(f"📊 Max tokens: 8000 (increased for verbose responses)")
    
    try:
        assessment = analyzer.analyze_image(page_08)
        
        if "error" in assessment:
            print(f"❌ Analysis failed: {assessment['error']}")
        else:
            analysis = assessment.get("analysis", {})
            if "page_analysis" in analysis:
                page_analysis = analysis["page_analysis"]
                text_content = page_analysis.get("text_content", "")
                
                if text_content and text_content != "PARSE_ERROR":
                    print("✅ SUCCESS! No parse error")
                    sample = text_content[:150].replace('\n', ' ')
                    print(f"📄 Sample: {sample}...")
                    
                    # Show counts
                    visual_elements = page_analysis.get("visual_elements", [])
                    tech_specs = page_analysis.get("technical_specifications", [])
                    print(f"🖼️  Visual elements: {len(visual_elements)}")
                    print(f"📊 Technical specs: {len(tech_specs)}")
                    
                else:
                    print(f"❌ Still getting parse error")
                    if "raw_response" in analysis:
                        raw = analysis["raw_response"]
                        print(f"🔍 Response length: {len(raw)} chars")
                        print(f"🔍 Ends with: ...{raw[-50:]}")
                        
        # Save result
        analyzer.save_assessment(assessment)
        print(f"💾 Result saved in: {analyzer.output_dir}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    main()



