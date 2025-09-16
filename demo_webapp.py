#!/usr/bin/env python3
"""
Web Application Demo Script
Shows the complete functionality of the Housing Compliance Web Application
"""

import json
import time
import subprocess
import webbrowser
from pathlib import Path

def check_prerequisites():
    """Check if all required files exist"""
    print("🔍 Checking Prerequisites...")
    print("-" * 30)
    
    required_files = [
        'app.py',
        'reverse_compliance_validator.py',
        'templates/base.html',
        'templates/index.html', 
        'templates/planning.html',
        'templates/validation.html',
        'static/css/style.css',
        'static/js/app.js',
        'requirements.txt',
        'start_webapp.sh'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
            print(f"❌ Missing: {file}")
        else:
            print(f"✅ Found: {file}")
    
    # Check for rules directory
    rules_dirs = list(Path('.').glob('rules_extraction_v3_*'))
    if not rules_dirs:
        print("❌ Missing: Rules extraction directory")
        missing_files.append("rules_extraction_v3_*")
    else:
        print(f"✅ Found: {rules_dirs[0]}")
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files!")
        return False
    
    print(f"\n✅ All prerequisites satisfied!")
    return True

def show_application_features():
    """Display application features"""
    print("\n🌟 WEB APPLICATION FEATURES")
    print("=" * 40)
    
    features = {
        "🏗️ Planning Mode": [
            "Proactive design guidance for new projects",
            "Site qualification assessment with zone requirements", 
            "Building envelope calculation with constraints",
            "Design recommendations and optimization tips",
            "Real-time compliance preview during design"
        ],
        "🔍 Validation Mode": [
            "Comprehensive compliance checking (160 rules)",
            "Detailed violation reports with measurements",
            "Compliance percentage scoring with visuals",
            "Remediation recommendations for fixes", 
            "Critical path identification for stoppers"
        ],
        "💻 User Interface": [
            "Responsive Bootstrap design (all devices)",
            "Attractive visual presentation with modern styling",
            "Configurable input forms with templates",
            "Interactive results with charts and progress bars",
            "Export/import functionality for project data"
        ]
    }
    
    for category, items in features.items():
        print(f"\n{category}")
        for item in items:
            print(f"   • {item}")

def show_technical_specs():
    """Display technical specifications"""
    print("\n🔧 TECHNICAL SPECIFICATIONS")
    print("=" * 35)
    
    specs = {
        "Backend": [
            "Flask 3.0.0 web framework",
            "RESTful API design with JSON",
            "Session management for state",
            "Integration with validation engine"
        ],
        "Frontend": [
            "Bootstrap 5 responsive UI",
            "Vanilla JavaScript (no frameworks)",
            "Local storage for persistence", 
            "Fetch API for async communication"
        ],
        "Data Processing": [
            "160 extracted zoning rules",
            "5 zone districts supported",
            "Unified JSON input/output format",
            "Real-time compliance calculation"
        ]
    }
    
    for category, items in specs.items():
        print(f"\n{category}:")
        for item in items:
            print(f"   • {item}")

def demonstrate_api_endpoints():
    """Show available API endpoints"""
    print("\n🌐 API ENDPOINTS")
    print("=" * 20)
    
    endpoints = [
        ("GET", "/", "Home page with mode selection"),
        ("GET", "/planning", "Planning mode interface"),
        ("GET", "/validation", "Validation mode interface"),
        ("GET", "/api/zone-requirements/<zone>", "Zone-specific requirements"),
        ("GET", "/api/project-template/<zone>", "Pre-filled project templates"),
        ("POST", "/api/plan-project", "Generate planning guidance"),
        ("POST", "/api/validate-project", "Perform compliance validation")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"   {method:4} {endpoint:35} - {description}")

def show_sample_data():
    """Display sample input/output data"""
    print("\n📊 SAMPLE DATA FORMATS")
    print("=" * 25)
    
    print("\n📥 INPUT FORMAT (JSON):")
    sample_input = {
        "project_info": {
            "project_name": "Demo Project",
            "project_id": "DEMO-2025-001"
        },
        "site_data": {
            "zone_district": "R-1",
            "lot_area": 7500,
            "lot_width": 75,
            "lot_depth": 120
        },
        "building_data": {
            "building_height": 28,
            "gross_floor_area": 3200,
            "setbacks": {
                "front_setback": 25,
                "rear_setback": 30,
                "side_setback_left": 8,
                "side_setback_right": 10
            }
        },
        "parking_data": {
            "parking_spaces": 2
        }
    }
    print(json.dumps(sample_input, indent=2))
    
    print("\n📤 PLANNING OUTPUT:")
    print("   • Design guidance with requirements")
    print("   • Next steps with specific actions")
    print("   • Buildable envelope calculations")
    print("   • Recommendations for optimization")
    
    print("\n📤 VALIDATION OUTPUT:")
    print("   • Overall compliance status")
    print("   • Detailed results for each rule")
    print("   • Violation reports with measurements")
    print("   • Compliance percentage and statistics")

def launch_application():
    """Launch the web application"""
    print("\n🚀 LAUNCHING WEB APPLICATION")
    print("=" * 35)
    
    print("Starting Flask server...")
    print("📍 URL: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("\n" + "="*50)
    
    try:
        # Start the Flask application
        subprocess.run(['python', 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start server: {e}")
    except FileNotFoundError:
        print("\n❌ Python not found. Please ensure Python is installed and in PATH.")

def main():
    """Main demo function"""
    print("🌐 HOUSING COMPLIANCE WEB APPLICATION DEMO")
    print("=" * 50)
    print("Complete web application with Planning and Validation modes")
    print("Based on 160 extracted rules from Palo Alto zoning manual")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Cannot proceed without required files.")
        return
    
    # Show features
    show_application_features()
    
    # Show technical specs
    show_technical_specs()
    
    # Show API endpoints
    demonstrate_api_endpoints()
    
    # Show sample data
    show_sample_data()
    
    # Launch application
    print("\n" + "="*50)
    response = input("🤔 Launch the web application now? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        launch_application()
    else:
        print("\n📋 To launch manually, run:")
        print("   ./start_webapp.sh")
        print("   OR")
        print("   python app.py")
        print("\n🌐 Then visit: http://localhost:5000")
    
    print("\n✅ Demo complete!")
    print("\n📄 Documentation available in:")
    print("   • WEBAPP_README.md - Complete user guide")
    print("   • UNIFIED_FORMATS.md - Input/output specifications")
    print("   • housing_project_compliance_workflow.md - Planning workflow")

if __name__ == "__main__":
    main()
