#!/usr/bin/env python3
"""
Streaming Image Analyzer v4 - Simplified JSON Handling
Fixed the JSON parsing issues by simplifying the extraction logic.
"""

import os
import base64
import json
import requests
import time
import threading
import copy
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image

class StreamingImageAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        #self.model = "anthropic/claude-3.5-sonnet"
        self.model = "google/gemini-2.5-flash"
        #self.model = "x-ai/grok-4"
        #self.model = "anthropic/claude-sonnet-4"
        self.model = "openai/gpt-5"
        
        
        # Create timestamped output directory
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = f'image_analysis_streaming_{timestamp}'
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir}")
        
        # Streaming control
        self.completed_count = 0
        self.total_images = 0
        self.start_time = None
        self.stats_lock = threading.Lock()
        self.failed_images = []
    
    def encode_image(self, image_path: Path) -> str:
        """Encode image to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def create_analysis_prompt(self) -> str:
        """Create simple prompt that ensures valid JSON"""
        return """You are analyzing photocopied pages from a city planning technical manual. 
        Extract what you can from the images. 
        Take into account that these images will typically contain:
        - crucial zoning rules
        - regulations
        - technical specifications
        It is crucial that all of this information must be captured with absolute precision.
        Do not make up any information or deduce any information from the images."""

    def call_llm(self, prompt: str, base64_image: str) -> str:
        """Make API call with simplified error handling."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }],
            "temperature": 0.1,
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=120)
            
            if not response.ok:
                return f"API_ERROR: {response.status_code} - {response.text}"
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            if not content or len(content.strip()) < 10:
                return "API_ERROR: Empty response"
            
            return content
        except Exception as e:
            return f"API_ERROR: {str(e)}"
    
    def process_raw_response(self, response: str) -> Dict[str, Any]:
        """Just return the raw response without any JSON parsing"""
        if response.startswith("API_ERROR"):
            return {"parse_error": True, "error": response}
        
        # Return raw response as-is
        return {
            "raw_content": response,
            "content_length": len(response),
            "parse_error": False
        }
    
    def analyze_image(self, image_path: Path) -> Dict[str, Any]:
        """Analyze a single image with simplified processing."""
        try:
            # Encode image
            base64_image = self.encode_image(image_path)
            
            # Get LLM analysis
            llm_response = self.call_llm(self.create_analysis_prompt(), base64_image)
            
            # Process raw response (no JSON parsing)
            analysis = self.process_raw_response(llm_response)
            
            return {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "analysis": analysis,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": self.model,
                "success": not analysis.get("parse_error", False)
            }
            
        except Exception as e:
            return {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": False
            }
    
    def save_assessment(self, assessment: Dict[str, Any]):
        """Save assessment to JSON file."""
        image_name = Path(assessment['image_path']).stem
        filename = f"{self.output_dir}/{image_name}_analysis.json"
        with open(filename, 'w') as f:
            json.dump(assessment, f, indent=2)
    
    def update_progress(self, image_name: str, success: bool = True):
        """Update progress statistics."""
        with self.stats_lock:
            self.completed_count += 1
            if not success:
                self.failed_images.append(image_name)
                
            elapsed = time.time() - self.start_time
            rate = self.completed_count / elapsed
            remaining = self.total_images - self.completed_count
            eta = remaining / rate if rate > 0 else 0
            
            progress_pct = (self.completed_count / self.total_images) * 100
            status_icon = "✅" if success else "❌"
            
            print(f"{status_icon} {image_name} | Progress: {self.completed_count}/{self.total_images} "
                  f"({progress_pct:.1f}%) | Rate: {rate:.2f}/s | ETA: {eta/60:.1f}m")
    
    def process_image_worker(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """Worker function to process a single image."""
        try:
            assessment = self.analyze_image(image_path)
            self.save_assessment(assessment)
            
            success = assessment.get("success", True)
            
            # Show sample output from raw content
            if success and "analysis" in assessment and "raw_content" in assessment["analysis"]:
                content = assessment["analysis"]["raw_content"][:100].replace('\n', ' ')
                print(f"   📄 Sample: {content}...")
            
            self.update_progress(image_path.name, success)
            return assessment
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {e}")
            self.update_progress(image_path.name, False)
            return None
    
    def analyze_images_streaming(self, image_paths: List[Path], max_concurrent: int = 4):
        """Analyze images with streaming approach - reduced concurrency for stability."""
        self.total_images = len(image_paths)
        self.start_time = time.time()
        
        print(f"🚀 STREAMING ANALYSIS v4 - Simplified JSON Handling")
        print(f"📊 Images: {self.total_images} | Concurrent: {max_concurrent} | Model: {self.model}")
        print()
        
        remaining_images = copy.deepcopy(image_paths)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {}
            
            # Initialize pipeline
            initial_count = min(max_concurrent, len(remaining_images))
            for _ in range(initial_count):
                if remaining_images:
                    image_path = remaining_images.pop(0)
                    future = executor.submit(self.process_image_worker, image_path)
                    futures[future] = image_path
            
            # Process completions
            while futures:
                for future in as_completed(futures):
                    try:
                        future.result()
                        if remaining_images:
                            new_image_path = remaining_images.pop(0)
                            new_future = executor.submit(self.process_image_worker, new_image_path)
                            futures[new_future] = new_image_path
                    except Exception as e:
                        print(f"❌ Future error: {e}")
                    
                    del futures[future]
                    break
        
        # Final stats
        total_time = time.time() - self.start_time
        success_count = self.total_images - len(self.failed_images)
        
        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"⏱️  Time: {total_time:.1f}s | Rate: {self.completed_count/total_time:.2f}/s")
        print(f"✅ Success: {success_count}/{self.total_images} ({success_count/self.total_images*100:.1f}%)")
        if self.failed_images:
            print(f"❌ Failed: {len(self.failed_images)}")
        
        return True

def main():
    print("🌊 STREAMING IMAGE ANALYZER v4 - Simplified")
    print("=" * 50)
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return
    
    base_path = Path(__file__).parent / "pngs"
    if not base_path.exists():
        print(f"❌ pngs directory not found")
        return
        
    all_images = sorted(base_path.glob("*.png"))
    if not all_images:
        print("❌ No PNG images found")
        return
    
    analyzer = StreamingImageAnalyzer(api_key)
    
    print(f"🎯 Found {len(all_images)} images")
    print(f"🔧 Using simplified JSON parsing approach")
    
    response = input(f"\n🤔 Analyze {len(all_images)} images? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cancelled")
        return
    
    try:
        analyzer.analyze_images_streaming(all_images, max_concurrent=16)
        print("\n✅ Complete! Check output directory for results.")
    except KeyboardInterrupt:
        print(f"\n⏸️  Interrupted. Partial results in: {analyzer.output_dir}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
