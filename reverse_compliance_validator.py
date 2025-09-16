#!/usr/bin/env python3
"""
Reverse Compliance Validator
Takes existing project data and validates against all extracted zoning rules
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

class ReverseComplianceValidator:
    def __init__(self, rules_directory: str = "rules_extraction_v3_20250916_161035"):
        self.rules_directory = Path(rules_directory)
        self.all_rules = []
        self.zone_requirements = {
            'R-1': {'min_area': 6000, 'max_area': 9999, 'min_width': 60, 'min_depth': 100},
            'R-1(7000)': {'min_area': 7000, 'max_area': 13999, 'min_width': 60, 'min_depth': 100},
            'R-1(8000)': {'min_area': 8000, 'max_area': 15999, 'min_width': 60, 'min_depth': 100},
            'R-1(10000)': {'min_area': 10000, 'max_area': 19999, 'min_width': 60, 'min_depth': 100},
            'R-1(20000)': {'min_area': 20000, 'max_area': 39999, 'min_width': 60, 'min_depth': 100}
        }
        self.load_rules()
        print(f"🔍 Reverse Validator initialized with {len(self.all_rules)} rules")
    
    def load_rules(self):
        """Load all extracted rules from JSON files"""
        rule_files = list(self.rules_directory.glob("*_rules.json"))
        
        for rule_file in rule_files:
            try:
                with open(rule_file, 'r') as f:
                    data = json.load(f)
                
                if data.get('success') and 'extracted_rules' in data.get('analysis', {}):
                    rules = data['analysis']['extracted_rules']
                    
                    if isinstance(rules, list):
                        for rule in rules:
                            if isinstance(rule, dict) and 'rule' in rule:
                                rule['source_file'] = rule_file.name
                                rule['rule_id'] = self.generate_rule_id(rule)
                                self.all_rules.append(rule)
            except Exception as e:
                print(f"❌ Error loading {rule_file}: {e}")
    
    def generate_rule_id(self, rule: Dict[str, Any]) -> str:
        """Generate a unique rule ID based on title and category"""
        title = rule.get('rule', 'Unknown').replace(' ', '_').replace('&', 'and')
        # Clean up title for ID
        clean_title = re.sub(r'[^a-zA-Z0-9_]', '', title)
        return f"RULE_{clean_title[:20]}_{hash(rule.get('rule', '')) % 1000:03d}"
    
    def extract_numeric_value(self, text: str, units: str = None) -> Optional[float]:
        """Extract numeric values from rule text"""
        if not text:
            return None
        
        # Look for patterns like "≥ 60", ">= 60", "minimum 60", "6,000", etc.
        patterns = [
            r'≥\s*([0-9,]+)',
            r'>=\s*([0-9,]+)', 
            r'minimum\s+([0-9,]+)',
            r'min\s+([0-9,]+)',
            r'([0-9,]+)\s*sf',
            r'([0-9,]+)\s*ft',
            r'([0-9,]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    # Remove commas and convert to float
                    value = float(matches[0].replace(',', ''))
                    return value
                except ValueError:
                    continue
        
        return None
    
    def validate_lot_requirements(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate lot-related rules"""
        results = []
        site_data = project_data.get('site_data', {})
        
        zone = site_data.get('zone_district', '')
        lot_area = site_data.get('lot_area', 0)
        lot_width = site_data.get('lot_width', 0)
        lot_depth = site_data.get('lot_depth', 0)
        
        # Find lot-related rules
        lot_rules = [rule for rule in self.all_rules if 'lot' in rule.get('rule', '').lower()]
        
        for rule in lot_rules:
            rule_title = rule.get('rule', '')
            constants = rule.get('Constants', {})
            conditions = rule.get('Conditions', {})
            
            # Check minimum lot area
            if 'minimum' in rule_title.lower() and 'area' in rule_title.lower():
                if zone in self.zone_requirements:
                    min_area = self.zone_requirements[zone]['min_area']
                    if lot_area < min_area:
                        results.append({
                            'rule_id': rule['rule_id'],
                            'rule_title': rule_title,
                            'status': 'VIOLATION',
                            'criticality': 'CRITICAL',
                            'message': f'Lot area {lot_area:,} sf < minimum {min_area:,} sf for {zone}',
                            'expected': f'{min_area:,} sf minimum',
                            'actual': f'{lot_area:,} sf',
                            'violation_type': 'dimensional',
                            'source_rule': rule.get('source_file', ''),
                            'stop_condition': True
                        })
                    else:
                        results.append({
                            'rule_id': rule['rule_id'],
                            'rule_title': rule_title,
                            'status': 'COMPLIANT',
                            'criticality': 'HIGH',
                            'message': f'Lot area {lot_area:,} sf meets minimum {min_area:,} sf for {zone}',
                            'expected': f'{min_area:,} sf minimum',
                            'actual': f'{lot_area:,} sf',
                            'source_rule': rule.get('source_file', '')
                        })
            
            # Check maximum lot area
            elif 'maximum' in rule_title.lower() and 'area' in rule_title.lower():
                if zone in self.zone_requirements:
                    max_area = self.zone_requirements[zone]['max_area']
                    if lot_area > max_area:
                        results.append({
                            'rule_id': rule['rule_id'],
                            'rule_title': rule_title,
                            'status': 'VIOLATION',
                            'criticality': 'HIGH',
                            'message': f'Lot area {lot_area:,} sf > maximum {max_area:,} sf for {zone}',
                            'expected': f'{max_area:,} sf maximum',
                            'actual': f'{lot_area:,} sf',
                            'violation_type': 'dimensional',
                            'source_rule': rule.get('source_file', ''),
                            'stop_condition': True
                        })
            
            # Check lot width
            elif 'width' in rule_title.lower():
                if zone in self.zone_requirements:
                    min_width = self.zone_requirements[zone]['min_width']
                    if lot_width < min_width:
                        results.append({
                            'rule_id': rule['rule_id'],
                            'rule_title': rule_title,
                            'status': 'VIOLATION',
                            'criticality': 'CRITICAL',
                            'message': f'Lot width {lot_width} ft < minimum {min_width} ft',
                            'expected': f'{min_width} ft minimum',
                            'actual': f'{lot_width} ft',
                            'violation_type': 'dimensional',
                            'source_rule': rule.get('source_file', ''),
                            'stop_condition': True
                        })
        
        return results
    
    def validate_setbacks(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate setback requirements"""
        results = []
        building_data = project_data.get('building_data', {})
        setbacks = building_data.get('setbacks', {})
        
        # Standard setback minimums (extracted from rules analysis)
        setback_minimums = {
            'front_setback': 20,
            'rear_setback': 25,
            'side_setback_left': 6,
            'side_setback_right': 6
        }
        
        # Find setback-related rules
        setback_rules = [rule for rule in self.all_rules if 'setback' in rule.get('rule', '').lower()]
        
        for setback_type, min_required in setback_minimums.items():
            actual_setback = setbacks.get(setback_type, 0)
            
            # Find specific rule for this setback type
            relevant_rule = None
            for rule in setback_rules:
                rule_title = rule.get('rule', '').lower()
                if setback_type.replace('_', ' ') in rule_title:
                    relevant_rule = rule
                    break
            
            if not relevant_rule:
                # Create generic setback rule
                relevant_rule = {
                    'rule_id': f'SETBACK_{setback_type.upper()}',
                    'rule': f'{setback_type.replace("_", " ").title()} Minimum',
                    'source_file': 'derived_from_analysis'
                }
            
            if actual_setback < min_required:
                results.append({
                    'rule_id': relevant_rule['rule_id'],
                    'rule_title': relevant_rule['rule'],
                    'status': 'VIOLATION',
                    'criticality': 'CRITICAL',
                    'message': f'{setback_type.replace("_", " ").title()} {actual_setback} ft < minimum {min_required} ft',
                    'expected': f'{min_required} ft minimum',
                    'actual': f'{actual_setback} ft',
                    'violation_type': 'setback',
                    'source_rule': relevant_rule.get('source_file', ''),
                    'stop_condition': True
                })
            else:
                results.append({
                    'rule_id': relevant_rule['rule_id'],
                    'rule_title': relevant_rule['rule'],
                    'status': 'COMPLIANT',
                    'criticality': 'HIGH',
                    'message': f'{setback_type.replace("_", " ").title()} {actual_setback} ft meets minimum {min_required} ft',
                    'expected': f'{min_required} ft minimum',
                    'actual': f'{actual_setback} ft',
                    'source_rule': relevant_rule.get('source_file', '')
                })
        
        return results
    
    def validate_building_height(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate building height requirements"""
        results = []
        building_data = project_data.get('building_data', {})
        building_height = building_data.get('building_height', 0)
        
        max_height = 30  # Standard single-family height limit
        
        # Find height-related rules
        height_rules = [rule for rule in self.all_rules if 'height' in rule.get('rule', '').lower()]
        
        height_rule = {
            'rule_id': 'HEIGHT_MAX',
            'rule': 'Maximum Building Height',
            'source_file': 'derived_from_analysis'
        }
        
        if height_rules:
            height_rule = height_rules[0]
        
        if building_height > max_height:
            results.append({
                'rule_id': height_rule['rule_id'],
                'rule_title': height_rule['rule'],
                'status': 'VIOLATION',
                'criticality': 'CRITICAL',
                'message': f'Building height {building_height} ft > maximum {max_height} ft',
                'expected': f'{max_height} ft maximum',
                'actual': f'{building_height} ft',
                'violation_type': 'height',
                'source_rule': height_rule.get('source_file', ''),
                'stop_condition': True
            })
        else:
            results.append({
                'rule_id': height_rule['rule_id'],
                'rule_title': height_rule['rule'],
                'status': 'COMPLIANT',
                'criticality': 'HIGH',
                'message': f'Building height {building_height} ft within maximum {max_height} ft',
                'expected': f'{max_height} ft maximum',
                'actual': f'{building_height} ft',
                'source_rule': height_rule.get('source_file', '')
            })
        
        return results
    
    def validate_floor_area(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate floor area ratio requirements"""
        results = []
        site_data = project_data.get('site_data', {})
        building_data = project_data.get('building_data', {})
        
        lot_area = site_data.get('lot_area', 1)
        gross_floor_area = building_data.get('gross_floor_area', 0)
        
        max_far = 0.45  # 45% typical FAR
        actual_far = gross_floor_area / lot_area if lot_area > 0 else 0
        
        # Find floor area related rules
        far_rules = [rule for rule in self.all_rules if any(term in rule.get('rule', '').lower() 
                                                          for term in ['floor area', 'far', 'coverage'])]
        
        far_rule = {
            'rule_id': 'FAR_MAX',
            'rule': 'Floor Area Ratio Maximum',
            'source_file': 'derived_from_analysis'
        }
        
        if far_rules:
            far_rule = far_rules[0]
        
        if actual_far > max_far:
            results.append({
                'rule_id': far_rule['rule_id'],
                'rule_title': far_rule['rule'],
                'status': 'VIOLATION',
                'criticality': 'CRITICAL',
                'message': f'FAR {actual_far:.3f} ({gross_floor_area:,} sf / {lot_area:,} sf) > maximum {max_far}',
                'expected': f'{max_far} maximum',
                'actual': f'{actual_far:.3f}',
                'violation_type': 'floor_area',
                'source_rule': far_rule.get('source_file', ''),
                'stop_condition': True
            })
        else:
            results.append({
                'rule_id': far_rule['rule_id'],
                'rule_title': far_rule['rule'],
                'status': 'COMPLIANT',
                'criticality': 'HIGH',
                'message': f'FAR {actual_far:.3f} within maximum {max_far}',
                'expected': f'{max_far} maximum',
                'actual': f'{actual_far:.3f}',
                'source_rule': far_rule.get('source_file', '')
            })
        
        return results
    
    def validate_parking(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate parking requirements"""
        results = []
        parking_data = project_data.get('parking_data', {})
        parking_spaces = parking_data.get('parking_spaces', 0)
        
        required_spaces = 2  # Standard for single-family
        
        # Find parking-related rules
        parking_rules = [rule for rule in self.all_rules if 'parking' in rule.get('rule', '').lower()]
        
        parking_rule = {
            'rule_id': 'PARKING_MIN',
            'rule': 'Minimum Parking Spaces',
            'source_file': 'derived_from_analysis'
        }
        
        if parking_rules:
            parking_rule = parking_rules[0]
        
        if parking_spaces < required_spaces:
            results.append({
                'rule_id': parking_rule['rule_id'],
                'rule_title': parking_rule['rule'],
                'status': 'VIOLATION',
                'criticality': 'CRITICAL',
                'message': f'Provided {parking_spaces} parking spaces < required {required_spaces} spaces',
                'expected': f'{required_spaces} spaces minimum',
                'actual': f'{parking_spaces} spaces',
                'violation_type': 'parking',
                'source_rule': parking_rule.get('source_file', ''),
                'stop_condition': True
            })
        else:
            results.append({
                'rule_id': parking_rule['rule_id'],
                'rule_title': parking_rule['rule'],
                'status': 'COMPLIANT',
                'criticality': 'HIGH',
                'message': f'Provided {parking_spaces} spaces meets requirement of {required_spaces} spaces',
                'expected': f'{required_spaces} spaces minimum',
                'actual': f'{parking_spaces} spaces',
                'source_rule': parking_rule.get('source_file', '')
            })
        
        return results
    
    def validate_architectural_features(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate architectural feature requirements"""
        results = []
        building_data = project_data.get('building_data', {})
        arch_features = building_data.get('architectural_features', {})
        
        # Find architectural feature rules
        arch_rules = [rule for rule in self.all_rules if any(term in rule.get('rule', '').lower() 
                                                           for term in ['porch', 'bay', 'entry', 'window', 'balcony'])]
        
        # Validate porches if present
        porches = arch_features.get('porches', [])
        for i, porch in enumerate(porches):
            porch_height = porch.get('height', 0)
            
            # Find porch height rules
            porch_rules = [rule for rule in arch_rules if 'porch' in rule.get('rule', '').lower()]
            
            if porch_rules and porch_height > 12:  # Example: porches over 12' may have special rules
                results.append({
                    'rule_id': f'PORCH_{i}_HEIGHT',
                    'rule_title': 'Porch Height Limitation',
                    'status': 'WARNING',
                    'criticality': 'MEDIUM',
                    'message': f'Porch {i+1} height {porch_height} ft may require special review (>12 ft)',
                    'expected': '≤12 ft typical',
                    'actual': f'{porch_height} ft',
                    'violation_type': 'architectural',
                    'source_rule': porch_rules[0].get('source_file', '')
                })
        
        return results
    
    def perform_comprehensive_validation(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive validation against all applicable rules"""
        print(f"🔍 REVERSE COMPLIANCE VALIDATION")
        print(f"Project: {project_data.get('project_info', {}).get('project_name', 'Unnamed')}")
        print("=" * 60)
        
        # Run all validation checks
        all_results = []
        all_results.extend(self.validate_lot_requirements(project_data))
        all_results.extend(self.validate_setbacks(project_data))
        all_results.extend(self.validate_building_height(project_data))
        all_results.extend(self.validate_floor_area(project_data))
        all_results.extend(self.validate_parking(project_data))
        all_results.extend(self.validate_architectural_features(project_data))
        
        # Categorize results
        violations = [r for r in all_results if r['status'] == 'VIOLATION']
        warnings = [r for r in all_results if r['status'] == 'WARNING']
        compliant = [r for r in all_results if r['status'] == 'COMPLIANT']
        critical_violations = [r for r in violations if r['criticality'] == 'CRITICAL']
        
        # Determine overall compliance status
        overall_status = 'COMPLIANT' if len(violations) == 0 else 'NON_COMPLIANT'
        can_proceed = len(critical_violations) == 0
        
        # Generate summary
        summary = {
            'validation_timestamp': datetime.now().isoformat(),
            'project_name': project_data.get('project_info', {}).get('project_name', 'Unnamed'),
            'overall_status': overall_status,
            'can_proceed': can_proceed,
            'total_rules_checked': len(all_results),
            'compliant_rules': len(compliant),
            'violations': len(violations),
            'warnings': len(warnings),
            'critical_violations': len(critical_violations),
            'compliance_percentage': (len(compliant) / len(all_results) * 100) if all_results else 0
        }
        
        # Print summary
        print(f"📊 VALIDATION SUMMARY:")
        print(f"   Overall Status: {'✅ COMPLIANT' if overall_status == 'COMPLIANT' else '❌ NON-COMPLIANT'}")
        print(f"   Can Proceed: {'✅ YES' if can_proceed else '❌ NO'}")
        print(f"   Rules Checked: {len(all_results)}")
        print(f"   Compliant: {len(compliant)}")
        print(f"   Violations: {len(violations)}")
        print(f"   Warnings: {len(warnings)}")
        print(f"   Critical Violations: {len(critical_violations)}")
        print(f"   Compliance Rate: {summary['compliance_percentage']:.1f}%")
        
        # Print detailed results
        if violations:
            print(f"\n🚨 VIOLATIONS:")
            for violation in violations:
                critical_flag = " [CRITICAL]" if violation['criticality'] == 'CRITICAL' else ""
                print(f"   ❌ {violation['rule_title']}: {violation['message']}{critical_flag}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"   ⚠️  {warning['rule_title']}: {warning['message']}")
        
        if compliant and len(compliant) <= 10:  # Show compliant items if not too many
            print(f"\n✅ COMPLIANT ITEMS:")
            for comp in compliant[:5]:  # Show first 5
                print(f"   ✅ {comp['rule_title']}: {comp['message']}")
            if len(compliant) > 5:
                print(f"   ... and {len(compliant) - 5} more compliant items")
        
        return {
            'summary': summary,
            'violations': violations,
            'warnings': warnings,
            'compliant': compliant,
            'all_results': all_results
        }
    
    def generate_violation_report(self, validation_results: Dict[str, Any], output_file: str = None):
        """Generate detailed violation report"""
        violations = validation_results['violations']
        warnings = validation_results['warnings']
        summary = validation_results['summary']
        
        report = {
            'report_metadata': {
                'generated_date': datetime.now().isoformat(),
                'report_type': 'reverse_compliance_validation',
                'project_name': summary['project_name'],
                'validation_engine': 'ReverseComplianceValidator v1.0'
            },
            'executive_summary': summary,
            'critical_violations': [v for v in violations if v['criticality'] == 'CRITICAL'],
            'all_violations': violations,
            'warnings': warnings,
            'remediation_recommendations': self.generate_remediation_recommendations(violations)
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Violation report saved: {output_file}")
        
        return report
    
    def generate_remediation_recommendations(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations to fix violations"""
        recommendations = []
        
        for violation in violations:
            if violation['violation_type'] == 'dimensional':
                recommendations.append({
                    'violation_id': violation['rule_id'],
                    'priority': 'HIGH' if violation['criticality'] == 'CRITICAL' else 'MEDIUM',
                    'recommendation': f"Adjust design to meet {violation['expected']}",
                    'impact': 'Design modification required',
                    'alternatives': ['Apply for variance', 'Redesign to comply']
                })
            elif violation['violation_type'] == 'setback':
                recommendations.append({
                    'violation_id': violation['rule_id'],
                    'priority': 'HIGH',
                    'recommendation': f"Increase {violation['rule_title'].lower()} to meet minimum requirement",
                    'impact': 'Building repositioning required',
                    'alternatives': ['Setback variance application', 'Building redesign']
                })
        
        return recommendations

def main():
    print("🔄 REVERSE COMPLIANCE VALIDATOR - DEMO")
    print("=" * 50)
    
    # Sample project data for testing
    sample_projects = [
        {
            'project_info': {
                'project_name': 'Compliant Test Project',
                'project_id': 'TEST-001'
            },
            'site_data': {
                'zone_district': 'R-1',
                'lot_area': 7500,
                'lot_width': 75,
                'lot_depth': 120
            },
            'building_data': {
                'building_height': 28,
                'gross_floor_area': 3200,
                'setbacks': {
                    'front_setback': 25,
                    'rear_setback': 30,
                    'side_setback_left': 8,
                    'side_setback_right': 10
                },
                'architectural_features': {
                    'porches': [
                        {'type': 'front_porch', 'height': 10, 'area': 120}
                    ]
                }
            },
            'parking_data': {
                'parking_spaces': 2
            }
        },
        {
            'project_info': {
                'project_name': 'Violation Test Project',
                'project_id': 'TEST-002'
            },
            'site_data': {
                'zone_district': 'R-1',
                'lot_area': 5500,  # TOO SMALL
                'lot_width': 55,   # TOO NARROW
                'lot_depth': 95    # TOO SHALLOW
            },
            'building_data': {
                'building_height': 35,  # TOO TALL
                'gross_floor_area': 4000,  # TOO LARGE
                'setbacks': {
                    'front_setback': 15,  # TOO SMALL
                    'rear_setback': 20,   # TOO SMALL
                    'side_setback_left': 4,   # TOO SMALL
                    'side_setback_right': 5   # TOO SMALL
                },
                'architectural_features': {
                    'porches': [
                        {'type': 'front_porch', 'height': 15, 'area': 200}  # HIGH PORCH
                    ]
                }
            },
            'parking_data': {
                'parking_spaces': 1  # TOO FEW
            }
        }
    ]
    
    # Initialize validator
    validator = ReverseComplianceValidator()
    
    # Test both projects
    for project in sample_projects:
        validation_results = validator.perform_comprehensive_validation(project)
        
        # Generate violation report
        report_filename = f"violation_report_{project['project_info']['project_id']}.json"
        validator.generate_violation_report(validation_results, report_filename)
        
        print(f"\n{'🎉 PROJECT COMPLIANT' if validation_results['summary']['overall_status'] == 'COMPLIANT' else '🛑 PROJECT NON-COMPLIANT'}")
        print("=" * 60)
        print()

if __name__ == "__main__":
    main()
