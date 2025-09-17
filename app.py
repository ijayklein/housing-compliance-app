#!/usr/bin/env python3
"""
Housing Compliance Web Application
Flask app with Planning and Validation modes
"""

from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime
from pathlib import Path
from reverse_compliance_validator import ReverseComplianceValidator

app = Flask(__name__)
app.secret_key = 'housing_compliance_secret_key_2025'

# Initialize validator
validator = ReverseComplianceValidator()

# Zone configuration
ZONE_CONFIG = {
    'R-1': {'min_area': 6000, 'max_area': 9999, 'min_width': 60, 'min_depth': 100, 'max_height': 30, 'max_far': 0.45},
    'R-1(7000)': {'min_area': 7000, 'max_area': 13999, 'min_width': 60, 'min_depth': 100, 'max_height': 30, 'max_far': 0.45},
    'R-1(8000)': {'min_area': 8000, 'max_area': 15999, 'min_width': 60, 'min_depth': 100, 'max_height': 30, 'max_far': 0.45},
    'R-1(10000)': {'min_area': 10000, 'max_area': 19999, 'min_width': 60, 'min_depth': 100, 'max_height': 30, 'max_far': 0.45},
    'R-1(20000)': {'min_area': 20000, 'max_area': 39999, 'min_width': 60, 'min_depth': 100, 'max_height': 30, 'max_far': 0.45}
}

@app.route('/')
def index():
    """Main page with mode selection"""
    return render_template('index.html')

@app.route('/planning')
def planning_mode():
    """Planning mode interface"""
    return render_template('planning.html', zones=ZONE_CONFIG.keys())

@app.route('/validation')
def validation_mode():
    """Validation mode interface"""
    return render_template('validation.html', zones=ZONE_CONFIG.keys())

@app.route('/api/zone-requirements/<zone>')
def get_zone_requirements(zone):
    """Get requirements for a specific zone"""
    if zone in ZONE_CONFIG:
        return jsonify(ZONE_CONFIG[zone])
    return jsonify({'error': 'Invalid zone'}), 400

