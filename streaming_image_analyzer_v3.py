#!/usr/bin/env python3
"""
Streaming Image Analyzer v3 - Enhanced JSON Parsing & Error Handling
Fixes common parsing errors and improves prompt structure for better LLM responses.
"""

import os
import base64
import json
import requests
import time
import threading
import copy
import tempfile
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional
from queue import Queue, Empty
from PIL import Image

class StreamingImageAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet"  # More reliable for JSON
        #self.model = "google/gemini-2.0-flash-exp"  
        #self.model = "openai/gpt-4.1-mini"
        
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
        
    def resize_image_if_needed(self, image_path: Path, max_dimension: int = 7500) -> Path:
        """
        Resize image if either dimension exceeds max_dimension.
        Returns path to resized image (temporary file) or original path if no resize needed.
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check if resizing is needed
                if width <= max_dimension and height <= max_dimension:
                    return image_path
                
                print(f"   📏 Resizing {image_path.name} from {width}x{height} (exceeds {max_dimension}px limit)")
                
                # Calculate new dimensions maintaining aspect ratio
                if width > height:
                    new_width = max_dimension
                    new_height = int((height * max_dimension) / width)
                else:
                    new_height = max_dimension
                    new_width = int((width * max_dimension) / height)
                
                # Create resized image
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save to temporary file with compression
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                resized_img.convert('RGB').save(temp_file.name, 'JPEG', quality=85, optimize=True)
                temp_file.close()
                
                # Check file size and compress more if needed
                file_size = Path(temp_file.name).stat().st_size
                max_size = 4 * 1024 * 1024  # 4MB to be safe (under 5MB limit)
                
                if file_size > max_size:
                    print(f"   📦 File still {file_size/1024/1024:.1f}MB, compressing further...")
                    # Try lower quality
                    for quality in [75, 65, 55, 45]:
                        resized_img.convert('RGB').save(temp_file.name, 'JPEG', quality=quality, optimize=True)
                        file_size = Path(temp_file.name).stat().st_size
                        if file_size <= max_size:
                            print(f"   ✅ Compressed to {file_size/1024/1024:.1f}MB at quality {quality}")
                            break
                    else:
                        print(f"   ⚠️  Still {file_size/1024/1024:.1f}MB after compression")
                else:
                    print(f"   📦 File size: {file_size/1024/1024:.1f}MB (within limits)")
                
                print(f"   ✅ Resized to {new_width}x{new_height}, saved as temp file")
                return Path(temp_file.name)
                
        except Exception as e:
            print(f"   ❌ Error resizing image {image_path.name}: {e}")
            return image_path
    
    def encode_image(self, image_path: Path) -> str:
        """Encode image to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def create_analysis_prompt(self) -> str:
        """Create simplified prompt that reduces truncation risk"""
        return """Extract text from this city planning manual page.

Return ONLY valid JSON (no markdown, no extra text):

{
  "page": "page number",
  "heading": "main heading",
  "content": "all text on page",
  "figures": ["Fig 1: caption", "Fig 2: caption"],
  "tables": ["table data as text"],
  "codes": ["18.12.040", "Table 2"]
}

Extract everything visible. Keep JSON valid and complete."""

    def extract_json_from_response(self, response: str) -> str:
        """Enhanced JSON extraction with multiple fallback strategies"""
        if not response or response.strip() == "":
            raise ValueError("Empty response")
        
        # Remove any markdown code blocks
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        elif response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        # Check for mostly whitespace responses
        non_whitespace = ''.join(response.split())
        if len(non_whitespace) < 20:
            raise ValueError(f"Response contains mostly whitespace. Non-whitespace chars: {len(non_whitespace)}")
        
        # Try to find JSON object boundaries
        first_brace = response.find('{')
        if first_brace == -1:
            raise ValueError("No opening brace found in response")
        
        # Find the matching closing brace
        brace_count = 0
        last_brace = -1
        for i, char in enumerate(response[first_brace:], first_brace):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    last_brace = i
                    break
        
        if last_brace == -1:
            # Handle incomplete JSON (common with token limits)
            response = response[first_brace:]
            
            # Find the last complete field by looking for properly closed strings
            lines = response.split('\n')
            complete_lines = []
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Skip empty lines
                if not stripped:
                    complete_lines.append(line)
                    continue
                
                # Check if this line looks incomplete (truncated text content)
                if '":' in stripped:
                    # This is a field line, check if it's complete
                    if not (stripped.endswith('"') or stripped.endswith('",') or 
                           stripped.endswith('}') or stripped.endswith('],') or
                           stripped.endswith(']')):
                        # This line is incomplete, but check if it's a string that got cut off
                        if stripped.count('"') % 2 == 1:  # Odd number of quotes = incomplete string
                            # Try to close the string properly
                            if not stripped.endswith('"'):
                                line = line.rstrip() + '"'
                                complete_lines.append(line)
                        break  # Stop processing after fixing this line
                    else:
                        complete_lines.append(line)
                else:
                    # Not a field line, probably part of a value
                    complete_lines.append(line)
            
            response = '\n'.join(complete_lines)
            
            # Clean up and ensure proper JSON structure
            response = response.rstrip().rstrip(',')
            
            # Count braces and brackets for proper closing
            open_braces = response.count('{')
            close_braces = response.count('}')
            open_brackets = response.count('[')
            close_brackets = response.count(']')
            
            # Close any open arrays first
            missing_brackets = open_brackets - close_brackets
            if missing_brackets > 0:
                response += ']' * missing_brackets
            
            # Close any open objects
            missing_braces = open_braces - close_braces
            if missing_braces > 0:
                response += '}' * missing_braces
        else:
            response = response[first_brace:last_brace + 1]
        
        return response
    
    def fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues"""
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix unescaped quotes in strings (basic fix)
        # This is a simple fix - for more complex cases, you'd need a proper parser
        json_str = re.sub(r'(?<!\\)"(?=.*".*:)', r'\\"', json_str)
        
        # Ensure proper string termination
        lines = json_str.split('\n')
        fixed_lines = []
        for line in lines:
            # Skip lines that look incomplete (no proper ending)
            if '":' in line and not (line.rstrip().endswith('"') or 
                                   line.rstrip().endswith(',') or
                                   line.rstrip().endswith('}') or
                                   line.rstrip().endswith(']')):
                # Try to close the string properly
                if line.count('"') % 2 == 1:  # Odd number of quotes
                    line = line.rstrip() + '"'
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

    def call_llm(self, prompt: str, base64_image: str, retry_count: int = 0) -> str:
        """Make API call to OpenRouter for image analysis with enhanced error handling."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/cityrules-analyzer",
            "X-Title": "City Planning Rule Image Analyzer"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 8000  # Increased for detailed page analysis
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=180)
            
            if not response.ok:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                # Retry once for certain error codes
                if retry_count == 0 and response.status_code in [429, 500, 502, 503, 504]:
                    print(f"   🔄 Retrying due to {response.status_code} error...")
                    time.sleep(2)
                    return self.call_llm(prompt, base64_image, retry_count + 1)
                return error_msg
            
            try:
                result = response.json()
                if 'choices' not in result or len(result['choices']) == 0:
                    return f"API Response Error: Invalid response structure: {result}"
                
                content = result['choices'][0]['message']['content']
                
                # Enhanced empty response detection
                if not content or len(content.strip()) < 10:
                    if retry_count == 0:
                        print(f"   🔄 Retrying due to empty response...")
                        time.sleep(1)
                        return self.call_llm(prompt, base64_image, retry_count + 1)
                    return f"API Response Error: Empty response after retry. Content length: {len(content) if content else 0}"
                
                return content
                
            except json.JSONDecodeError as e:
                return f"API Response Parse Error: Failed to parse JSON response: {str(e)} - Response: {response.text[:500]}"
                
        except requests.exceptions.Timeout:
            if retry_count == 0:
                print(f"   🔄 Retrying due to timeout...")
                return self.call_llm(prompt, base64_image, retry_count + 1)
            return f"API Timeout Error: Request timed out after retries"
        except requests.exceptions.RequestException as e:
            return f"API Request Error: {str(e)}"
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def create_fallback_structure(self, raw_response: str, error_msg: str) -> Dict[str, Any]:
        """Create a fallback structure when JSON parsing fails"""
        return {
            "page_number": "unknown",
            "main_heading": "PARSE_ERROR",
            "text_content": f"Failed to parse response: {error_msg}",
            "tables": [],
            "figures": [],
            "zoning_rules": [],
            "code_references": [],
            "quality_notes": f"JSON parsing failed: {error_msg}",
            "raw_response": raw_response[:1000],  # Truncate to prevent huge files
            "parse_error": True
        }
    
    def analyze_image(self, image_path: Path) -> Dict[str, Any]:
        """Analyze a single image using OpenRouter API with enhanced error handling."""
        resized_image_path = None
        try:
            # Resize image if needed
            actual_image_path = self.resize_image_if_needed(image_path)
            if actual_image_path != image_path:
                resized_image_path = actual_image_path
            
            # Encode image
            base64_image = self.encode_image(actual_image_path)
            
            # Create analysis prompt
            prompt = self.create_analysis_prompt()
            
            # Get LLM analysis
            llm_response = self.call_llm(prompt, base64_image)
            
            # Check for API errors
            if llm_response.startswith("API Error") or llm_response.startswith("API Response Error"):
                llm_analysis = self.create_fallback_structure(llm_response, "API Error")
            else:
                # Try to parse JSON response
                try:
                    # Extract and clean JSON
                    json_str = self.extract_json_from_response(llm_response)
                    json_str = self.fix_common_json_issues(json_str)
                    
                    # Parse JSON
                    llm_analysis = json.loads(json_str)
                    
                    # Validate required fields and set defaults for missing ones
                    required_fields = {
                        "page": "unknown",
                        "heading": "no heading", 
                        "content": "no text extracted",
                        "figures": [],
                        "tables": [],
                        "codes": []
                    }
                    for field, default_value in required_fields.items():
                        if field not in llm_analysis:
                            llm_analysis[field] = default_value
                    
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"   🔧 JSON parsing failed: {str(e)}")
                    llm_analysis = self.create_fallback_structure(llm_response, str(e))
            
            # Create assessment structure
            assessment = {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "analysis": llm_analysis,
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model_used": self.model,
                "success": not llm_analysis.get("parse_error", False)
            }
            
            return assessment
            
        except Exception as e:
            return {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "error": str(e),
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model_used": self.model,
                "success": False
            }
        finally:
            # Clean up temporary resized image if created
            if resized_image_path and resized_image_path.exists():
                try:
                    resized_image_path.unlink()
                except Exception as cleanup_error:
                    print(f"   ⚠️  Warning: Could not delete temp file {resized_image_path}: {cleanup_error}")
    
    def save_assessment(self, assessment: Dict[str, Any]):
        """Save individual image assessment to JSON file."""
        image_name = Path(assessment['image_path']).stem
        filename = f"{self.output_dir}/{image_name}_analysis.json"
        
        with open(filename, 'w') as f:
            json.dump(assessment, f, indent=2)
    
    def update_progress(self, image_name: str, success: bool = True):
        """Update progress statistics in a thread-safe manner."""
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
            print(f"{status_icon} {image_name} | Progress: {self.completed_count}/{self.total_images} ({progress_pct:.1f}%) | "
                  f"Rate: {rate:.2f}/s | ETA: {eta/60:.1f}m")
    
    def process_image_worker(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """Worker function to process a single image."""
        try:
            assessment = self.analyze_image(image_path)
            self.save_assessment(assessment)
            
            # Check if analysis was successful
            success = assessment.get("success", True) and "error" not in assessment
            
            if success and "analysis" in assessment:
                # Show sample of response for interim reporting
                analysis = assessment["analysis"]
                if "content" in analysis and not analysis.get("parse_error", False):
                    sample = str(analysis["content"])[:150]
                    sample = sample.replace('\n', ' ').strip()
                    if len(sample) > 150:
                        sample += "..."
                    print(f"   📄 Sample: {sample}")
                else:
                    print(f"   ⚠️  Parse issues detected")
            
            self.update_progress(image_path.name, success)
            return assessment
        except Exception as e:
            print(f"❌ Error processing image {image_path.name}: {e}")
            self.update_progress(image_path.name, False)
            return None
    
    def analyze_images_streaming(self, image_paths: List[Path], max_concurrent: int = 8):
        """
        Analyze all images using streaming approach with reduced concurrency for stability.
        """
        self.total_images = len(image_paths)
        self.start_time = time.time()
        
        print(f"🚀 STREAMING IMAGE ANALYSIS STARTED (v3 - Enhanced Error Handling)")
        print(f"📊 Configuration:")
        print(f"   Total Images: {self.total_images}")
        print(f"   Max Concurrent: {max_concurrent}")
        print(f"   Model: {self.model}")
        print(f"   Strategy: Tit-for-Tat with enhanced JSON parsing")
        print()
        
        # Create a copy of image paths to work with
        remaining_images = copy.deepcopy(image_paths)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit initial batch of requests
            futures = {}
            
            # Fill the pipeline with initial requests
            initial_count = min(max_concurrent, len(remaining_images))
            for _ in range(initial_count):
                if remaining_images:
                    image_path = remaining_images.pop(0)
                    future = executor.submit(self.process_image_worker, image_path)
                    futures[future] = image_path
            
            print(f"🔄 Pipeline initialized with {initial_count} concurrent requests")
            print(f"📈 Streaming progress:")
            
            # Process completions and immediately submit new requests
            while futures:
                # Wait for at least one future to complete
                for future in as_completed(futures):
                    image_path = futures[future]
                    
                    try:
                        # Get the result
                        result = future.result()
                        
                        # Immediately submit a new request if more images remain
                        if remaining_images:
                            new_image_path = remaining_images.pop(0)
                            new_future = executor.submit(self.process_image_worker, new_image_path)
                            futures[new_future] = new_image_path
                        
                    except Exception as e:
                        print(f"❌ Future failed for image {image_path.name}: {e}")
                    
                    # Remove completed future
                    del futures[future]
                    
                    # Break from inner loop to check while condition
                    break
        
        # Final statistics
        end_time = time.time()
        total_time = end_time - self.start_time
        
        print(f"\n🎉 STREAMING ANALYSIS COMPLETED!")
        print(f"⏱️  Total Time: {total_time/60:.2f} minutes ({total_time:.1f} seconds)")
        print(f"📊 Performance: {self.completed_count/total_time:.2f} images/second")
        print(f"📂 Output Directory: {self.output_dir}")
        
        # Detailed success analysis
        files = [f for f in os.listdir(self.output_dir) if f.endswith('_analysis.json')]
        success_count = 0
        parse_error_count = 0
        
        for filename in files:
            try:
                with open(os.path.join(self.output_dir, filename), 'r') as f:
                    data = json.load(f)
                    if data.get("success", True) and "error" not in data:
                        if not data.get("analysis", {}).get("parse_error", False):
                            success_count += 1
                        else:
                            parse_error_count += 1
            except:
                pass
        
        failed_count = len(self.failed_images)
        success_rate = (success_count / self.total_images) * 100
        
        print(f"📄 Results Summary:")
        print(f"   ✅ Successful: {success_count}/{self.total_images} ({success_rate:.1f}%)")
        print(f"   🔧 Parse Errors: {parse_error_count}")
        print(f"   ❌ Failed: {failed_count}")
        
        if failed_count > 0 or parse_error_count > 0:
            print(f"💡 Suggestions:")
            if parse_error_count > 0:
                print(f"   • Try switching to Claude Sonnet (more reliable JSON)")
            if failed_count > 0:
                print(f"   • Reduce max_concurrent if getting API rate limits")
        
        return True

def main():
    """Main function to run the streaming analysis."""
    print("🌊 STREAMING CITY PLANNING IMAGE ANALYZER v3")
    print("=" * 60)
    
    # Get OpenRouter API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set your OpenRouter API key:")
        print("export OPENROUTER_API_KEY='your-actual-api-key'")
        print("Get your API key from: https://openrouter.ai/keys")
        return
    
    # Find all PNG images in pngs directory
    base_path = Path(__file__).parent / "pngs"
    if not base_path.exists():
        print(f"❌ Error: pngs directory not found at {base_path}")
        return
        
    all_images = sorted(base_path.glob("*.png"))
    
    if not all_images:
        print("❌ No PNG images found in pngs directory")
        return
    
    # Create analyzer
    analyzer = StreamingImageAnalyzer(api_key)
    
    # Reduced concurrency for better stability and fewer parsing errors
    max_concurrent = 8
    
    print(f"🎯 Found {len(all_images)} images to analyze")
    print(f"⚡ Using enhanced streaming strategy with {max_concurrent} concurrent requests")
    print(f"📁 Images will be processed from: {base_path}")
    
    # Show first few image names
    print(f"📋 Sample images:")
    for img in all_images[:5]:
        print(f"   • {img.name}")
    if len(all_images) > 5:
        print(f"   ... and {len(all_images) - 5} more")
    
    # Confirm before starting
    print(f"\n🤔 Proceed with streaming analysis of {len(all_images)} images? (y/N): ", end="")
    response = input().strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Analysis cancelled.")
        return
    
    try:
        # Run streaming analysis
        analyzer.analyze_images_streaming(all_images, max_concurrent=max_concurrent)
        
        print("\n✅ Analysis completed successfully!")
        print("📊 Check the output directory for detailed results.")
        
    except KeyboardInterrupt:
        print(f"\n⏸️  Analysis interrupted by user.")
        print(f"📂 Partial results saved in: {analyzer.output_dir}")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        print(f"📂 Partial results may be in: {analyzer.output_dir}")

if __name__ == "__main__":
    main()
