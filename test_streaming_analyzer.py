#!/usr/bin/env python3
"""
Test Streaming Image Analyzer - For Page_08 and Page_33
"""

import os
import sys
from pathlib import Path

# Import the streaming analyzer
# Import the fixed streaming analyzer
from streaming_image_analyzer import StreamingImageAnalyzer

def main():
    """Test the streaming analyzer with Page_08 and Page_33."""
    print("🧪 TESTING STREAMING IMAGE ANALYZER")
    print("=" * 50)
    
    # Get OpenRouter API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set your OpenRouter API key:")
        print("export OPENROUTER_API_KEY='your-actual-api-key'")
        print("Get your API key from: https://openrouter.ai/keys")
        return
    
    # Define test images
    base_path = Path(__file__).parent / "pngs"
    test_images = [
        base_path / "Page_08.png",
        base_path / "Page_33.png"
    ]
    
    # Verify images exist
    missing_images = []
    for img_path in test_images:
        if not img_path.exists():
            missing_images.append(str(img_path))
    
    if missing_images:
        print(f"❌ Error: Missing test images:")
        for img in missing_images:
            print(f"   • {img}")
        return
    
    # Create analyzer
    analyzer = StreamingImageAnalyzer(api_key)
    
    # Configuration for testing
    max_concurrent = 2  # Small number for testing
    
    print(f"🎯 Testing with {len(test_images)} images")
    print(f"⚡ Using {max_concurrent} concurrent requests")
    print(f"📋 Test images:")
    for img in test_images:
        print(f"   • {img.name}")
    
    print(f"\n🚀 Starting test analysis...")
    
    try:
        # Run streaming analysis
        analyzer.analyze_images_streaming(test_images, max_concurrent=max_concurrent)
        
        print("\n✅ Test completed successfully!")
        print(f"📂 Results saved in: {analyzer.output_dir}")
        
        # Show result files
        result_files = list(Path(analyzer.output_dir).glob("*.json"))
        print(f"📄 Created {len(result_files)} result files:")
        for file in result_files:
            print(f"   • {file.name}")
        
    except KeyboardInterrupt:
        print(f"\n⏸️  Test interrupted by user.")
        print(f"📂 Partial results in: {analyzer.output_dir}")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        print(f"📂 Partial results may be in: {analyzer.output_dir}")

if __name__ == "__main__":
    main()
