#!/usr/bin/env python3
"""
Simple reprocessing script - one file at a time
"""

import os
import json
import requests
import time
from pathlib import Path

def process_single_file(filename: str):
    """Process a single markdown file"""
    print(f"Processing {filename}...")
    
    # API setup
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return False
    
    # Load extraction prompt
    try:
        with open("promptforextraction.txt", 'r') as f:
            extraction_prompt = f.read().strip()
    except:
        print("❌ Could not load prompt")
        return False
    
    # Read markdown file
    md_path = Path("markdown_pages") / filename
    if not md_path.exists():
        print(f"❌ {filename} not found")
        return False
    
    with open(md_path, 'r') as f:
        markdown_content = f.read()
    
    # Create prompt
    prompt = f"""{extraction_prompt}

## Input Text to Analyze:

{markdown_content}

## Instructions:
Analyze the above text and extract all rules/regulations according to the schema. 
Return ONLY valid JSON. No markdown formatting, no explanations, just pure JSON."""
    
    # API call
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "openai/gpt-4o",  # More stable than gpt-5
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 6000
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=data, 
            timeout=60
        )
        
        if not response.ok:
            print(f"❌ API Error: {response.status_code}")
            return False
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Try to parse JSON
        try:
            # Clean up content
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    json_str = content[start:end].strip()
                else:
                    json_str = content[start:].strip()
            elif content.startswith('[') or content.startswith('{'):
                json_str = content
            else:
                # Find first bracket
                start = max(content.find('['), content.find('{'))
                if start == -1:
                    print(f"❌ No JSON found in response")
                    return False
                json_str = content[start:]
            
            parsed_json = json.loads(json_str)
            
            # Save result
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_dir = f"rules_reprocessed_{timestamp}"
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = Path(output_dir) / f"{md_path.stem}_rules.json"
            
            final_result = {
                "file_path": str(md_path),
                "file_name": filename,
                "analysis": {
                    "extracted_rules": parsed_json,
                    "parse_error": False,
                    "raw_response": content
                },
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": "openai/gpt-4o",
                "success": True
            }
            
            with open(output_file, 'w') as f:
                json.dump(final_result, f, indent=2)
            
            rule_count = len(parsed_json) if isinstance(parsed_json, list) else 1
            print(f"✅ {filename}: {rule_count} rules extracted")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    failed_files = [
        'Page_11.md', 'Page_08.md', 'Page_18.md', 'Page_30.md', 'Page_29.md', 
        'Page_37.md', 'Page_36.md', 'Page_40.md', 'Page_39.md', 'Page_45.md', 
        'Page_48.md', 'Page_50.md', 'Page_49.md'
    ]
    
    print(f"Reprocessing {len(failed_files)} files...")
    
    success = 0
    for filename in failed_files:
        if process_single_file(filename):
            success += 1
        time.sleep(2)  # Rate limiting
        print()
    
    print(f"Complete: {success}/{len(failed_files)} successful")
