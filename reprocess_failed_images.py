#!/usr/bin/env python3
"""
Reprocess Failed Images - Fix Parse Errors
"""

import os
import json
from pathlib import Path
from streaming_image_analyzer import StreamingImageAnalyzer

def find_failed_images(results_dir: Path) -> list:
    """Find images that had parse errors in the analysis results."""
    failed_images = []
    
    for json_file in results_dir.glob("*_analysis.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Check if this was a parse error
            if (data.get("analysis", {}).get("page_analysis", {}).get("text_content") == "PARSE_ERROR" or
                "error" in data):
                
                # Extract image path
                image_path = Path(data["image_path"])
                if image_path.exists():
                    failed_images.append(image_path)
                    print(f"Found failed image: {image_path.name}")
                    
                    # Show the error details
                    if "analysis" in data and "additional_notes" in data["analysis"]["page_analysis"]:
                        error_notes = data["analysis"]["page_analysis"]["additional_notes"]
                        print(f"  Error: {error_notes[0] if error_notes else 'Unknown'}")
                    elif "error" in data:
                        print(f"  Error: {data['error']}")
                        
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
    
    return failed_images

def main():
    """Main function to reprocess failed images."""
    print("🔧 REPROCESSING FAILED IMAGES")
    print("=" * 40)
    
    # Get OpenRouter API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        return
    
    # Find the results directory with the most files (full analysis)
    results_dirs = [d for d in Path(".").glob("image_analysis_streaming_*") if d.is_dir()]
    if not results_dirs:
        print("❌ No analysis results directories found")
        return
    
    # Find directory with most JSON files (indicates full analysis)
    latest_results_dir = max(results_dirs, key=lambda d: len(list(d.glob("*.json"))))
    print(f"📂 Checking results in: {latest_results_dir}")
    
    # Find failed images
    failed_images = find_failed_images(latest_results_dir)
    
    if not failed_images:
        print("✅ No failed images found!")
        return
    
    print(f"\n🎯 Found {len(failed_images)} failed images to reprocess:")
    for img in failed_images:
        print(f"   • {img.name}")
    
    # Confirm reprocessing
    response = input(f"\n🤔 Reprocess {len(failed_images)} failed images? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Reprocessing cancelled.")
        return
    
    # Create analyzer with improved error handling
    analyzer = StreamingImageAnalyzer(api_key)
    
    print(f"\n🚀 Reprocessing failed images...")
    
    # Process each failed image
    for i, image_path in enumerate(failed_images, 1):
        print(f"\n[{i}/{len(failed_images)}] Processing {image_path.name}...")
        
        try:
            # Analyze the image
            assessment = analyzer.analyze_image(image_path)
            
            # Save the new result (will overwrite the failed one)
            analyzer.save_assessment(assessment)
            
            # Check if this one succeeded
            success = "error" not in assessment and assessment.get("analysis", {}).get("page_analysis", {}).get("text_content") != "PARSE_ERROR"
            
            if success:
                # Show sample output
                analysis = assessment["analysis"]
                if "page_analysis" in analysis and "text_content" in analysis["page_analysis"]:
                    sample = analysis["page_analysis"]["text_content"][:150]
                    sample = sample.replace('\n', ' ').strip()
                    if len(sample) > 150:
                        sample += "..."
                    print(f"   ✅ Success! Sample: {sample}")
                else:
                    print(f"   ✅ Success! (No sample available)")
            else:
                print(f"   ❌ Still failed")
                if "error" in assessment:
                    print(f"      Error: {assessment['error']}")
                elif "additional_notes" in assessment.get("analysis", {}).get("page_analysis", {}):
                    error_notes = assessment["analysis"]["page_analysis"]["additional_notes"]
                    print(f"      Error: {error_notes[0] if error_notes else 'Unknown'}")
                    
        except Exception as e:
            print(f"   ❌ Exception during reprocessing: {e}")
    
    print(f"\n✅ Reprocessing completed!")
    print(f"📂 Updated results saved in: {analyzer.output_dir}")

if __name__ == "__main__":
    main()
