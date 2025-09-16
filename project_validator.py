#!/usr/bin/env python3
"""
Simple Housing Project Validator
Demonstrates automated compliance checking based on extracted rules
"""

import json
from typing import Dict, List, Any, Tuple

class HousingProjectValidator:
    def __init__(self):
        self.zone_requirements = {
            'R-1': {'min_area': 6000, 'max_area': 9999, 'min_width': 60, 'min_depth': 100},
            'R-1(7000)': {'min_area': 7000, 'max_area': 13999, 'min_width': 60, 'min_depth': 100},
            'R-1(8000)': {'min_area': 8000, 'max_area': 15999, 'min_width': 60, 'min_depth': 100},
            'R-1(10000)': {'min_area': 10000, 'max_area': 19999, 'min_width': 60, 'min_depth': 100},
            'R-1(20000)': {'min_area': 20000, 'max_area': 39999, 'min_width': 60, 'min_depth': 100}
        }
        
        self.validation_results = []
    
    def validate_lot_requirements(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate basic lot requirements"""
        results = []
        
        zone = project_data.get('zone_district', '')
        lot_area = project_data.get('lot_area', 0)
        lot_width = project_data.get('lot_width', 0)
        lot_depth = project_data.get('lot_depth', 0)
        
        if zone not in self.zone_requirements:
            results.append({
                'rule': 'Zone District Validation',
                'status': 'FAIL',
                'message': f'Invalid zone district: {zone}',
                'critical': True
            })
            return results
        
        req = self.zone_requirements[zone]
        
        # Check lot area
        if lot_area < req['min_area']:
            results.append({
                'rule': 'Minimum Lot Area',
                'status': 'FAIL',
                'message': f'Lot area {lot_area} sf < minimum {req["min_area"]} sf for {zone}',
                'critical': True
            })
        elif lot_area > req['max_area']:
            results.append({
                'rule': 'Maximum Lot Area',
                'status': 'FAIL',
                'message': f'Lot area {lot_area} sf > maximum {req["max_area"]} sf for {zone}',
                'critical': True
            })
        else:
            results.append({
                'rule': 'Lot Area Compliance',
                'status': 'PASS',
                'message': f'Lot area {lot_area} sf within {req["min_area"]}-{req["max_area"]} sf range',
                'critical': False
            })
        
        # Check lot width
        if lot_width < req['min_width']:
            results.append({
                'rule': 'Minimum Lot Width',
                'status': 'FAIL',
                'message': f'Lot width {lot_width} ft < minimum {req["min_width"]} ft',
                'critical': True
            })
        else:
            results.append({
                'rule': 'Lot Width Compliance',
                'status': 'PASS',
                'message': f'Lot width {lot_width} ft >= minimum {req["min_width"]} ft',
                'critical': False
            })
        
        # Check lot depth
        if lot_depth < req['min_depth']:
            results.append({
                'rule': 'Minimum Lot Depth',
                'status': 'FAIL',
                'message': f'Lot depth {lot_depth} ft < minimum {req["min_depth"]} ft',
                'critical': True
            })
        else:
            results.append({
                'rule': 'Lot Depth Compliance',
                'status': 'PASS',
                'message': f'Lot depth {lot_depth} ft >= minimum {req["min_depth"]} ft',
                'critical': False
            })
        
        return results
    
    def validate_setbacks(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate setback requirements"""
        results = []
        
        # Example setback requirements (would be loaded from extracted rules)
        setback_requirements = {
            'front_setback_min': 20,  # feet
            'side_setback_min': 6,    # feet
            'rear_setback_min': 25,   # feet
        }
        
        setbacks = project_data.get('setbacks', {})
        
        for setback_type, min_required in setback_requirements.items():
            actual_setback = setbacks.get(setback_type.replace('_min', ''), 0)
            
            if actual_setback < min_required:
                results.append({
                    'rule': f'{setback_type.replace("_", " ").title()}',
                    'status': 'FAIL',
                    'message': f'{setback_type.replace("_", " ").title()} {actual_setback} ft < minimum {min_required} ft',
                    'critical': True
                })
            else:
                results.append({
                    'rule': f'{setback_type.replace("_", " ").title()}',
                    'status': 'PASS',
                    'message': f'{setback_type.replace("_", " ").title()} {actual_setback} ft >= minimum {min_required} ft',
                    'critical': False
                })
        
        return results
    
    def validate_building_height(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate building height requirements"""
        results = []
        
        max_height = 30  # feet (typical for single-family)
        building_height = project_data.get('building_height', 0)
        
        if building_height > max_height:
            results.append({
                'rule': 'Maximum Building Height',
                'status': 'FAIL',
                'message': f'Building height {building_height} ft > maximum {max_height} ft',
                'critical': True
            })
        else:
            results.append({
                'rule': 'Building Height Compliance',
                'status': 'PASS',
                'message': f'Building height {building_height} ft <= maximum {max_height} ft',
                'critical': False
            })
        
        return results
    
    def validate_floor_area(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate floor area ratio requirements"""
        results = []
        
        max_far = 0.45  # 45% typical FAR
        lot_area = project_data.get('lot_area', 1)
        gross_floor_area = project_data.get('gross_floor_area', 0)
        
        actual_far = gross_floor_area / lot_area if lot_area > 0 else 0
        
        if actual_far > max_far:
            results.append({
                'rule': 'Floor Area Ratio (FAR)',
                'status': 'FAIL',
                'message': f'FAR {actual_far:.3f} ({gross_floor_area} sf / {lot_area} sf) > maximum {max_far}',
                'critical': True
            })
        else:
            results.append({
                'rule': 'Floor Area Ratio Compliance',
                'status': 'PASS',
                'message': f'FAR {actual_far:.3f} <= maximum {max_far}',
                'critical': False
            })
        
        return results
    
    def validate_parking(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate parking requirements"""
        results = []
        
        required_spaces = 2  # Typical for single-family
        provided_spaces = project_data.get('parking_spaces', 0)
        
        if provided_spaces < required_spaces:
            results.append({
                'rule': 'Minimum Parking Spaces',
                'status': 'FAIL',
                'message': f'Provided {provided_spaces} spaces < required {required_spaces} spaces',
                'critical': True
            })
        else:
            results.append({
                'rule': 'Parking Space Compliance',
                'status': 'PASS',
                'message': f'Provided {provided_spaces} spaces >= required {required_spaces} spaces',
                'critical': False
            })
        
        return results
    
    def validate_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete project validation"""
        print(f"🏗️ VALIDATING PROJECT: {project_data.get('project_name', 'Unnamed')}")
        print("=" * 60)
        
        all_results = []
        
        # Run all validation checks
        all_results.extend(self.validate_lot_requirements(project_data))
        all_results.extend(self.validate_setbacks(project_data))
        all_results.extend(self.validate_building_height(project_data))
        all_results.extend(self.validate_floor_area(project_data))
        all_results.extend(self.validate_parking(project_data))
        
        # Summarize results
        total_checks = len(all_results)
        passed_checks = len([r for r in all_results if r['status'] == 'PASS'])
        failed_checks = len([r for r in all_results if r['status'] == 'FAIL'])
        critical_failures = len([r for r in all_results if r['status'] == 'FAIL' and r['critical']])
        
        # Display results
        print(f"📊 VALIDATION SUMMARY:")
        print(f"   Total Checks: {total_checks}")
        print(f"   ✅ Passed: {passed_checks}")
        print(f"   ❌ Failed: {failed_checks}")
        print(f"   🚨 Critical Failures: {critical_failures}")
        
        overall_status = "FAIL" if critical_failures > 0 else "PASS"
        print(f"   🎯 Overall Status: {overall_status}")
        
        print(f"\\n📋 DETAILED RESULTS:")
        for result in all_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            critical_flag = " 🚨" if result.get('critical', False) else ""
            print(f"   {status_icon} {result['rule']}: {result['message']}{critical_flag}")
        
        return {
            'project_name': project_data.get('project_name', 'Unnamed'),
            'overall_status': overall_status,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'critical_failures': critical_failures,
            'detailed_results': all_results,
            'can_proceed': critical_failures == 0
        }

def main():
    print("🏠 HOUSING PROJECT VALIDATOR - DEMO")
    print("=" * 50)
    
    # Example project data
    sample_projects = [
        {
            'project_name': 'Smith Residence - COMPLIANT',
            'zone_district': 'R-1',
            'lot_area': 7500,  # sf
            'lot_width': 75,   # ft
            'lot_depth': 120,  # ft
            'setbacks': {
                'front_setback': 25,
                'side_setback': 8,
                'rear_setback': 30
            },
            'building_height': 28,      # ft
            'gross_floor_area': 3200,   # sf
            'parking_spaces': 2
        },
        {
            'project_name': 'Jones Residence - NON-COMPLIANT',
            'zone_district': 'R-1',
            'lot_area': 5500,  # sf - TOO SMALL
            'lot_width': 55,   # ft - TOO NARROW
            'lot_depth': 95,   # ft - TOO SHALLOW
            'setbacks': {
                'front_setback': 15,  # TOO SMALL
                'side_setback': 4,    # TOO SMALL
                'rear_setback': 20    # TOO SMALL
            },
            'building_height': 35,      # ft - TOO TALL
            'gross_floor_area': 4000,   # sf - TOO LARGE
            'parking_spaces': 1        # TOO FEW
        }
    ]
    
    validator = HousingProjectValidator()
    
    for project in sample_projects:
        validation_result = validator.validate_project(project)
        
        print(f"\\n{'🎉 PROJECT CAN PROCEED' if validation_result['can_proceed'] else '🛑 PROJECT CANNOT PROCEED'}")
        print("=" * 60)
        print()

if __name__ == "__main__":
    main()
