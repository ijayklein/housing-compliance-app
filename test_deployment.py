#!/usr/bin/env python3
"""
Test Deployment Setup
Verify all deployment files are ready
"""

import os
import json
from pathlib import Path

def check_deployment_files():
    """Check if all deployment files exist and are valid"""
    print("🔍 CHECKING DEPLOYMENT READINESS")
    print("=" * 40)
    
    files_to_check = {
        'render.yaml': 'Render platform config',
        'Procfile': 'Heroku deployment file',
        'Dockerfile': 'Docker container config',
        'railway.json': 'Railway platform config',
        '.gitignore': 'Git ignore file',
        'requirements.txt': 'Python dependencies',
        'app.py': 'Main Flask application',
        'templates/base.html': 'Base HTML template',
        'static/css/style.css': 'CSS styles',
        'static/js/app.js': 'JavaScript functionality'
    }
    
    missing_files = []
    for file, description in files_to_check.items():
        if Path(file).exists():
            print(f"✅ {file:20} - {description}")
        else:
            print(f"❌ {file:20} - {description}")
            missing_files.append(file)
    
    # Check rules directory
    rules_dirs = list(Path('.').glob('rules_extraction_v3_*'))
    if rules_dirs:
        print(f"✅ {'rules directory':20} - {rules_dirs[0]}")
    else:
        print(f"❌ {'rules directory':20} - rules_extraction_v3_*")
        missing_files.append('rules_extraction_v3_*')
    
    print()
    if missing_files:
        print(f"❌ Missing {len(missing_files)} files for deployment!")
        return False
    else:
        print("✅ All deployment files ready!")
        return True

def validate_json_configs():
    """Validate JSON configuration files"""
    print("\n🔧 VALIDATING CONFIGURATIONS")
    print("=" * 35)
    
    json_files = {
        'railway.json': 'Railway configuration'
    }
    
    for file, description in json_files.items():
        try:
            with open(file, 'r') as f:
                json.load(f)
            print(f"✅ {file:15} - Valid JSON")
        except FileNotFoundError:
            print(f"❌ {file:15} - File not found")
        except json.JSONDecodeError as e:
            print(f"❌ {file:15} - Invalid JSON: {e}")

def check_app_config():
    """Check Flask app configuration"""
    print("\n⚙️  CHECKING APP CONFIGURATION")
    print("=" * 35)
    
    try:
        # Import app to check for syntax errors
        import app
        print("✅ app.py         - Imports successfully")
        
        # Check if app has production-ready port handling
        with open('app.py', 'r') as f:
            content = f.read()
            
        if 'os.environ.get(\'PORT\'' in content:
            print("✅ Port handling  - Production ready")
        else:
            print("⚠️  Port handling  - May need environment PORT support")
            
        if 'FLASK_DEBUG' in content:
            print("✅ Debug config   - Environment variable support")
        else:
            print("⚠️  Debug config   - Consider adding FLASK_DEBUG support")
            
    except ImportError as e:
        print(f"❌ app.py         - Import error: {e}")
    except Exception as e:
        print(f"❌ app.py         - Error: {e}")

def show_deployment_options():
    """Show available deployment options"""
    print("\n🚀 DEPLOYMENT OPTIONS")
    print("=" * 25)
    
    platforms = [
        {
            'name': 'Render',
            'config': 'render.yaml',
            'url': 'https://render.com',
            'free_tier': '750 hours/month',
            'setup_time': '5 minutes'
        },
        {
            'name': 'Railway', 
            'config': 'railway.json',
            'url': 'https://railway.app',
            'free_tier': '$5 credit/month',
            'setup_time': '3 minutes'
        },
        {
            'name': 'Heroku',
            'config': 'Procfile',
            'url': 'https://heroku.com',
            'free_tier': 'Limited',
            'setup_time': '10 minutes'
        },
        {
            'name': 'Google Cloud Run',
            'config': 'Dockerfile',
            'url': 'https://cloud.google.com/run',
            'free_tier': '2M requests/month',
            'setup_time': '15 minutes'
        }
    ]
    
    for platform in platforms:
        config_status = "✅" if Path(platform['config']).exists() else "❌"
        print(f"\n{platform['name']}:")
        print(f"  Config: {config_status} {platform['config']}")
        print(f"  URL: {platform['url']}")
        print(f"  Free tier: {platform['free_tier']}")
        print(f"  Setup time: {platform['setup_time']}")

def show_next_steps():
    """Show next steps for deployment"""
    print("\n📋 NEXT STEPS FOR DEPLOYMENT")
    print("=" * 35)
    
    steps = [
        "1. Choose a platform (Render recommended for beginners)",
        "2. Create GitHub repository and push code",
        "3. Connect platform to your GitHub repo",
        "4. Configure environment variables if needed",
        "5. Deploy and test your live application",
        "6. Optional: Set up custom domain"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print(f"\n📖 Detailed instructions in: DEPLOYMENT_GUIDE.md")

def main():
    """Main test function"""
    print("🌐 DEPLOYMENT READINESS CHECK")
    print("Housing Compliance Web Application")
    print("=" * 50)
    
    # Check deployment files
    files_ready = check_deployment_files()
    
    # Validate configurations
    validate_json_configs()
    
    # Check app configuration
    check_app_config()
    
    # Show deployment options
    show_deployment_options()
    
    # Show next steps
    show_next_steps()
    
    print("\n" + "=" * 50)
    if files_ready:
        print("🎉 READY FOR DEPLOYMENT!")
        print("\nRecommended: GitHub + Render (5 minutes, free)")
        print("1. Push to GitHub: git add . && git commit -m 'Deploy' && git push")
        print("2. Go to render.com and connect your repo")
        print("3. Deploy automatically with render.yaml")
    else:
        print("❌ NOT READY - Missing required files")
    
    print(f"\n📄 Full deployment guide: DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    main()
