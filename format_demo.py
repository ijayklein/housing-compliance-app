#!/usr/bin/env python3
"""
Format Demonstration: Same Input, Different Outputs
Shows how Forward Planning and Reverse Validation use identical input formats
"""

import json
from datetime import datetime
from reverse_compliance_validator import ReverseComplianceValidator

def create_sample_project_data():
    """Create sample project data in unified format"""
    return {
        "project_info": {
            "project_name": "Format Demo Project",
            "project_id": "DEMO-FORMAT-001",
            "applicant_name": "Demo Applicant",
            "architect": "Demo Architecture",
            "submission_date": "2025-09-16"
        },
        "site_data": {
            "zone_district": "R-1",
            "lot_area": 7200,
            "lot_width": 72,
            "lot_depth": 110,
            "lot_shape": "standard",
            "corner_lot": False,
            "flag_lot": False
        },
        "building_data": {
            "building_height": 29,
            "gross_floor_area": 3100,
            "floors": {
                "first_floor_area": 1800,
                "second_floor_area": 1300,
                "basement_area": 600,
                "attic_area": 150
            },
            "setbacks": {
                "front_setback": 22,
                "rear_setback": 27,
                "side_setback_left": 7,
                "side_setback_right": 8
            },
            "architectural_features": {
                "porches": [
                    {
                        "type": "front_porch",
                        "area": 100,
                        "height": 11,
                        "covered": True
                    }
                ],
                "bay_windows": [
                    {
                        "projection": 2,
                        "width": 6,
                        "floor": "first"
                    }
                ]
            }
        },
        "parking_data": {
            "parking_spaces": 2,
            "covered_spaces": 2,
            "garage": {
                "type": "attached",
                "size": "2-car",
                "setback_from_street": 22
            },
            "driveway": {
                "width": 12,
                "length": 24,
                "slope": 6
            }
        },
        "accessory_structures": [],
        "special_features": {
            "adu": {
                "present": False
            },
            "below_grade_patio": {
                "present": False
            }
        }
    }

def simulate_forward_planning_output(project_data):
    """Simulate Forward Planning System output"""
    return {
        "planning_response": {
            "project_id": project_data["project_info"]["project_id"],
            "project_name": project_data["project_info"]["project_name"],
            "planning_timestamp": datetime.now().isoformat(),
            "workflow_phase": "Phase 2 - Building Design",
            "current_step": "2.3 Final Design Review",
            "status": "READY_FOR_VALIDATION",
            "guidance": {
                "current_requirements": [
                    {
                        "rule_id": "SB-1",
                        "rule_title": "Front Setback Minimum",
                        "requirement": "Front setback must be ≥ 20 feet",
                        "current_value": project_data["building_data"]["setbacks"]["front_setback"],
                        "status": "COMPLIANT",
                        "guidance": f"Front setback {project_data['building_data']['setbacks']['front_setback']} ft meets requirement"
                    },
                    {
                        "rule_id": "BH-1",
                        "rule_title": "Maximum Building Height",
                        "requirement": "Building height must be ≤ 30 feet",
                        "current_value": project_data["building_data"]["building_height"],
                        "status": "COMPLIANT",
                        "guidance": f"Building height {project_data['building_data']['building_height']} ft within limit"
                    },
                    {
                        "rule_id": "FA-1",
                        "rule_title": "Floor Area Ratio Maximum",
                        "requirement": "FAR must be ≤ 45%",
                        "current_value": round(project_data["building_data"]["gross_floor_area"] / project_data["site_data"]["lot_area"], 3),
                        "status": "COMPLIANT",
                        "guidance": "FAR within acceptable range"
                    }
                ],
                "next_steps": [
                    {
                        "step": 1,
                        "action": "Proceed to reverse validation",
                        "required_inputs": ["Complete project data"],
                        "decision_point": "Validate all requirements before submission"
                    }
                ],
                "design_constraints": {
                    "buildable_envelope": {
                        "max_footprint_area": 4680,  # Based on setbacks
                        "setback_envelope": {
                            "front_min": 20,
                            "rear_min": 25,
                            "side_min": 6
                        }
                    },
                    "height_limits": {
                        "max_building_height": 30,
                        "daylight_plane_compliant": True
                    },
                    "floor_area_limits": {
                        "max_far": 0.45,
                        "max_gfa": round(project_data["site_data"]["lot_area"] * 0.45)
                    }
                }
            },
            "compliance_preview": {
                "anticipated_issues": [],
                "optimization_opportunities": [
                    "Design appears compliant with all major requirements",
                    "Consider architectural features for enhanced design"
                ],
                "readiness_for_validation": "HIGH"
            }
        }
    }