@app.route('/api/plan-project', methods=['POST'])
def plan_project():
    """Forward planning API endpoint"""
    try:
        project_data = request.json
        
        # Validate required fields
        required_fields = ['site_data', 'project_info']
        for field in required_fields:
            if field not in project_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate planning guidance
        planning_result = generate_planning_guidance(project_data)
        
        # Store in session for later use
        session['current_project'] = project_data
        session['planning_result'] = planning_result
        
        return jsonify(planning_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate-project', methods=['POST'])
def validate_project():
    """Reverse validation API endpoint"""
    try:
        project_data = request.json
        
        # Validate required fields
        required_fields = ['site_data', 'building_data', 'parking_data']
        for field in required_fields:
            if field not in project_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Perform validation
        validation_results = validator.perform_comprehensive_validation(project_data)
        
        # Format for web response
        web_response = format_validation_response(validation_results)
        
        # Store in session
        session['current_project'] = project_data
        session['validation_result'] = web_response
        
        return jsonify(web_response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-template/<zone>')
def get_project_template(zone):
    """Get a project template for the specified zone"""
    if zone not in ZONE_CONFIG:
        return jsonify({'error': 'Invalid zone'}), 400
    
    template = {
        "project_info": {
            "project_name": "",
            "project_id": "",
            "applicant_name": "",
            "architect": "",
            "submission_date": datetime.now().strftime("%Y-%m-%d")
        },
        "site_data": {
            "zone_district": zone,
            "lot_area": ZONE_CONFIG[zone]['min_area'],
            "lot_width": ZONE_CONFIG[zone]['min_width'],
            "lot_depth": ZONE_CONFIG[zone]['min_depth'],
            "lot_shape": "standard",
            "corner_lot": False,
            "flag_lot": False
        },
        "building_data": {
            "building_height": 25,
            "gross_floor_area": int(ZONE_CONFIG[zone]['min_area'] * 0.4),
            "floors": {
                "first_floor_area": int(ZONE_CONFIG[zone]['min_area'] * 0.25),
                "second_floor_area": int(ZONE_CONFIG[zone]['min_area'] * 0.15),
                "basement_area": 0,
                "attic_area": 0
            },
            "setbacks": {
                "front_setback": 20,
                "rear_setback": 25,
                "side_setback_left": 6,
                "side_setback_right": 6
            },
            "architectural_features": {
                "porches": [],
                "bay_windows": []
            }
        },
        "parking_data": {
            "parking_spaces": 2,
            "covered_spaces": 2,
            "garage": {
                "type": "attached",
                "size": "2-car",
                "setback_from_street": 20
            },
            "driveway": {
                "width": 12,
                "length": 20,
                "slope": 5
            }
        },
        "accessory_structures": [],
        "special_features": {
            "adu": {"present": False},
            "below_grade_patio": {"present": False}
        }
    }
    
    return jsonify(template)

def generate_planning_guidance(project_data):
    """Generate forward planning guidance"""
    site_data = project_data.get('site_data', {})
    zone = site_data.get('zone_district', 'R-1')
    
    if zone not in ZONE_CONFIG:
        return {'error': 'Invalid zone district'}
    
    zone_req = ZONE_CONFIG[zone]
    guidance = {
        'project_id': project_data.get('project_info', {}).get('project_id', 'UNKNOWN'),
        'project_name': project_data.get('project_info', {}).get('project_name', 'Unnamed Project'),
        'planning_timestamp': datetime.now().isoformat(),
        'workflow_phase': 'Phase 1 - Site Analysis',
        'zone_district': zone,
        'status': 'IN_PROGRESS',
        'guidance': {
            'site_requirements': [
                {
                    'category': 'Lot Dimensions',
                    'requirements': [
                        f"Minimum lot area: {zone_req['min_area']:,} sf",
                        f"Maximum lot area: {zone_req['max_area']:,} sf", 
                        f"Minimum width: {zone_req['min_width']} ft",
                        f"Minimum depth: {zone_req['min_depth']} ft"
                    ],
                    'current_values': {
                        'lot_area': site_data.get('lot_area', 0),
                        'lot_width': site_data.get('lot_width', 0),
                        'lot_depth': site_data.get('lot_depth', 0)
                    },
                    'compliance_status': check_site_compliance(site_data, zone_req)
                },
                {
                    'category': 'Building Envelope',
                    'requirements': [
                        f"Maximum building height: {zone_req['max_height']} ft",
                        f"Maximum FAR: {zone_req['max_far']} ({zone_req['max_far']*100}%)",
                        "Minimum setbacks: Front 20', Rear 25', Side 6' each"
                    ],
                    'buildable_area': calculate_buildable_area(site_data),
                    'max_floor_area': int(site_data.get('lot_area', 0) * zone_req['max_far'])
                },
                {
                    'category': 'Parking Requirements',
                    'requirements': [
                        "Minimum parking spaces: 2 spaces per dwelling unit",
                        "At least 1 covered space required",
                        "Parking spaces: 9' × 18' minimum each",
                        "Driveway width: 12' minimum for single car, 20' for double"
                    ],
                    'recommendations': {
                        'total_spaces': 2,
                        'covered_spaces': 1,
                        'garage_recommended': True,
                        'driveway_width': 12
                    }
                }
            ],
            'next_steps': generate_next_steps(site_data, zone_req),
            'design_constraints': {
                'zone_requirements': zone_req,
                'critical_dimensions': {
                    'max_footprint': calculate_max_footprint(site_data),
                    'max_gfa': int(site_data.get('lot_area', 0) * zone_req['max_far'])
                }
            }
        },
        'recommendations': generate_recommendations(site_data, zone_req)
    }
    
    return guidance

def check_site_compliance(site_data, zone_req):
    """Check if site meets basic requirements"""
    lot_area = site_data.get('lot_area', 0)
    lot_width = site_data.get('lot_width', 0)
    lot_depth = site_data.get('lot_depth', 0)
    
    issues = []
    if lot_area < zone_req['min_area']:
        issues.append(f"Lot area {lot_area:,} sf < minimum {zone_req['min_area']:,} sf")
    if lot_area > zone_req['max_area']:
        issues.append(f"Lot area {lot_area:,} sf > maximum {zone_req['max_area']:,} sf")
    if lot_width < zone_req['min_width']:
        issues.append(f"Lot width {lot_width} ft < minimum {zone_req['min_width']} ft")
    if lot_depth < zone_req['min_depth']:
        issues.append(f"Lot depth {lot_depth} ft < minimum {zone_req['min_depth']} ft")
    
    return {
        'compliant': len(issues) == 0,
        'issues': issues
    }

def calculate_buildable_area(site_data):
    """Calculate buildable area based on setbacks"""
    lot_width = site_data.get('lot_width', 0)
    lot_depth = site_data.get('lot_depth', 0)
    
    # Standard setbacks
    front_setback = 20
    rear_setback = 25
    side_setbacks = 6 * 2  # Both sides
    
    buildable_width = max(0, lot_width - side_setbacks)
    buildable_depth = max(0, lot_depth - front_setback - rear_setback)
    buildable_area = buildable_width * buildable_depth
    
    return {
        'width': buildable_width,
        'depth': buildable_depth,
        'area': buildable_area
    }

def calculate_max_footprint(site_data):
    """Calculate maximum building footprint"""
    buildable = calculate_buildable_area(site_data)
    return buildable['area']

def generate_next_steps(site_data, zone_req):
    """Generate next steps based on current project state"""
    compliance = check_site_compliance(site_data, zone_req)
    
    if not compliance['compliant']:
        return [
            {
                'step': 1,
                'action': 'Resolve site compliance issues',
                'description': 'Address the following issues: ' + '; '.join(compliance['issues']),
                'required': True,
                'phase': 'Phase 1 - Site Analysis'
            }
        ]
    
    return [
        {
            'step': 1,
            'action': 'Proceed to building design',
            'description': 'Site meets basic requirements. Begin building envelope design.',
            'required': True,
            'phase': 'Phase 2 - Building Design'
        },
        {
            'step': 2,
            'action': 'Design within buildable envelope',
            'description': f"Maximum footprint: {calculate_max_footprint(site_data):,} sf",
            'required': True,
            'phase': 'Phase 2 - Building Design'
        }
    ]

def generate_recommendations(site_data, zone_req):
    """Generate design recommendations"""
    recommendations = []
    
    lot_area = site_data.get('lot_area', 0)
    max_gfa = int(lot_area * zone_req['max_far'])
    
    recommendations.append({
        'category': 'Floor Area Planning',
        'message': f"Maximum allowed GFA: {max_gfa:,} sf ({zone_req['max_far']*100}% of lot area)",
        'priority': 'HIGH'
    })
    
    buildable = calculate_buildable_area(site_data)
    recommendations.append({
        'category': 'Building Footprint',
        'message': f"Maximum ground floor footprint: {buildable['area']:,} sf",
        'priority': 'HIGH'
    })
    
    if lot_area > zone_req['min_area'] * 1.2:
        recommendations.append({
            'category': 'Design Opportunity',
            'message': 'Lot size allows for flexible design options',
            'priority': 'MEDIUM'
        })
    
    return recommendations

def format_validation_response(validation_results):
    """Format validation results for web display"""
    summary = validation_results['summary']
    all_results = validation_results['all_results']
    
    # Categorize results
    violations = [r for r in all_results if r['status'] == 'VIOLATION']
    warnings = [r for r in all_results if r['status'] == 'WARNING']
    compliant = [r for r in all_results if r['status'] == 'COMPLIANT']
    
    # Group by category
    results_by_category = {}
    for result in all_results:
        category = result.get('violation_type', 'general')
        if category not in results_by_category:
            results_by_category[category] = []
        results_by_category[category].append(result)
    
    return {
        'validation_timestamp': summary['validation_timestamp'],
        'project_name': summary['project_name'],
        'overall_status': summary['overall_status'],
        'can_proceed': summary['can_proceed'],
        'summary_stats': {
            'total_rules_checked': summary['total_rules_checked'],
            'compliant_rules': summary['compliant_rules'],
            'violations': summary['violations'],
            'warnings': summary['warnings'],
            'critical_violations': summary['critical_violations'],
            'compliance_percentage': summary['compliance_percentage']
        },
        'results_by_category': results_by_category,
        'critical_violations': [r for r in violations if r.get('criticality') == 'CRITICAL'],
        'all_violations': violations,
        'warnings': warnings,
        'compliant_items': compliant[:10]  # Limit for display
    }

if __name__ == '__main__':
    import os
    
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    static_dir = Path(__file__).parent / 'static'
    static_dir.mkdir(exist_ok=True)
    
    # Get port from environment (for deployment) or default to 5001
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    print("🌐 Starting Housing Compliance Web Application...")
    print("📁 Templates directory: templates/")
    print("📁 Static files directory: static/")
    print(f"🚀 Access the application at: http://localhost:{port}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
