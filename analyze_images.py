#!/usr/bin/env python3

import os
import base64
import json
import requests
from pathlib import Path

class CityPlanningImageAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-sonnet-4"
        
    def encode_image(self, image_path):
        """Encode image to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def create_analysis_prompt(self):
        """Create detailed prompt for city planning rule analysis"""
        return """You are analyzing photocopied pages from a city planning technical manual. These images contain crucial zoning rules, regulations, and technical specifications that must be captured with absolute precision.

CRITICAL REQUIREMENTS:
1. Extract ALL text content verbatim, preserving exact formatting, spacing, and structure
2. Identify and describe ALL figures, diagrams, charts, tables, and visual elements in detail
3. Capture ALL numerical values, measurements, percentages, and technical specifications
4. Document ALL section headings, subheadings, bullet points, and hierarchical structure
5. Note any handwritten annotations, stamps, or markings
6. Describe the overall layout and organization of the page
7. Identify any references to other sections, pages, or documents

FORMAT YOUR RESPONSE AS:
## PAGE ANALYSIS

### TEXT CONTENT
[Provide complete verbatim transcription of all text, maintaining original formatting]

### VISUAL ELEMENTS
[Describe all figures, diagrams, tables, charts with detailed explanations of what they show]

### TECHNICAL SPECIFICATIONS
[List all measurements, percentages, numerical values, and technical requirements]

### STRUCTURAL ELEMENTS
[Document headings, sections, subsections, and organizational structure]

### ADDITIONAL NOTES
[Any handwritten notes, stamps, quality issues, or other observations]

Be exhaustive and precise - missing information could impact critical city planning decisions."""

    def analyze_image(self, image_path):
        """Analyze a single image using OpenRouter API"""
        
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.create_analysis_prompt()
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
            "max_tokens": 4000,
            "temperature": 0.1
        }
        
        # Make request
        response = requests.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def analyze_images(self, image_paths):
        """Analyze multiple images and return results"""
        results = {}
        
        for image_path in image_paths:
            print(f"Analyzing {image_path}...")
            try:
                analysis = self.analyze_image(image_path)
                results[str(image_path)] = {
                    "status": "success",
                    "analysis": analysis
                }
                # Show sample of response for interim reporting
                sample = analysis[:200] + "..." if len(analysis) > 200 else analysis
                print(f"Sample output: {sample}")
                print("-" * 50)
            except Exception as e:
                results[str(image_path)] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"Error analyzing {image_path}: {e}")
        
        return results
    
    def save_results(self, results, output_file):
        """Save analysis results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

def main():
    # Get API key from environment
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set your OpenRouter API key:")
        print("export OPENROUTER_API_KEY='your-actual-api-key'")
        print("Get your API key from: https://openrouter.ai/keys")
        return
    
    # Initialize analyzer
    analyzer = CityPlanningImageAnalyzer(api_key)
    
    # Define test images
    base_path = Path(__file__).parent / "pngs"
    test_images = [
        base_path / "Page_08.png",
        base_path / "Page_33.png"
    ]
    
    # Verify images exist
    for img_path in test_images:
        if not img_path.exists():
            print(f"Error: Image not found: {img_path}")
            return
    
    print("Starting city planning rule image analysis...")
    print(f"Using model: {analyzer.model}")
    print(f"Images to analyze: {len(test_images)}")
    print("=" * 60)
    
    # Analyze images
    results = analyzer.analyze_images(test_images)
    
    # Save results
    output_file = "analysis_results.json"
    analyzer.save_results(results, output_file)
    
    print(f"\nAnalysis complete. Results saved to {output_file}")
    
    # Print summary
    successful = sum(1 for r in results.values() if r["status"] == "success")
    failed = len(results) - successful
    print(f"Successfully analyzed: {successful} images")
    print(f"Failed: {failed} images")

if __name__ == "__main__":
    main()
