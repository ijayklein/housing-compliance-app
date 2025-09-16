#!/usr/bin/env python3
"""
Streaming Image Analyzer - "Tit for Tat" Strategy
Maintains a constant flow of API requests by immediately sending new requests as previous ones complete.
This maximizes throughput by avoiding batch completion waits for city planning rule image analysis.
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
from queue import Queue, Empty
from PIL import Image

class StreamingImageAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-sonnet-4"
        #self.model = "google/gemini-2.5-flash"
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
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)  # Use JPEG for better compression
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
        """Create detailed prompt for city planning rule analysis"""
        return """You are analyzing photocopied pages from a city planning technical manual. These images contain crucial zoning rules, regulations, and technical specifications that must be captured with absolute precision.

CRITICAL REQUIREMENTS:
1. Extract ALL text content verbatim, preserving exact formatting, spacing, and structure
2. Identify and describe ALL figures, diagrams, charts, tables, and visual elements in detail
3. Identify and describe ALL qualifiers (or pre-conditions) and conditions, mentioned, which should be met and be clear about the (be clear about) content in detail
3. Capture ALL numerical values, measurements, percentages, and technical specifications
4. Document ALL section headings, subheadings, bullet points, and hierarchical structure
5. Note any handwritten annotations, stamps, or markings
6. Describe the overall layout and organization of the page
7. Identify any references to other sections, pages, or documents

FORMAT YOUR RESPONSE AS JSON:
{
  "page_analysis": {
    "text_content": "Complete verbatim transcription of all text, maintaining original formatting",
    "visual_elements": [
      {
        "type": "figure|diagram|table|chart",
        "description": "Detailed explanation of what the element shows",
        "location": "Position on page (top, middle, bottom, etc.)"
      }
    ],
    "technical_specifications": [
      {
        "parameter": "Name of specification",
        "value_type": "Numerical|Measurement|Percentage|Text|List|Range|None",
        "value": "Numerical value or measurement, percentage, text, list, range, or None",
        "unit": "Unit of measurement if applicable"
      }
    ],
    "structural_elements": {
      "main_heading": "Primary heading if present",
      "subheadings": ["List of subheadings"],
      "sections": ["List of section identifiers"]
    },
    "additional_notes": [
      "Any handwritten notes, stamps, quality issues, or other observations"
    ],
    "cross_references": [
      "References to other sections, pages, or documents"
    ],
    "conditions_and_qualifiers": {
      "qualifiers": [
        {
          "id": "q1",
          "text": "Exact quoted text of the qualifier/pre-condition",
          "applies_to_conditions": ["c1", "c3"],
          "scope": "Global|Local|Specific"
        }
      ],
      "conditions": [
        {
          "id": "c1",
          "text": "Exact quoted text of the condition",
          "value_type": "Numerical|Measurement|Boolean|Text|Range",
          "operator": "=|>|<|>=|<=|!=|contains|matches",
          "threshold_value": "Specific value if applicable",
          "unit": "Unit if applicable"
        }
      ],
      "logical_relationships": [
        {
          "operation": "AND|OR|NOT|XOR|IF-THEN|IF-THEN-ELSE",
          "condition_ids": ["c1", "c2"],
          "expression": "Exact text showing the logical relationship",
          "evaluation_order": 1
        }
      ],
      "execution_sequence": [
        {
          "step": 1,
          "action": "Description of what must be evaluated/executed",
          "condition_ids": ["c1"],
          "qualifier_ids": ["q1"],
          "dependencies": ["Previous step numbers this depends on"]
        }
      ]
    }
  }
}


