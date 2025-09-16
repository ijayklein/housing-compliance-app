#!/usr/bin/env python3
"""
Test OpenRouter API Connection
"""

import os
import requests
import json

def test_openrouter_api():
    """Test if the OpenRouter API key is working."""
    print("🔑 TESTING OPENROUTER API")
    print("=" * 30)
    
    # Get API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        return False
    
    # Check key format
    print(f"📋 API Key length: {len(api_key)} characters")
    print(f"📋 Key starts with: {api_key[:15]}...")
    
    if len(api_key) < 20:
        print("⚠️  Warning: API key seems too short (should be 50+ characters)")
    
    if not api_key.startswith('sk-or-'):
        print("⚠️  Warning: OpenRouter keys typically start with 'sk-or-'")
    
    # Test API call
    print(f"\n🚀 Testing API connection...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/cityrules-analyzer",
        "X-Title": "API Test"
    }
    
    # Simple text completion test (cheaper than image analysis)
    data = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {
                "role": "user",
                "content": "Say 'API test successful' in exactly those words."
            }
        ],
        "max_tokens": 10,
        "temperature": 0
    }
    
    try:
        print("📡 Making test API call...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"✅ API test successful!")
                print(f"📝 Response: {content}")
                
                # Show usage info if available
                if 'usage' in result:
                    usage = result['usage']
                    print(f"💰 Tokens used: {usage.get('total_tokens', 'unknown')}")
                
                return True
            else:
                print(f"❌ Unexpected response structure: {result}")
                return False
                
        elif response.status_code == 401:
            print(f"❌ Authentication failed (401)")
            print(f"🔍 This usually means the API key is invalid")
            try:
                error_detail = response.json()
                print(f"📋 Error details: {error_detail}")
            except:
                print(f"📋 Raw response: {response.text}")
            return False
            
        elif response.status_code == 429:
            print(f"❌ Rate limited (429)")
            print(f"🔍 Too many requests - wait a moment and try again")
            return False
            
        else:
            print(f"❌ API call failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📋 Error details: {error_detail}")
            except:
                print(f"📋 Raw response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    success = test_openrouter_api()
    
    if success:
        print(f"\n🎉 API test passed!")
        print(f"✅ You can now run the image analysis safely:")
        print(f"   ./run_streaming_analysis.sh")
    else:
        print(f"\n❌ API test failed!")
        print(f"🔧 Please check your API key and try again.")
        print(f"💡 Get a key from: https://openrouter.ai/keys")

if __name__ == "__main__":
    main()



