#!/usr/bin/env python3
"""
Working Test - Process Page_08 and Page_33 without getting stuck
"""

import os
import base64
import json
import requests
import tempfile
from pathlib import Path
from PIL import Image

def process_image(image_path):
    """Process image with resizing if needed."""
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Check if resizing needed
        if max(width, height) > 7500:
            print(f"   📏 Resizing {image_path.name} from {width}x{height}")
            if width > height:
                new_width = 7500
                new_height = int((height * 7500) / width)
            else:
                new_height = 7500
                new_width = int((width * 7500) / height)
            
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save as JPEG for better compression
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            resized_img.convert('RGB').save(temp_file.name, 'JPEG', quality=85, optimize=True)
            temp_file.close()
            
            file_size = Path(temp_file.name).stat().st_size
            print(f"   ✅ Resized to {new_width}x{new_height}, size: {file_size/1024/1024:.1f}MB")
            return Path(temp_file.name)
        else:
            print(f"   ✅ {image_path.name} is {width}x{height} (no resize needed)")
            return image_path

def analyze_image(image_path, api_key):
    """Analyze single image with simple approach."""
    print(f"\n📄 Analyzing {image_path.name}...")
    
    # Process image (resize if needed)
    processed_path = process_image(image_path)
    temp_file_created = processed_path != image_path
    
    try:
        # Encode image
        with open(processed_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        # Simple prompt
        prompt = """Analyze this city planning document page. Extract:
1. Main heading/title
2. Key text content (first 100 words)
3. Any figures or diagrams described briefly
4. Technical specifications or measurements

Keep response concise and structured."""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        print("   🚀 Making API call...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"   ✅ SUCCESS!")
                # Show first 150 chars as sample
                sample = content.replace('\n', ' ')[:150]
                print(f"   📝 Sample: {sample}...")
                return {"status": "success", "content": content}
            else:
                print(f"   ❌ Unexpected response structure")
                return {"status": "error", "error": "Unexpected response"}
        else:
            print(f"   ❌ API Error: {response.status_code}")
            return {"status": "error", "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        # Cleanup temp file
        if temp_file_created and processed_path.exists():
            processed_path.unlink()

def main():
    print("🧪 WORKING TEST - PAGE_08 & PAGE_33")
    print("=" * 40)
    
    # Check API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key or len(api_key) < 50:
        print("❌ Need valid API key")
        return
    
    # Test images
    test_images = [
        Path("pngs/Page_08.png"),
        Path("pngs/Page_33.png")
    ]
    
    # Check images exist
    for img in test_images:
        if not img.exists():
            print(f"❌ {img} not found")
            return
    
    print(f"🎯 Testing {len(test_images)} images...")
    
    results = {}
    success_count = 0
    
    for image_path in test_images:
        result = analyze_image(image_path, api_key)
        results[image_path.name] = result
        if result["status"] == "success":
            success_count += 1
    
    print(f"\n🎉 RESULTS:")
    print(f"✅ Successful: {success_count}/{len(test_images)}")
    print(f"❌ Failed: {len(test_images) - success_count}/{len(test_images)}")
    
    if success_count == len(test_images):
        print(f"\n🚀 All tests passed! Your system is ready for full analysis.")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()



