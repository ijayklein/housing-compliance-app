#!/usr/bin/env python3
"""
Streaming Markdown Analyzer v1 - Rule Extraction
Based on streaming_image_analyzer_v4.py protocol for processing markdown files.
"""

import os
import json
import requests
import time
import threading
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional

class StreamingMarkdownAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openai/gpt-5"  # Good for structured JSON output
        
        # Create timestamped output directory
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = f'rules_extraction_{timestamp}'
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir}")
        
        # Load extraction prompt
        self.extraction_prompt = self.load_extraction_prompt()
        
        # Streaming control
        self.completed_count = 0
        self.total_files = 0
        self.start_time = None
        self.stats_lock = threading.Lock()
        self.failed_files = []
    
    def load_extraction_prompt(self) -> str:
        """Load the extraction prompt from promptforextraction.txt"""
        try:
            with open("promptforextraction.txt", 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print("❌ promptforextraction.txt not found")
            return ""
    
    def create_analysis_prompt(self, markdown_content: str) -> str:
        """Create analysis prompt with the markdown content"""
        return f"""{self.extraction_prompt}

## Input Text to Analyze:

{markdown_content}

## Instructions:
Analyze the above text and extract all rules/regulations according to the schema. Output valid JSON only."""
    
    def call_llm(self, prompt: str) -> str:
        """Make API call for text analysis."""
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
            "temperature": 0.1,
            "max_tokens": 8000
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
    
    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM response"""
        if response.startswith("API_ERROR"):
            return {"parse_error": True, "error": response}
        
        try:
            # Try to find JSON in the response
            content = response.strip()
            
            # Look for JSON blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    json_str = content[start:end].strip()
                else:
                    json_str = content[start:].strip()
            elif content.startswith('{') or content.startswith('['):
                json_str = content
            else:
                # Try to find the first { or [
                start_brace = content.find('{')
                start_bracket = content.find('[')
                
                if start_brace == -1 and start_bracket == -1:
                    return {"parse_error": True, "error": "No JSON found in response", "raw_response": response}
                
                start = start_brace if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket) else start_bracket
                json_str = content[start:]
            
            # Parse JSON
            parsed = json.loads(json_str)
            return {
                "extracted_rules": parsed,
                "parse_error": False,
                "raw_response": response
            }
            
        except json.JSONDecodeError as e:
            return {
                "parse_error": True, 
                "error": f"JSON decode error: {str(e)}", 
                "raw_response": response
            }
        except Exception as e:
            return {
                "parse_error": True, 
                "error": f"Extraction error: {str(e)}", 
                "raw_response": response
            }
    
    def analyze_markdown_file(self, md_path: Path) -> Dict[str, Any]:
        """Analyze a single markdown file for rule extraction."""
        try:
            # Read markdown content
            with open(md_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Get LLM analysis
            prompt = self.create_analysis_prompt(markdown_content)
            llm_response = self.call_llm(prompt)
            
            # Extract JSON from response
            analysis = self.extract_json_from_response(llm_response)
            
            return {
                "file_path": str(md_path),
                "file_name": md_path.name,
                "analysis": analysis,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": self.model,
                "success": not analysis.get("parse_error", False)
            }
            
        except Exception as e:
            return {
                "file_path": str(md_path),
                "file_name": md_path.name,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": False
            }
    
    def save_assessment(self, assessment: Dict[str, Any]):
        """Save assessment to JSON file."""
        file_name = Path(assessment['file_path']).stem
        filename = f"{self.output_dir}/{file_name}_rules.json"
        with open(filename, 'w') as f:
            json.dump(assessment, f, indent=2)
    
    def update_progress(self, file_name: str, success: bool = True):
        """Update progress statistics."""
        with self.stats_lock:
            self.completed_count += 1
            if not success:
                self.failed_files.append(file_name)
                
            elapsed = time.time() - self.start_time
            rate = self.completed_count / elapsed
            remaining = self.total_files - self.completed_count
            eta = remaining / rate if rate > 0 else 0
            
            progress_pct = (self.completed_count / self.total_files) * 100
            status_icon = "✅" if success else "❌"
            
            print(f"{status_icon} {file_name} | Progress: {self.completed_count}/{self.total_files} "
                  f"({progress_pct:.1f}%) | Rate: {rate:.2f}/s | ETA: {eta/60:.1f}m")
    
    def process_file_worker(self, md_path: Path) -> Optional[Dict[str, Any]]:
        """Worker function to process a single markdown file."""
        try:
            assessment = self.analyze_markdown_file(md_path)
            self.save_assessment(assessment)
            
            success = assessment.get("success", True)
            
            # Show sample output from extracted rules
            if success and "analysis" in assessment and "extracted_rules" in assessment["analysis"]:
                rules = assessment["analysis"]["extracted_rules"]
                if isinstance(rules, list) and rules:
                    rule_count = len(rules)
                    print(f"   📋 Extracted {rule_count} rule(s)")
                elif isinstance(rules, dict):
                    print(f"   📋 Extracted rule data")
                else:
                    print(f"   📋 Extracted structured data")
            elif success:
                print(f"   📄 Analysis completed")
            
            self.update_progress(md_path.name, success)
            return assessment
        except Exception as e:
            print(f"❌ Error processing {md_path.name}: {e}")
            self.update_progress(md_path.name, False)
            return None
    
    def analyze_files_streaming(self, md_paths: List[Path], max_concurrent: int = 4):
        """Analyze markdown files with streaming approach."""
        self.total_files = len(md_paths)
        self.start_time = time.time()
        
        print(f"🚀 STREAMING MARKDOWN ANALYSIS v1 - Rule Extraction")
        print(f"📊 Files: {self.total_files} | Concurrent: {max_concurrent} | Model: {self.model}")
        print()
        
        remaining_files = copy.deepcopy(md_paths)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {}
            
            # Initialize pipeline
            initial_count = min(max_concurrent, len(remaining_files))
            for _ in range(initial_count):
                if remaining_files:
                    md_path = remaining_files.pop(0)
                    future = executor.submit(self.process_file_worker, md_path)
                    futures[future] = md_path
            
            # Process completions
            while futures:
                for future in as_completed(futures):
                    try:
                        future.result()
                        if remaining_files:
                            new_md_path = remaining_files.pop(0)
                            new_future = executor.submit(self.process_file_worker, new_md_path)
                            futures[new_future] = new_md_path
                    except Exception as e:
                        print(f"❌ Future error: {e}")
                    
                    del futures[future]
                    break
        
        # Final stats
        total_time = time.time() - self.start_time
        success_count = self.total_files - len(self.failed_files)
        
        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"⏱️  Time: {total_time:.1f}s | Rate: {self.completed_count/total_time:.2f}/s")
        print(f"✅ Success: {success_count}/{self.total_files} ({success_count/self.total_files*100:.1f}%)")
        if self.failed_files:
            print(f"❌ Failed: {len(self.failed_files)}")
            print(f"   Failed files: {', '.join(self.failed_files)}")
        
        return True

def main():
    print("📋 STREAMING MARKDOWN ANALYZER v1 - Rule Extraction")
    print("=" * 55)
    
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
    
    analyzer = StreamingMarkdownAnalyzer(api_key)
    
    if not analyzer.extraction_prompt:
        print("❌ Could not load extraction prompt")
        return
    
    print(f"🎯 Found {len(all_md_files)} markdown files")
    print(f"🔧 Using extraction prompt from promptforextraction.txt")
    
    response = input(f"\n🤔 Analyze {len(all_md_files)} files for rule extraction? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cancelled")
        return
    
    try:
        analyzer.analyze_files_streaming(all_md_files, max_concurrent=4)
        print("\n✅ Complete! Check output directory for extracted rules.")
    except KeyboardInterrupt:
        print(f"\n⏸️  Interrupted. Partial results in: {analyzer.output_dir}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
