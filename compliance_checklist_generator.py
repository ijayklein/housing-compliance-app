#!/usr/bin/env python3
"""
Housing Project Compliance Checklist Generator
Based on extracted Palo Alto zoning rules
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class ComplianceChecklistGenerator:
    def __init__(self, rules_directory: str):
        self.rules_directory = Path(rules_directory)
        self.all_rules = []
        self.load_rules()
    
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
                                self.all_rules.append(rule)
            except Exception as e:
                print(f"Error loading {rule_file}: {e}")
        
        print(f"Loaded {len(self.all_rules)} rules from {len(rule_files)} files")
    
    def categorize_rule(self, rule: Dict[str, Any]) -> str:
        """Categorize a rule based on its title and content"""
        rule_title = rule.get('rule', '').lower()
        
        # Define category keywords
        categories = {
            'lot_requirements': ['lot', 'size', 'area', 'width', 'depth', 'dimension'],
            'setbacks': ['setback', 'distance', 'yard', 'rear', 'side', 'front'],
            'building_height': ['height', 'floor', 'story', 'daylight', 'plane'],
            'floor_area': ['floor area', 'gfa', 'far', 'coverage', 'equivalency'],
            'parking_access': ['parking', 'driveway', 'garage', 'access', 'vehicle'],
            'architectural': ['porch', 'entry', 'bay', 'window', 'balcony', 'deck'],
            'accessory': ['accessory', 'structure', 'shed', 'outbuilding'],
            'dwelling_units': ['dwelling', 'unit', 'adu', 'second'],
            'site_features': ['patio', 'excavation', 'retaining', 'wall', 'fence'],
            'utilities': ['noise', 'equipment', 'hvac', 'mechanical']
        }
        
        for category, keywords in categories.items():
            if any(keyword in rule_title for keyword in keywords):
                return category
        
        return 'other'
    
    def extract_requirements(self, rule: Dict[str, Any]) -> List[str]:
        """Extract specific requirements from a rule"""
        requirements = []
        
        # Extract from Conditions
        conditions = rule.get('Conditions', {})
        if isinstance(conditions, dict):
            mandatory = conditions.get('Mandatory', '')
            if mandatory:
                requirements.append(f"MANDATORY: {mandatory}")
        
        # Extract from Constants
        constants = rule.get('Constants', {})
        if isinstance(constants, dict):
            numerical = constants.get('Numerical Values', '')
            if numerical:
                requirements.append(f"VALUES: {numerical}")
        
        # Extract from Variables
        variables = rule.get('Variables', {})
        if isinstance(variables, dict):
            dimensional = variables.get('Dimensional', '')
            if dimensional:
                requirements.append(f"DIMENSIONS: {dimensional}")
        
        return requirements
    
    def generate_checklist_by_phase(self) -> Dict[str, List[Dict]]:
        """Generate checklist organized by project phases"""
        
        phase_mapping = {
            'Phase 1 - Site Analysis': ['lot_requirements'],
            'Phase 2 - Building Design': ['setbacks', 'building_height', 'floor_area', 'architectural'],
            'Phase 3 - Parking & Access': ['parking_access'],
            'Phase 4 - Special Features': ['accessory', 'dwelling_units', 'site_features', 'utilities'],
            'Phase 5 - Final Review': ['other']
        }
        
        checklist = {}
        
        for phase, categories in phase_mapping.items():
            checklist[phase] = []
            
            for rule in self.all_rules:
                rule_category = self.categorize_rule(rule)
                
                if rule_category in categories:
                    requirements = self.extract_requirements(rule)
                    
                    checklist_item = {
                        'rule_title': rule.get('rule', 'Unknown'),
                        'category': rule_category,
                        'scope': rule.get('Qualifiers', {}).get('Scope', ''),
                        'applicability': rule.get('Qualifiers', {}).get('Applicability', ''),
                        'requirements': requirements,
                        'source_file': rule.get('source_file', ''),
                        'status': 'pending'  # For tracking compliance
                    }
                    
                    checklist[phase].append(checklist_item)
        
        return checklist
    
    def generate_zone_specific_checklist(self, zone_district: str) -> Dict[str, List[Dict]]:
        """Generate checklist specific to a zone district"""
        zone_rules = []
        
        for rule in self.all_rules:
            # Check if rule applies to the specified zone
            applicability = rule.get('Qualifiers', {}).get('Applicability', '').lower()
            if zone_district.lower() in applicability or 'r-1' in applicability:
                zone_rules.append(rule)
        
        # Use the filtered rules to generate checklist
        original_rules = self.all_rules
        self.all_rules = zone_rules
        checklist = self.generate_checklist_by_phase()
        self.all_rules = original_rules  # Restore original
        
        return checklist
    
    def generate_critical_path_checklist(self) -> List[Dict]:
        """Generate checklist of critical path items that could stop project"""
        critical_keywords = [
            'minimum', 'maximum', 'required', 'shall', 'must',
            'setback', 'height', 'area', 'parking', 'access'
        ]
        
        critical_rules = []
        
        for rule in self.all_rules:
            rule_text = f"{rule.get('rule', '')} {rule.get('Conditions', {}).get('Mandatory', '')}".lower()
            
            if any(keyword in rule_text for keyword in critical_keywords):
                requirements = self.extract_requirements(rule)
                
                critical_item = {
                    'rule_title': rule.get('rule', 'Unknown'),
                    'category': self.categorize_rule(rule),
                    'criticality': 'HIGH',
                    'stop_condition': True,
                    'requirements': requirements,
                    'exceptions': rule.get('Exceptions', {}).get('Explicit Deviations', ''),
                    'source_file': rule.get('source_file', '')
                }
                
                critical_rules.append(critical_item)
        
        return critical_rules
    
    def save_checklist(self, checklist: Dict, filename: str):
        """Save checklist to JSON file"""
        output_data = {
            'generated_date': datetime.now().isoformat(),
            'total_rules_analyzed': len(self.all_rules),
            'checklist_type': 'housing_project_compliance',
            'phases': checklist
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Checklist saved to: {filename}")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report of all rules"""
        categories = {}
        total_requirements = 0
        
        for rule in self.all_rules:
            category = self.categorize_rule(rule)
            categories[category] = categories.get(category, 0) + 1
            
            requirements = self.extract_requirements(rule)
            total_requirements += len(requirements)
        
        return {
            'total_rules': len(self.all_rules),
            'total_requirements': total_requirements,
            'categories': categories,
            'average_requirements_per_rule': total_requirements / len(self.all_rules) if self.all_rules else 0
        }