**IMPORTANT:**
- **Be exhaustive and precise** - missing information could impact critical city planning decisions
- **Extract conditions and qualifiers completely** - incomplete logical relationships or missing qualifiers could lead to misapplication of requirements
- **Maintain exact text quotations** - any paraphrasing or interpretation of conditions could change their meaning
- **Respond with ONLY the JSON object specified**
- **Do not include any other text or explanation outside the JSON**
- **If text is unclear due to image quality, note it in additional_notes and mark affected conditions/qualifiers as "unclear_due_to_image_quality": true**
- **If logical relationships are ambiguous or not explicitly stated, note this in the logical_relationships section with "ambiguity_note" field**"""

    def call_llm(self, prompt: str, base64_image: str) -> str:
        """Make API call to OpenRouter for image analysis."""
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
            "max_tokens": 8000  # Increased for Gemini's verbose responses
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=120)
            
            if not response.ok:
                return f"API Error: {response.status_code} - {response.text}"
            
            try:
                result = response.json()
                if 'choices' not in result:
                    return f"API Response Error: Missing 'choices' field in response: {result}"
                if len(result['choices']) == 0:
                    return f"API Response Error: Empty choices array in response: {result}"
                if 'message' not in result['choices'][0]:
                    return f"API Response Error: Missing 'message' field in choice: {result['choices'][0]}"
                if 'content' not in result['choices'][0]['message']:
                    return f"API Response Error: Missing 'content' field in message: {result['choices'][0]['message']}"
                
                content = result['choices'][0]['message']['content']
                
                # Check for empty/whitespace-only responses (common with GPT-4.1-mini on complex prompts)
                if not content or content.strip() == "" or len(content.strip()) < 10:
                    return f"API Response Error: Empty or whitespace-only response from model. Response length: {len(content)} chars"
                
                # Check for responses that are mostly whitespace/newlines
                non_whitespace = ''.join(content.split())
                if len(non_whitespace) < 50:  # Less than 50 non-whitespace characters
                    return f"API Response Error: Response contains mostly whitespace. Non-whitespace chars: {len(non_whitespace)}"
                    
                return content
            except json.JSONDecodeError as e:
                return f"API Response Parse Error: Failed to parse JSON response: {str(e)} - Response: {response.text[:500]}"
                
        except requests.exceptions.Timeout:
            return f"API Timeout Error: Request timed out after 120 seconds"
        except requests.exceptions.RequestException as e:
            return f"API Request Error: {str(e)}"
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def fix_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues that cause parsing errors - GEMINI-OPTIMIZED VERSION."""
        # Simple fixes only to avoid infinite loops
        
        # Remove trailing commas before closing brackets/braces
        json_str = json_str.replace(',}', '}').replace(',]', ']')
        
        # Fix truncated JSON (common with Gemini's verbose responses)
        if not json_str.rstrip().endswith('}'):
            print("   🔧 Detected truncated JSON, attempting to fix...")
            
            # Find the last complete field and close the JSON properly
            lines = json_str.split('\n')
            fixed_lines = []
            
            for line in lines:
                # Skip incomplete lines (no closing quote or brace)
                if '":' in line and not (line.rstrip().endswith('"') or 
                                        line.rstrip().endswith(',') or
                                        line.rstrip().endswith('}') or
                                        line.rstrip().endswith(']')):
                    print(f"   🔧 Removing incomplete line: {line[:50]}...")
                    break
                fixed_lines.append(line)
            
            # Ensure proper closing
            json_str = '\n'.join(fixed_lines)
            if not json_str.rstrip().endswith('}'):
                # Count open braces vs close braces
                open_braces = json_str.count('{')
                close_braces = json_str.count('}')
                missing_braces = open_braces - close_braces
                
                # Add missing closing braces
                json_str = json_str.rstrip()
                if json_str.endswith(','):
                    json_str = json_str[:-1]  # Remove trailing comma
                json_str += '\n' + '  ' * (missing_braces - 1) + '}' * missing_braces
        
        # Fix the text_content array format issue
        if '"text_content":' in json_str and '],\n' in json_str:
            lines = json_str.split('\n')
            fixed_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                if '"text_content":' in line and line.strip().endswith('"'):
                    # Check if next line is just whitespace and ],
                    if i + 1 < len(lines) and lines[i + 1].strip() == '],':
                        # Replace the ], with just ,
                        fixed_lines.append(line.rstrip() + ',')
                        i += 2  # Skip the ], line
                        continue
                fixed_lines.append(line)
                i += 1
            json_str = '\n'.join(fixed_lines)
        
        return json_str
    
    def analyze_image(self, image_path: Path) -> Dict[str, Any]:
        """Analyze a single image using OpenRouter API."""
        resized_image_path = None
        try:
            # Resize image if needed (handles oversized images)
            actual_image_path = self.resize_image_if_needed(image_path)
            if actual_image_path != image_path:
                resized_image_path = actual_image_path  # Track for cleanup
            
            # Encode image
            base64_image = self.encode_image(actual_image_path)
            
            # Create analysis prompt
            prompt = self.create_analysis_prompt()
            
            # Get LLM analysis with retry for empty responses
            llm_response = self.call_llm(prompt, base64_image)
            
            # Retry once if we get an empty/whitespace response
            if "API Response Error: Empty" in llm_response or "Response contains mostly whitespace" in llm_response:
                print(f"   🔄 Retrying due to empty response...")
                llm_response = self.call_llm(prompt, base64_image)
            
            # Try to parse JSON response
            try:
                # Remove markdown code blocks if present
                clean_response = llm_response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                elif clean_response.startswith('```'):
                    clean_response = clean_response[3:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                # Handle potential trailing commas and other JSON issues
                clean_response = self.fix_json_issues(clean_response)
                
                llm_analysis = json.loads(clean_response)
            except json.JSONDecodeError as e:
                # Fallback structure if JSON parsing fails
                llm_analysis = {
                    "page_analysis": {
                        "text_content": "PARSE_ERROR",
                        "visual_elements": [],
                        "technical_specifications": [],
                        "structural_elements": {"main_heading": "", "subheadings": [], "sections": []},
                        "additional_notes": [f"Failed to parse LLM response: {str(e)}"],
                        "cross_references": []
                    },
                    "raw_response": llm_response
                }
            
            # Create assessment structure
            assessment = {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "analysis": llm_analysis,
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model_used": self.model
            }
            
            return assessment
            
        except Exception as e:
            return {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "error": str(e),
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model_used": self.model
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
            success = "error" not in assessment
            if success and "analysis" in assessment:
                # Show sample of response for interim reporting
                analysis = assessment["analysis"]
                if "page_analysis" in analysis and "text_content" in analysis["page_analysis"]:
                    sample = analysis["page_analysis"]["text_content"][:150]
                    sample = sample.replace('\n', ' ').strip()
                    if len(sample) > 150:
                        sample += "..."
                    print(f"   📄 Sample: {sample}")
            
            self.update_progress(image_path.name, success)
            return assessment
        except Exception as e:
            print(f"❌ Error processing image {image_path.name}: {e}")
            self.update_progress(image_path.name, False)
            return None
    
    def analyze_images_streaming(self, image_paths: List[Path], max_concurrent: int = 16):
        """
        Analyze all images using streaming approach.
        Maintains constant flow of requests by immediately sending new ones as others complete.
        """
        self.total_images = len(image_paths)
        self.start_time = time.time()
        
        print(f"🚀 STREAMING IMAGE ANALYSIS STARTED")
        print(f"📊 Configuration:")
        print(f"   Total Images: {self.total_images}")
        print(f"   Max Concurrent: {max_concurrent}")
        print(f"   Model: {self.model}")
        print(f"   Strategy: Tit-for-Tat (immediate request replacement)")
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
            while futures:  # Continue while there are active futures
                # Wait for at least one future to complete
                for future in as_completed(futures):
                    image_path = futures[future]
                    
                    try:
                        # Get the result (this will raise exception if worker failed)
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
        
        # Quick file count verification
        files = [f for f in os.listdir(self.output_dir) if f.endswith('_analysis.json')]
        success_count = len(files)
        failed_count = len(self.failed_images)
        success_rate = (success_count / self.total_images) * 100
        
        print(f"📄 Files Created: {success_count}/{self.total_images} ({success_rate:.1f}% success rate)")
        if failed_count > 0:
            print(f"❌ Failed Images: {failed_count}")
            print(f"   {', '.join(self.failed_images[:5])}")
            if len(self.failed_images) > 5:
                print(f"   ... and {len(self.failed_images) - 5} more")
        
        return True

def main():
    """Main function to run the streaming analysis."""
    print("🌊 STREAMING CITY PLANNING IMAGE ANALYZER")
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
    
    # Configuration
    max_concurrent = 16  # Conservative for image analysis (larger payloads)
    
    print(f"🎯 Found {len(all_images)} images to analyze")
    print(f"⚡ Using streaming strategy with {max_concurrent} concurrent requests")
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
