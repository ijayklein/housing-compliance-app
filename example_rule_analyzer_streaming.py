#!/usr/bin/env python3
"""
Streaming Rule Analyzer - "Tit for Tat" Strategy
Maintains a constant flow of API requests by immediately sending new requests as previous ones complete.
This maximizes throughput by avoiding batch completion waits.
"""

import json
import requests
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from queue import Queue, Empty
import copy

class StreamingRuleAnalyzer:
    def __init__(self, openrouter_api_key: str):
        self.api_key = openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.5-flash"
        
        # Load the articles summary and candidate rules
        with open('articles_high_level_summary.json', 'r') as f:
            self.articles_summary = json.load(f)
        
        with open('candidate_rules.json', 'r') as f:
            self.candidate_rules = json.load(f)
        
        # Create timestamped output directory for assessments
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = f'rule_assessments_streaming_{timestamp}'
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Output directory: {self.output_dir}")
        
        # Streaming control
        self.pending_queue = Queue()
        self.completed_count = 0
        self.total_rules = 0
        self.start_time = None
        self.stats_lock = threading.Lock()
        
    def get_article_summary(self, rule_id: str) -> str:
        """Extract article number from rule ID and find corresponding article summary."""
        article_num = rule_id.split('.')[0]
        
        for chapter_name, articles in self.articles_summary.items():
            for article in articles:
                if article['article'].startswith(f"{article_num} -"):
                    return article['summary']
        
        return f"No summary found for article {article_num}"
    
    def create_analysis_prompt(self, rule: Dict[str, Any], article_summary: str) -> str:
        """Create the prompt for LLM analysis of a rule."""
        
        rule_id = rule['code_regulation_id']
        rule_name = rule['code_regulation_name']
        rule_content = rule['content']
        
        prompt = f"""
You are an expert electrical code analyst. Analyze the following electrical code rule to determine if it can be transformed into an automated validation test program.

RULE CONTEXT:
Article Summary: {article_summary}

RULE TO ANALYZE:
Rule ID: {rule_id}
Rule Name: {rule_name}
Rule Content: {rule_content}

TRANSFORMATION CRITERIA:
A rule is TRANSFORMABLE if it involves:
- Numerical values, measurements, or calculations
- Quantifiable parameters (distances, sizes, quantities, percentages)
- Logical conditions that can be programmatically evaluated
- Design-stage verifiable requirements

A rule is NOT TRANSFORMABLE if it requires:
- Physical on-site inspection
- Human judgment of workmanship quality
- Material verification that cannot be determined from design documents
- Subjective assessment of installation quality

REQUIRED JSON OUTPUT FORMAT:
{{
  "transformability": "YES" | "NO",
    // YES if rule can be automated, NO if requires human inspection/judgment
  "confidence_level": "HIGH" | "MEDIUM" | "LOW",
    // Confidence in the transformability assessment
  "primary_blocking_factors": ["NONE"] | ["FIELD_INSPECTION_REQUIRED", "MATERIAL_VERIFICATION_REQUIRED", "WORKMANSHIP_QUALITY_REQUIRED", "SUBJECTIVE_ASSESSMENT_REQUIRED", "PROCEDURAL_INFORMATIONAL_ONLY"],
    // Main impediments to automation (max 3 items)
  "quantifiable_elements": [numbers],
    // Numerical values from the rule that could be validated (max 10 items)
  "automation_complexity": "LOW" | "MEDIUM" | "HIGH" | "NONE",
    // Programming effort required for automation
  "reasoning_summary": "brief explanation",
    // 1-2 sentence explanation of the decision (max 100 words)
  "key_validation_checks": ["check1", "check2"],
    // Main validation steps for automation (max 5 items)
  "required_design_inputs": ["input1", "input2"],
    // Design documents/data needed for validation (max 5 items)
  "automation_limitations": ["limitation1"] | ["NONE"],
    // Constraints or limitations of automated approach (max 3 items)
  "estimated_automation_coverage": 0-100
    // Percentage of the rule that could be automated (0 = none, 100 = fully automated)
}}

IMPORTANT: 
- Keep arrays concise and avoid repetition
- Use UNIQUE values only in quantifiable_elements
- Limit array sizes as specified above
- Use ONLY decimal numbers (e.g., 0.125, 0.5, 0.25) NOT mathematical expressions (e.g., 1/8, 1/2, 1/4)
- Respond with ONLY the JSON object above
- Do not include any other text or explanation outside the JSON
"""
        return prompt
    
    def call_llm(self, prompt: str) -> str:
        """Make API call to OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "Electrical Code Rule Analyzer"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            
            if not response.ok:
                return f"API Error: {response.status_code} - {response.text}"
                
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def fix_mathematical_expressions(self, json_str: str) -> str:
        """Fix mathematical expressions in JSON strings that cause parsing errors."""
        import re
        
        fixes = [
            (r'\b1\s*/\s*8\b', '0.125'),    # 1/8 -> 0.125
            (r'\b1\s*/\s*2\b', '0.5'),      # 1/2 -> 0.5  
            (r'\b1\s*/\s*4\b', '0.25'),     # 1/4 -> 0.25
            (r'\b3\s*/\s*4\b', '0.75'),     # 3/4 -> 0.75
            (r'\b1\s*/\s*3\b', '0.333'),    # 1/3 -> 0.333
            (r'\b2\s*/\s*3\b', '0.667'),    # 2/3 -> 0.667
            (r'\b5\s*/\s*8\b', '0.625'),    # 5/8 -> 0.625
            (r'\b7\s*/\s*8\b', '0.875'),    # 7/8 -> 0.875
        ]
        
        fixed_str = json_str
        
        for pattern, replacement in fixes:
            if re.search(pattern, fixed_str):
                fixed_str = re.sub(pattern, replacement, fixed_str)
        
        return fixed_str
    
    def analyze_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single rule for transformation potential."""
        rule_id = rule['code_regulation_id']
        article_summary = self.get_article_summary(rule_id)
        
        # Create analysis prompt
        prompt = self.create_analysis_prompt(rule, article_summary)
        
        # Get LLM analysis
        llm_response = self.call_llm(prompt)
        
        # Try to parse JSON response
        try:
            # Remove markdown code blocks if present
            clean_response = llm_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.startswith('```'):
                clean_response = clean_response[3:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            # Fix mathematical expressions in JSON before parsing
            clean_response = self.fix_mathematical_expressions(clean_response)
            
            llm_analysis = json.loads(clean_response)
        except json.JSONDecodeError as e:
            # Fallback structure if JSON parsing fails
            llm_analysis = {
                "transformability": "UNKNOWN",
                "confidence_level": "LOW",
                "primary_blocking_factors": ["PARSE_ERROR"],
                "quantifiable_elements": [],
                "automation_complexity": "UNKNOWN",
                "reasoning_summary": f"Failed to parse LLM response: {str(e)}",
                "key_validation_checks": [],
                "required_design_inputs": [],
                "automation_limitations": ["Response parsing failed"],
                "estimated_automation_coverage": 0,
                "raw_response": llm_response
            }
        
        # Create assessment structure
        assessment = {
            "rule_id": rule_id,
            "rule_name": rule['code_regulation_name'],
            "rule_content": rule['content'],
            "article_summary": article_summary,
            "llm_analysis": llm_analysis,
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return assessment
    
    def save_assessment(self, assessment: Dict[str, Any]):
        """Save individual rule assessment to JSON file."""
        rule_id = assessment['rule_id'].replace('.', '_')
        filename = f"{self.output_dir}/rule_{rule_id}_assessment.json"
        
        with open(filename, 'w') as f:
            json.dump(assessment, f, indent=2)
    
    def update_progress(self, rule_id: str):
        """Update progress statistics in a thread-safe manner."""
        with self.stats_lock:
            self.completed_count += 1
            elapsed = time.time() - self.start_time
            rate = self.completed_count / elapsed
            remaining = self.total_rules - self.completed_count
            eta = remaining / rate if rate > 0 else 0
            
            progress_pct = (self.completed_count / self.total_rules) * 100
            
            print(f"✓ {rule_id} | Progress: {self.completed_count}/{self.total_rules} ({progress_pct:.1f}%) | "
                  f"Rate: {rate:.1f}/s | ETA: {eta/60:.1f}m")
    
    def process_rule_worker(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Worker function to process a single rule."""
        try:
            assessment = self.analyze_rule(rule)
            self.save_assessment(assessment)
            self.update_progress(rule['code_regulation_id'])
            return assessment
        except Exception as e:
            print(f"❌ Error processing rule {rule['code_regulation_id']}: {e}")
            return None
    
    def analyze_all_rules_streaming(self, max_concurrent: int = 32):
        """
        Analyze all rules using streaming approach.
        Maintains constant flow of requests by immediately sending new ones as others complete.
        """
        self.total_rules = len(self.candidate_rules)
        self.start_time = time.time()
        
        print(f"🚀 STREAMING ANALYSIS STARTED")
        print(f"📊 Configuration:")
        print(f"   Total Rules: {self.total_rules}")
        print(f"   Max Concurrent: {max_concurrent}")
        print(f"   Model: {self.model}")
        print(f"   Strategy: Tit-for-Tat (immediate request replacement)")
        print()
        
        # Create a copy of rules to work with
        remaining_rules = copy.deepcopy(self.candidate_rules)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit initial batch of requests
            futures = {}
            
            # Fill the pipeline with initial requests
            initial_count = min(max_concurrent, len(remaining_rules))
            for _ in range(initial_count):
                if remaining_rules:
                    rule = remaining_rules.pop(0)
                    future = executor.submit(self.process_rule_worker, rule)
                    futures[future] = rule
            
            print(f"🔄 Pipeline initialized with {initial_count} concurrent requests")
            print(f"📈 Streaming progress:")
            
            # Process completions and immediately submit new requests
            while futures:  # Continue while there are active futures
                # Wait for at least one future to complete
                for future in as_completed(futures):
                    rule = futures[future]
                    
                    try:
                        # Get the result (this will raise exception if worker failed)
                        result = future.result()
                        
                        # Immediately submit a new request if more rules remain
                        if remaining_rules:
                            new_rule = remaining_rules.pop(0)
                            new_future = executor.submit(self.process_rule_worker, new_rule)
                            futures[new_future] = new_rule
                        
                    except Exception as e:
                        print(f"❌ Future failed for rule {rule['code_regulation_id']}: {e}")
                    
                    # Remove completed future
                    del futures[future]
                    
                    # Break from inner loop to check while condition
                    break
        
        # Final statistics
        end_time = time.time()
        total_time = end_time - self.start_time
        
        print(f"\n🎉 STREAMING ANALYSIS COMPLETED!")
        print(f"⏱️  Total Time: {total_time/60:.2f} minutes ({total_time:.1f} seconds)")
        print(f"📊 Performance: {self.completed_count/total_time:.1f} rules/second")
        print(f"📂 Output Directory: {self.output_dir}")
        
        # Quick file count verification
        files = [f for f in os.listdir(self.output_dir) if f.endswith('_assessment.json')]
        success_rate = (len(files) / self.total_rules) * 100
        print(f"📄 Files Created: {len(files)}/{self.total_rules} ({success_rate:.1f}% success rate)")
        
        return True

def main():
    """Main function to run the streaming analysis."""
    print("🌊 STREAMING ELECTRICAL CODE RULE ANALYZER")
    print("=" * 60)
    
    # Get OpenRouter API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        api_key = input("Enter your OpenRouter API key: ").strip()
    
    if not api_key:
        print("❌ Error: OpenRouter API key is required")
        return
    
    # Create analyzer
    analyzer = StreamingRuleAnalyzer(api_key)
    
    # Configuration
    max_concurrent = 32  # Adjust based on API rate limits
    
    print(f"🎯 Ready to analyze {len(analyzer.candidate_rules)} rules")
    print(f"⚡ Using streaming strategy with {max_concurrent} concurrent requests")
    
    # Confirm before starting
    response = input(f"\n🤔 Proceed with streaming analysis? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Analysis cancelled.")
        return
    
    try:
        # Run streaming analysis
        analyzer.analyze_all_rules_streaming(max_concurrent=max_concurrent)
        
        print("\n✅ Analysis completed successfully!")
        print("📊 Check the output directory for results.")
        
    except KeyboardInterrupt:
        print(f"\n⏸️  Analysis interrupted by user.")
        print(f"📂 Partial results saved in: {analyzer.output_dir}")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        print(f"📂 Partial results may be in: {analyzer.output_dir}")

if __name__ == "__main__":
    main()