def main():
    print("🏗️ HOUSING PROJECT COMPLIANCE CHECKLIST GENERATOR")
    print("=" * 60)
    
    # Initialize generator
    rules_dir = "rules_extraction_v3_20250916_161035"
    generator = ComplianceChecklistGenerator(rules_dir)
    
    if not generator.all_rules:
        print("❌ No rules found. Check the rules directory.")
        return
    
    # Generate summary report
    summary = generator.generate_summary_report()
    print(f"📊 SUMMARY REPORT:")
    print(f"   Total Rules: {summary['total_rules']}")
    print(f"   Total Requirements: {summary['total_requirements']}")
    print(f"   Avg Requirements/Rule: {summary['average_requirements_per_rule']:.1f}")
    print(f"   Categories: {len(summary['categories'])}")
    
    print(f"\n📋 Category Breakdown:")
    for category, count in sorted(summary['categories'].items()):
        print(f"   {category.replace('_', ' ').title()}: {count} rules")
    
    # Generate phase-based checklist
    print(f"\n🔄 Generating Phase-Based Checklist...")
    phase_checklist = generator.generate_checklist_by_phase()
    generator.save_checklist(phase_checklist, "housing_project_checklist_by_phase.json")
    
    # Generate critical path checklist
    print(f"\n🚨 Generating Critical Path Checklist...")
    critical_checklist = generator.generate_critical_path_checklist()
    
    critical_data = {
        'generated_date': datetime.now().isoformat(),
        'critical_rules': critical_checklist,
        'total_critical_items': len(critical_checklist)
    }
    
    with open("housing_project_critical_path.json", 'w') as f:
        json.dump(critical_data, f, indent=2)
    
    print(f"Critical path checklist saved: housing_project_critical_path.json")
    print(f"   Critical Items: {len(critical_checklist)}")
    
    # Generate zone-specific checklists
    zones = ['R-1', 'R-1(7000)', 'R-1(8000)', 'R-1(10000)', 'R-1(20000)']
    
    print(f"\n🏘️ Generating Zone-Specific Checklists...")
    for zone in zones:
        zone_checklist = generator.generate_zone_specific_checklist(zone)
        zone_filename = f"housing_project_checklist_{zone.replace('(', '_').replace(')', '')}.json"
        generator.save_checklist(zone_checklist, zone_filename)
        
        total_items = sum(len(phase_items) for phase_items in zone_checklist.values())
        print(f"   {zone}: {total_items} applicable rules")
    
    print(f"\n✅ All checklists generated successfully!")
    print(f"\n📄 Generated Files:")
    print(f"   • housing_project_checklist_by_phase.json - Main workflow checklist")
    print(f"   • housing_project_critical_path.json - Critical path items")
    print(f"   • housing_project_checklist_[ZONE].json - Zone-specific checklists")

if __name__ == "__main__":
    main()
