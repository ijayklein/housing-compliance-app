#!/usr/bin/env python3
"""
Test Page_23 Resizing Solution
"""

import os
from pathlib import Path
from streaming_image_analyzer import StreamingImageAnalyzer

def main():
    """Test the resizing solution specifically for Page_23."""
    print("🧪 TESTING PAGE_23 RESIZING SOLUTION")
    print("=" * 50)
    
    # Check if Page_23 exists
    page_23_path = Path("pngs/Page_23.png")
    if not page_23_path.exists():
        print(f"❌ Error: {page_23_path} not found")
        return
    
    # Get OpenRouter API key (for full test, but we can test resizing without it)
    api_key = os.environ.get('OPENROUTER_API_KEY', 'dummy-key-for-resize-test')
    
    # Create analyzer
    analyzer = StreamingImageAnalyzer(api_key)
    
    print(f"📋 Testing image: {page_23_path.name}")
    
    # Test 1: Check original dimensions
    from PIL import Image
    with Image.open(page_23_path) as img:
        width, height = img.size
        print(f"📏 Original dimensions: {width}x{height} pixels")
        max_dim = max(width, height)
        print(f"📐 Max dimension: {max_dim} pixels (limit: 8000)")
        
        if max_dim > 8000:
            print("⚠️  Image exceeds size limit - resizing will be triggered")
        else:
            print("✅ Image is within size limits")
    
    # Test 2: Test the resizing function
    print(f"\n🔧 Testing resize function...")
    try:
        resized_path = analyzer.resize_image_if_needed(page_23_path, max_dimension=7500)
        
        if resized_path != page_23_path:
            print(f"✅ Resizing triggered successfully!")
            print(f"📁 Temporary file created: {resized_path}")
            
            # Check new dimensions
            with Image.open(resized_path) as resized_img:
                new_width, new_height = resized_img.size
                print(f"📏 New dimensions: {new_width}x{new_height} pixels")
                
                # Verify it's within limits
                if max(new_width, new_height) <= 7500:
                    print("✅ Resized image is within limits!")
                else:
                    print("❌ Resized image still exceeds limits")
            
            # Clean up temp file
            try:
                resized_path.unlink()
                print("🗑️  Temporary file cleaned up")
            except Exception as e:
                print(f"⚠️  Could not clean up temp file: {e}")
                
        else:
            print("ℹ️  No resizing needed (image already within limits)")
    
    except Exception as e:
        print(f"❌ Error during resize test: {e}")
    
    # Test 3: Test full analysis (if API key available)
    if api_key != 'dummy-key-for-resize-test':
        print(f"\n🚀 Testing full analysis with resizing...")
        try:
            assessment = analyzer.analyze_image(page_23_path)
            
            if "error" in assessment:
                print(f"❌ Analysis failed: {assessment['error']}")
            else:
                print("✅ Analysis completed successfully!")
                
                # Check if we got actual content
                analysis = assessment.get("analysis", {})
                if "page_analysis" in analysis:
                    text_content = analysis["page_analysis"].get("text_content", "")
                    if text_content and text_content != "PARSE_ERROR":
                        sample = text_content[:100].replace('\n', ' ')
                        print(f"📄 Sample content: {sample}...")
                    else:
                        print(f"⚠️  Analysis returned parse error or empty content")
                        
        except Exception as e:
            print(f"❌ Error during full analysis: {e}")
    else:
        print(f"\nℹ️  Skipping full analysis test (no API key)")
        print(f"   Set OPENROUTER_API_KEY to test complete functionality")

if __name__ == "__main__":
    main()



