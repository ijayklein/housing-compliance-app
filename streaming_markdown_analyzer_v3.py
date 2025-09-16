#!/usr/bin/env python3
"""
Streaming Markdown Analyzer v3 - Fixed File Management and JSON Parsing
"""

import os
import json
import requests
import time
import threading
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class StreamingMarkdownAnalyzerV3:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.5-pro"
        
        # Create timestamped output directory
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = f'rules_extraction_v3_{timestamp}'
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir}")
        
        # Load extraction prompt
        self.extraction_prompt = self.load_extraction_prompt()
        
        # Tracking
        self.completed_files = set()
        self.failed_files = []
        self.successful_files = []
        self.total_files = 0
        self.start_time = None
        self.stats_lock = threading.Lock()
        
        # LLM interaction tracking
        self.message_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.retry_count = 0
        self.interaction_log = []
        self.log_lock = threading.Lock()
    
    def load_extraction_prompt(self) -> str:
        """Load the extraction prompt from promptforextraction.txt"""
        try:
            with open("promptforextraction.txt", 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print("❌ promptforextraction.txt not found")
            return ""
    
    def create_analysis_prompt(self, markdown_content: str) -> str:
        """Create simplified analysis prompt to reduce JSON complexity"""
        return f"""{self.extraction_prompt}

## Input Text to Analyze:

{markdown_content}

## Critical Instructions:
1. Extract rules according to the schema
2. Return ONLY a valid JSON array of rules
3. Each rule must be a complete JSON object
4. Use simple string values - avoid complex nested structures
5. If unsure about a field, use "TBD" or empty string
6. Ensure all quotes are properly escaped
7. Do not truncate the JSON - complete all objects

Example format:
[
  {{
    "rule": "Rule title",
    "Qualifiers": {{
      "Scope": "Description",
      "Applicability": "Description",
      "Exclusions": "Description"
    }},
    "Variables": {{}},
    "Constants": {{}},
    "Conditions": {{}},
    "Exceptions": {{}},
    "Relationships": {{}}
  }}
]"""
    
    def log_interaction(self, file_name: str, attempt: int, status: str, details: Dict[str, Any]):
        """Log LLM interaction details"""
        with self.log_lock:
            self.interaction_log.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_name": file_name,
                "attempt": attempt,
                "status": status,
                "model": self.model,
                **details
            })
    
    def fix_json_string(self, json_str: str) -> str:
        """Attempt to fix common JSON issues"""
        try:
            # Remove trailing commas
            json_str = json_str.replace(',}', '}').replace(',]', ']')
            
            # Try to close unclosed strings by finding the last quote
            if json_str.count('"') % 2 == 1:
                # Odd number of quotes - add closing quote
                json_str += '"'
            
            # Try to close unclosed objects/arrays
            open_braces = json_str.count('{') - json_str.count('}')
            open_brackets = json_str.count('[') - json_str.count(']')
            
            # Add missing closing braces
            for _ in range(open_braces):
                json_str += '}'
            
            # Add missing closing brackets
            for _ in range(open_brackets):
                json_str += ']'
            
            return json_str
        except:
            return json_str
    
    def call_llm_with_retry(self, prompt: str, file_name: str, max_retries: int = 3) -> Tuple[str, Dict[str, Any]]:
        """Make API call with retry logic and detailed logging"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.0,
            "max_tokens": 16000,  # Increased for complex JSON
            "top_p": 1.0
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"   🔄 {file_name}: Sending to LLM (attempt {attempt}/{max_retries})")
                
                start_time = time.time()
                response = requests.post(self.base_url, headers=headers, json=data, timeout=180)
                response_time = time.time() - start_time
                
                with self.stats_lock:
                    self.message_count += 1
                    if attempt > 1:
                        self.retry_count += 1
                
                if not response.ok:
                    error_msg = f"API Error {response.status_code}: {response.text}"
                    print(f"   ❌ {file_name}: {error_msg}")
                    
                    self.log_interaction(file_name, attempt, "API_ERROR", {
                        "error": error_msg,
                        "response_time": response_time,
                        "status_code": response.status_code
                    })
                    
                    if attempt == max_retries:
                        return f"API_ERROR: {error_msg}", {}
                    
                    time.sleep(2 ** attempt)
                    continue
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract token usage if available
                usage = result.get('usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                
                with self.stats_lock:
                    self.total_input_tokens += input_tokens
                    self.total_output_tokens += output_tokens
                
                print(f"   ✅ {file_name}: Received response ({len(content)} chars, {response_time:.1f}s)")
                
                self.log_interaction(file_name, attempt, "SUCCESS", {
                    "response_time": response_time,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "content_length": len(content)
                })
                
                if not content or len(content.strip()) < 10:
                    print(f"   ⚠️ {file_name}: Empty response")
                    if attempt == max_retries:
                        return "API_ERROR: Empty response", {}
                    continue
                
                return content, {
                    "response_time": response_time,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "attempt": attempt
                }
                
            except requests.exceptions.Timeout:
                error_msg = "Request timeout"
                print(f"   ⏰ {file_name}: {error_msg}")
                
                self.log_interaction(file_name, attempt, "TIMEOUT", {
                    "error": error_msg
                })
                
                if attempt == max_retries:
                    return f"API_ERROR: {error_msg}", {}
                
                time.sleep(2 ** attempt)
                
            except Exception as e:
                error_msg = str(e)
                print(f"   💥 {file_name}: {error_msg}")
                
                self.log_interaction(file_name, attempt, "EXCEPTION", {
                    "error": error_msg
                })
                
                if attempt == max_retries:
                    return f"API_ERROR: {error_msg}", {}
                
                time.sleep(2 ** attempt)
        
        return "API_ERROR: Max retries exceeded", {}
    
    def extract_json_from_response(self, response: str, file_name: str) -> Dict[str, Any]:
        """Extract and parse JSON with enhanced error recovery"""
        if response.startswith("API_ERROR"):
            return {"parse_error": True, "error": response}
        
        try:
            content = response.strip()
            
            # Remove markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    json_str = content[start:end].strip()
                else:
                    json_str = content[start:].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    json_str = content[start:end].strip()
                else:
                    json_str = content[start:].strip()
            else:
                json_str = content
            
            # Find JSON boundaries
            if not (json_str.startswith('{') or json_str.startswith('[')):
                start_brace = json_str.find('{')
                start_bracket = json_str.find('[')
                
                if start_brace == -1 and start_bracket == -1:
                    print(f"   ❌ {file_name}: No JSON found")
                    return {"parse_error": True, "error": "No JSON found", "raw_response": response}
                
                start = start_brace if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket) else start_bracket
                json_str = json_str[start:]
            
            # Try to parse as-is first
            try:
                parsed = json.loads(json_str)
                print(f"   📋 {file_name}: JSON parsed successfully")
                
                # Determine output type
                if isinstance(parsed, list):
                    print(f"   📊 {file_name}: Extracted {len(parsed)} rule(s)")
                elif isinstance(parsed, dict):
                    print(f"   📊 {file_name}: Extracted rule data (dict)")
                
                return {
                    "extracted_rules": parsed,
                    "parse_error": False,
                    "raw_response": response
                }
            except json.JSONDecodeError as e:
                print(f"   🔧 {file_name}: Attempting JSON repair - {str(e)}")
                
                # Try to fix the JSON
                fixed_json = self.fix_json_string(json_str)
                
                try:
                    parsed = json.loads(fixed_json)
                    print(f"   ✅ {file_name}: JSON repaired and parsed successfully")
                    
                    if isinstance(parsed, list):
                        print(f"   📊 {file_name}: Extracted {len(parsed)} rule(s)")
                    elif isinstance(parsed, dict):
                        print(f"   📊 {file_name}: Extracted rule data (dict)")
                    
                    return {
                        "extracted_rules": parsed,
                        "parse_error": False,
                        "raw_response": response,
                        "repaired": True
                    }
                except json.JSONDecodeError as e2:
                    print(f"   ❌ {file_name}: JSON repair failed - {str(e2)}")
                    return {
                        "parse_error": True, 
                        "error": f"JSON decode error (original: {str(e)}, repaired: {str(e2)})", 
                        "raw_response": response,
                        "attempted_json": json_str,
                        "repaired_json": fixed_json
                    }
            
        except Exception as e:
            print(f"   ❌ {file_name}: Extraction error - {str(e)}")
            return {
                "parse_error": True, 
                "error": f"Extraction error: {str(e)}", 
                "raw_response": response
            }
    
    def analyze_markdown_file(self, md_path: Path) -> Dict[str, Any]:
        """Analyze a single markdown file"""
        file_name = md_path.name
        
        try:
            # Read markdown content
            with open(md_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            print(f"📄 {file_name}: Starting analysis...")
            
            # Get LLM analysis with retry
            prompt = self.create_analysis_prompt(markdown_content)
            llm_response, call_metadata = self.call_llm_with_retry(prompt, file_name)
            
            # Extract JSON from response
            analysis = self.extract_json_from_response(llm_response, file_name)
            
            # Add call metadata
            analysis.update(call_metadata)
            
            return {
                "file_path": str(md_path),
                "file_name": file_name,
                "analysis": analysis,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": self.model,
                "success": not analysis.get("parse_error", False)
            }
            
        except Exception as e:
            print(f"   💥 {file_name}: Exception - {str(e)}")
            return {
                "file_path": str(md_path),
                "file_name": file_name,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": False
            }
    
    def save_assessment(self, assessment: Dict[str, Any]):
        """Save assessment to JSON file"""
        file_name = Path(assessment['file_path']).stem
        filename = f"{self.output_dir}/{file_name}_rules.json"
        with open(filename, 'w') as f:
            json.dump(assessment, f, indent=2)
    
    def process_file_worker(self, md_path: Path) -> Optional[Dict[str, Any]]:
        """Worker function to process a single file"""
        try:
            assessment = self.analyze_markdown_file(md_path)
            self.save_assessment(assessment)
            
            success = assessment.get("success", True)
            file_name = md_path.name
            
            with self.stats_lock:
                self.completed_files.add(file_name)
                if success:
                    self.successful_files.append(file_name)
                else:
                    self.failed_files.append(file_name)
            
            return assessment
        except Exception as e:
            print(f"❌ Error processing {md_path.name}: {e}")
            with self.stats_lock:
                self.completed_files.add(md_path.name)
                self.failed_files.append(md_path.name)
            return None
    
    def analyze_files_streaming(self, md_paths: List[Path], max_concurrent: int = 8):
        """Analyze files with proper retry management"""
        self.total_files = len(md_paths)
        self.start_time = time.time()
        
        print(f"🚀 STREAMING MARKDOWN ANALYSIS v3 - Fixed File Management")
        print(f"📊 Files: {self.total_files} | Concurrent: {max_concurrent} | Model: {self.model}")
        print(f"🔄 Retry logic: Failed files will be retried at the end")
        print()
        
        # Phase 1: Process all files
        print("📋 Phase 1: Processing all files...")
        remaining_files = copy.deepcopy(md_paths)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {}
            
            # Submit initial batch
            initial_count = min(max_concurrent, len(remaining_files))
            for _ in range(initial_count):
                if remaining_files:
                    md_path = remaining_files.pop(0)
                    future = executor.submit(self.process_file_worker, md_path)
                    futures[future] = md_path
            
            # Process completions and submit new work
            while futures:
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        completed_file = futures[future]
                        
                        # Progress update
                        with self.stats_lock:
                            completed_count = len(self.completed_files)
                            elapsed = time.time() - self.start_time
                            rate = completed_count / elapsed if elapsed > 0 else 0
                            remaining = self.total_files - completed_count
                            eta = remaining / rate if rate > 0 else 0
                            
                            progress_pct = (completed_count / self.total_files) * 100
                            success = result and result.get("success", False) if result else False
                            status_icon = "✅" if success else "❌"
                            
                            print(f"{status_icon} {completed_file.name} | Progress: {completed_count}/{self.total_files} "
                                  f"({progress_pct:.1f}%) | Rate: {rate:.2f}/s | ETA: {eta/60:.1f}m")
                        
                        # Submit next file if available
                        if remaining_files:
                            new_md_path = remaining_files.pop(0)
                            new_future = executor.submit(self.process_file_worker, new_md_path)
                            futures[new_future] = new_md_path
                    
                    except Exception as e:
                        print(f"❌ Future error: {e}")
                    
                    del futures[future]
                    break
        
        # Phase 2: Retry failed files
        if self.failed_files:
            print(f"\n🔄 Phase 2: Retrying {len(self.failed_files)} failed files...")
            failed_paths = [Path("markdown_pages") / f for f in self.failed_files]
            
            # Clear failed files list for retry
            self.failed_files = []
            
            with ThreadPoolExecutor(max_workers=min(4, len(failed_paths))) as executor:
                retry_futures = {executor.submit(self.process_file_worker, path): path for path in failed_paths}
                
                for future in as_completed(retry_futures):
                    try:
                        result = future.result()
                        retry_file = retry_futures[future]
                        success = result and result.get("success", False) if result else False
                        
                        if success:
                            print(f"✅ RETRY SUCCESS: {retry_file.name}")
                            with self.stats_lock:
                                if retry_file.name in self.failed_files:
                                    self.failed_files.remove(retry_file.name)
                                if retry_file.name not in self.successful_files:
                                    self.successful_files.append(retry_file.name)
                        else:
                            print(f"❌ RETRY FAILED: {retry_file.name}")
                    except Exception as e:
                        print(f"❌ Retry error: {e}")
        
        # Final stats
        total_time = time.time() - self.start_time
        success_count = len(self.successful_files)
        final_failed_count = len(self.failed_files)
        
        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"⏱️  Time: {total_time:.1f}s | Rate: {self.total_files/total_time:.2f}/s")
        print(f"✅ Success: {success_count}/{self.total_files} ({success_count/self.total_files*100:.1f}%)")
        print(f"📨 Total LLM messages: {self.message_count}")
        print(f"🔄 Retry attempts: {self.retry_count}")
        print(f"📥 Input tokens: {self.total_input_tokens:,}")
        print(f"📤 Output tokens: {self.total_output_tokens:,}")
        print(f"💰 Total tokens: {self.total_input_tokens + self.total_output_tokens:,}")
        
        if final_failed_count > 0:
            print(f"❌ Final failures: {final_failed_count}")
            print(f"   Failed files: {', '.join(self.failed_files)}")
        
        # Save interaction log
        log_file = f"{self.output_dir}/interaction_log.json"
        with open(log_file, 'w') as f:
            json.dump(self.interaction_log, f, indent=2)
        print(f"📋 Interaction log saved: {log_file}")
        
        return True

def main():
    print("📋 STREAMING MARKDOWN ANALYZER v3 - Fixed File Management & JSON Parsing")
    print("=" * 75)
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return
    
    md_path = Path(__file__).parent / "markdown_pages"
    if not md_path.exists():
        print(f"❌ markdown_pages directory not found")
        return
        
    all_md_files = sorted(md_path.glob("*.md"))
    if not all_md_files:
        print("❌ No markdown files found")
        return
    
    analyzer = StreamingMarkdownAnalyzerV3(api_key)
    
    if not analyzer.extraction_prompt:
        print("❌ Could not load extraction prompt")
        return
    
    print(f"🎯 Found {len(all_md_files)} markdown files")
    print(f"🔧 Enhanced JSON parsing with repair logic")
    print(f"🔄 Two-phase processing: Initial run + Failed file retry")
    print(f"⚡ Concurrent workers: 8 (initial) + 4 (retry)")
    
    response = input(f"\n🤔 Analyze {len(all_md_files)} files? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cancelled")
        return
    
    try:
        analyzer.analyze_files_streaming(all_md_files, max_concurrent=8)
        print("\n✅ Complete! Check output directory for results.")
    except KeyboardInterrupt:
        print(f"\n⏸️  Interrupted. Partial results in: {analyzer.output_dir}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
