#!/usr/bin/env python3
"""
Simple Page_23 Test - No Complex JSON Parsing
"""

import os
import base64
import json
import requests
import tempfile
from pathlib import Path
from PIL import Image

def resize_and_compress_image(image_path):
    """Resize and compress Page_23 to meet API limits."""
    print(f"📏 Processing {image_path.name}...")
    
    with Image.open(image_path) as img:
        width, height = img.size
        print(f"   Original: {width}x{height} pixels")
        
        # Resize to 7500px max dimension
        if max(width, height) > 7500:
            if width > height:
                new_width = 7500
                new_height = int((height * 7500) / width)
            else:
                new_height = 7500
                new_width = int((width * 7500) / height)
            
            print(f"   Resizing to: {new_width}x{new_height}")
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            resized_img = img
            new_width, new_height = width, height
        
        # Save as JPEG with compression
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        resized_img.convert('RGB').save(temp_file.name, 'JPEG', quality=85, optimize=True)
        temp_file.close()
        
        # Check file size
        file_size = Path(temp_file.name).stat().st_size
        print(f"   File size: {file_size/1024/1024:.1f}MB")
        
        if file_size > 4*1024*1024:  # 4MB
            print(f"   Compressing further...")
            for quality in [75, 65, 55]:
                resized_img.convert('RGB').save(temp_file.name, 'JPEG', quality=quality, optimize=True)
                file_size = Path(temp_file.name).stat().st_size
                if file_size <= 4*1024*1024:
                    print(f"   ✅ Compressed to {file_size/1024/1024:.1f}MB at quality {quality}")
                    break
        
        return Path(temp_file.name)

def test_api_call(image_path, api_key):
    """Make a simple API call without complex JSON parsing."""
    
    # Encode image
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode('utf-8')
    
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
                    {
                        "type": "text",
                        "text": "Describe this city planning document page in 2-3 sentences. What does it show?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200,
        "temperature": 0.1
    }
    
    print("🚀 Making API call...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=60
    )
    
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            print(f"✅ SUCCESS!")
            print(f"📝 Response: {content}")
            return True
        else:
            print(f"❌ Unexpected response structure")
            return False
    else:
        print(f"❌ API Error: {response.status_code}")
        try:
            error = response.json()
            print(f"📋 Details: {error}")
        except:
            print(f"📋 Raw: {response.text[:200]}")
        return False

def main():
    print("🧪 SIMPLE PAGE_23 TEST")
    print("=" * 30)
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key or len(api_key) < 50:
        print("❌ Need valid API key")
        return
    
    page_23 = Path("pngs/Page_23.png")
    if not page_23.exists():
        print(f"❌ {page_23} not found")
        return
    
    try:
        # Step 1: Resize and compress
        processed_image = resize_and_compress_image(page_23)
        
        # Step 2: Test API call
        success = test_api_call(processed_image, api_key)
        
        if success:
            print(f"\n🎉 Page_23 analysis works!")
        else:
            print(f"\n❌ Still having issues")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup
        if 'processed_image' in locals() and processed_image.exists():
            processed_image.unlink()
            print("🗑️ Cleaned up temp file")

if __name__ == "__main__":
    main()