def demonstrate_format_usage():
    """Demonstrate how both systems use the same input format"""
    print("🔄 UNIFIED FORMAT DEMONSTRATION")
    print("=" * 50)
    print("Showing how Forward Planning and Reverse Validation")
    print("use IDENTICAL input format but produce different outputs")
    print()
    
    # Create sample project data
    project_data = create_sample_project_data()
    
    print("📥 UNIFIED INPUT FORMAT")
    print("-" * 25)
    print("Same JSON structure used by BOTH systems:")
    print(json.dumps({
        "project_info": project_data["project_info"],
        "site_data": {k: v for k, v in project_data["site_data"].items() if k in ["zone_district", "lot_area", "lot_width"]},
        "building_data": {k: v for k, v in project_data["building_data"].items() if k in ["building_height", "gross_floor_area"]},
        "...": "additional fields"
    }, indent=2))
    print()
    
    # Simulate Forward Planning output
    planning_output = simulate_forward_planning_output(project_data)
    
    print("📤 FORWARD PLANNING OUTPUT")
    print("-" * 30)
    print("🎯 Purpose: Guide design decisions")
    print("📊 Key Information:")
    print(f"   • Current Phase: {planning_output['planning_response']['workflow_phase']}")
    print(f"   • Status: {planning_output['planning_response']['status']}")
    print(f"   • Requirements Checked: {len(planning_output['planning_response']['guidance']['current_requirements'])}")
    print("   • Guidance Type: Proactive design recommendations")
    print("   • Next Steps: Proceed to validation")
    print()
    
    # Show sample guidance
    print("📋 Sample Guidance:")
    for req in planning_output['planning_response']['guidance']['current_requirements'][:2]:
        print(f"   ✅ {req['rule_title']}: {req['guidance']}")
    print()
    
    # Perform Reverse Validation
    print("📤 REVERSE VALIDATION OUTPUT")
    print("-" * 32)
    print("🎯 Purpose: Validate existing design")
    
    validator = ReverseComplianceValidator()
    validation_results = validator.perform_comprehensive_validation(project_data)
    
    print("📊 Key Information:")
    print(f"   • Overall Status: {validation_results['summary']['overall_status']}")
    print(f"   • Can Proceed: {validation_results['summary']['can_proceed']}")
    print(f"   • Rules Checked: {validation_results['summary']['total_rules_checked']}")
    print(f"   • Compliance Rate: {validation_results['summary']['compliance_percentage']:.1f}%")
    print("   • Output Type: Objective pass/fail results")
    print()
    
    # Compare outputs
    print("⚖️  OUTPUT COMPARISON")
    print("-" * 20)
    
    comparison_table = [
        ["Aspect", "Forward Planning", "Reverse Validation"],
        ["Purpose", "Guide design", "Validate design"],
        ["Input", "Same JSON format", "Same JSON format"],
        ["Processing", "Generate guidance", "Check compliance"],
        ["Output Focus", "Next steps & recommendations", "Pass/fail & violations"],
        ["Rule References", "Same rule_ids", "Same rule_ids"],
        ["Integration", "Feeds into validation", "Validates planning results"]
    ]
    
    for row in comparison_table:
        if row == comparison_table[0]:  # Header
            print(f"{'':>2}{'':>15} | {'':>20} | {'':>25}")
            print(f"{'':>2}{'-'*15} | {'-'*20} | {'-'*25}")
        print(f"{'':>2}{row[0]:>15} | {row[1]:>20} | {row[2]:>25}")
    print()
    
    # Show integration workflow
    print("🔄 INTEGRATION WORKFLOW")
    print("-" * 25)
    workflow_steps = [
        "1. Same project_data.json input",
        "2. Forward Planning → design guidance",
        "3. Update project_data based on guidance", 
        "4. Reverse Validation → compliance check",
        "5. If violations: return to step 2",
        "6. If compliant: proceed to submission"
    ]
    
    for step in workflow_steps:
        print(f"   {step}")
    print()
    
    print("✅ FORMAT BENEFITS:")
    print("   • No data transformation between systems")
    print("   • Consistent rule references enable traceability")
    print("   • Seamless workflow from planning to validation")
    print("   • Single input format for entire project lifecycle")
    print()
    
    # Save sample files
    with open('sample_project_input.json', 'w') as f:
        json.dump(project_data, f, indent=2)
    
    with open('sample_planning_output.json', 'w') as f:
        json.dump(planning_output, f, indent=2)
    
    validation_output = {
        "validation_response": {
            "project_id": project_data["project_info"]["project_id"],
            "project_name": project_data["project_info"]["project_name"],
            "validation_timestamp": datetime.now().isoformat(),
            "overall_status": validation_results['summary']['overall_status'],
            "can_proceed": validation_results['summary']['can_proceed'],
            "summary": validation_results['summary'],
            "detailed_results": validation_results['all_results'][:5]  # Sample results
        }
    }
    
    with open('sample_validation_output.json', 'w') as f:
        json.dump(validation_output, f, indent=2)
    
    print("📄 Sample files generated:")
    print("   • sample_project_input.json - Unified input format")
    print("   • sample_planning_output.json - Forward planning response")
    print("   • sample_validation_output.json - Reverse validation response")

if __name__ == "__main__":
    demonstrate_format_usage()
