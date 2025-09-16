# Data Formats Specification
## Housing Project Compliance Workflow System

---

## 📥 **INPUT FORMATS**

### **1. Project Data Input Format**

The system expects project data in JSON format with the following structure:

```json
{
  "project_info": {
    "project_name": "Smith Residence",
    "project_id": "PR-2025-001",
    "applicant_name": "John Smith",
    "architect": "ABC Architecture",
    "submission_date": "2025-09-16"
  },
  "site_data": {
    "zone_district": "R-1",
    "lot_area": 7500,
    "lot_width": 75,
    "lot_depth": 120,
    "lot_shape": "standard",
    "corner_lot": false,
    "flag_lot": false,
    "easements": [
      {
        "type": "utility",
        "width": 10,
        "location": "rear"
      }
    ],
    "topography": {
      "slope_percentage": 5,
      "highest_point_elevation": 150,
      "lowest_point_elevation": 145
    }
  },
  "building_data": {
    "building_height": 28,
    "gross_floor_area": 3200,
    "floors": {
      "first_floor_area": 1800,
      "second_floor_area": 1400,
      "basement_area": 800,
      "attic_area": 200
    },
    "setbacks": {
      "front_setback": 25,
      "rear_setback": 30,
      "side_setback_left": 8,
      "side_setback_right": 10
    },
    "architectural_features": {
      "porches": [
        {
          "type": "front_porch",
          "area": 120,
          "height": 10,
          "covered": true
        }
      ],
      "bay_windows": [
        {
          "projection": 2,
          "width": 8,
          "floor": "first"
        }
      ],
      "chimneys": [
        {
          "height": 35,
          "setback_from_property_line": 15
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
      "setback_from_street": 20,
      "door_orientation": "front"
    },
    "driveway": {
      "width": 12,
      "length": 25,
      "slope": 8,
      "material": "concrete"
    }
  },
  "accessory_structures": [
    {
      "type": "storage_shed",
      "area": 120,
      "height": 12,
      "setbacks": {
        "rear": 5,
        "side": 3
      }
    }
  ],
  "special_features": {
    "adu": {
      "present": false
    },
    "below_grade_patio": {
      "present": true,
      "area": 200,
      "depth": 4
    },
    "retaining_walls": [
      {
        "height": 3,
        "length": 50,
        "setback": 2
      }
    ]
  }
}
```

### **2. Required Input Fields**

#### **Minimum Required Fields:**
- `site_data.zone_district` (string): R-1, R-1(7000), R-1(8000), R-1(10000), R-1(20000)
- `site_data.lot_area` (number): Square feet
- `site_data.lot_width` (number): Feet
- `site_data.lot_depth` (number): Feet
- `building_data.building_height` (number): Feet
- `building_data.gross_floor_area` (number): Square feet
- `building_data.setbacks` (object): All setback measurements in feet
- `parking_data.parking_spaces` (number): Count of spaces

#### **Optional Fields:**
- All architectural features
- Accessory structures
- Special features
- Detailed floor breakdowns

### **3. Input Validation Rules**

```json
{
  "validation_rules": {
    "zone_district": {
      "type": "enum",
      "allowed_values": ["R-1", "R-1(7000)", "R-1(8000)", "R-1(10000)", "R-1(20000)"]
    },
    "lot_area": {
      "type": "number",
      "minimum": 1000,
      "maximum": 50000
    },
    "lot_width": {
      "type": "number",
      "minimum": 30,
      "maximum": 300
    },
    "lot_depth": {
      "type": "number",
      "minimum": 50,
      "maximum": 500
    },
    "building_height": {
      "type": "number",
      "minimum": 8,
      "maximum": 50
    },
    "setbacks": {
      "type": "object",
      "properties": {
        "front_setback": {"type": "number", "minimum": 0},
        "rear_setback": {"type": "number", "minimum": 0},
        "side_setback_left": {"type": "number", "minimum": 0},
        "side_setback_right": {"type": "number", "minimum": 0}
      }
    }
  }
}
```

---

## 📤 **OUTPUT FORMATS**

### **1. Compliance Validation Results**

```json
{
  "validation_summary": {
    "project_name": "Smith Residence",
    "project_id": "PR-2025-001",
    "validation_date": "2025-09-16T20:50:51.451422",
    "overall_status": "PASS",
    "can_proceed": true,
    "total_checks": 45,
    "passed_checks": 43,
    "failed_checks": 2,
    "critical_failures": 0,
    "warnings": 2
  },
  "phase_results": {
    "Phase 1 - Site Analysis": {
      "status": "PASS",
      "checks_performed": 12,
      "checks_passed": 12,
      "checks_failed": 0,
      "critical_failures": 0
    },
    "Phase 2 - Building Design": {
      "status": "WARNING",
      "checks_performed": 18,
      "checks_passed": 16,
      "checks_failed": 2,
      "critical_failures": 0
    },
    "Phase 3 - Parking & Access": {
      "status": "PASS",
      "checks_performed": 8,
      "checks_passed": 8,
      "checks_failed": 0,
      "critical_failures": 0
    },
    "Phase 4 - Special Features": {
      "status": "PASS",
      "checks_performed": 5,
      "checks_passed": 5,
      "checks_failed": 0,
      "critical_failures": 0
    },
    "Phase 5 - Final Review": {
      "status": "PASS",
      "checks_performed": 2,
      "checks_passed": 2,
      "checks_failed": 0,
      "critical_failures": 0
    }
  },
  "detailed_results": [
    {
      "rule_id": "LS-1",
      "rule_title": "Minimum Lot Area",
      "category": "lot_requirements",
      "phase": "Phase 1 - Site Analysis",
      "status": "PASS",
      "criticality": "HIGH",
      "message": "Lot area 7500 sf within required range 6000-9999 sf for R-1 zone",
      "expected_value": "6000-9999",
      "actual_value": "7500",
      "units": "sf",
      "stop_condition": false,
      "source_rule": "18.12.040 (a) Table 2"
    },
    {
      "rule_id": "SB-3",
      "rule_title": "Front Setback Minimum",
      "category": "setbacks",
      "phase": "Phase 2 - Building Design",
      "status": "WARNING",
      "criticality": "MEDIUM",
      "message": "Front setback 20 ft meets minimum but contextual setback may apply",
      "expected_value": "20",
      "actual_value": "20",
      "units": "ft",
      "stop_condition": false,
      "recommendations": ["Verify neighborhood contextual setback requirements"],
      "source_rule": "18.12.040 (b)"
    }
  ],
  "recommendations": [
    {
      "priority": "HIGH",
      "category": "design_optimization",
      "message": "Consider increasing front setback to match neighborhood pattern",
      "affected_rules": ["SB-3", "SB-4"]
    }
  ],
  "next_steps": [
    {
      "step": 1,
      "action": "Address warning items",
      "description": "Review contextual setback requirements",
      "required": false
    },
    {
      "step": 2,
      "action": "Prepare submission package",
      "description": "Compile all required documentation",
      "required": true
    }
  ]
}
```

### **2. Compliance Checklist Output**

```json
{
  "checklist_metadata": {
    "generated_date": "2025-09-16T20:50:51.451422",
    "total_rules_analyzed": 160,
    "checklist_type": "housing_project_compliance",
    "zone_specific": "R-1",
    "version": "1.0"
  },
  "phases": {
    "Phase 1 - Site Analysis": [
      {
        "rule_title": "Minimum Lot Area",
        "rule_id": "LS-1",
        "category": "lot_requirements",
        "scope": "Defines minimum lot area for new construction",
        "applicability": "All new single-family residential projects",
        "requirements": [
          "MANDATORY: Lot area must be >= 6000 sf for R-1 zone",
          "VALUES: R-1: 6000-9999 sf"
        ],
        "validation_method": "automated",
        "input_fields": ["site_data.lot_area", "site_data.zone_district"],
        "status": "pending",
        "criticality": "HIGH",
        "stop_condition": true,
        "source_file": "Page_08_rules.json",
        "code_reference": "18.12.040 (a) Table 2"
      }
    ]
  }
}
```

### **3. Critical Path Output**

```json
{
  "critical_path_metadata": {
    "generated_date": "2025-09-16T20:50:51.452977",
    "total_critical_items": 136,
    "stop_conditions": 89,
    "warning_conditions": 47
  },
  "critical_rules": [
    {
      "rule_title": "Minimum Lot Area",
      "rule_id": "LS-1",
      "category": "lot_requirements",
      "criticality": "HIGH",
      "stop_condition": true,
      "requirements": [
        "MANDATORY: Lot area >= minimum for zone district"
      ],
      "validation_logic": {
        "condition": "site_data.lot_area >= zone_requirements[site_data.zone_district].min_area",
        "failure_action": "STOP_PROJECT",
        "error_message": "Lot area {actual} sf < minimum {required} sf for {zone}"
      },
      "exceptions": [
        "Variance approval",
        "Existing non-conforming lot"
      ],
      "source_file": "Page_08_rules.json"
    }
  ]
}
```

### **4. Error Response Format**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "timestamp": "2025-09-16T20:50:51.451422",
    "details": [
      {
        "field": "site_data.zone_district",
        "error": "Invalid zone district 'R-2'. Must be one of: R-1, R-1(7000), R-1(8000), R-1(10000), R-1(20000)",
        "provided_value": "R-2"
      },
      {
        "field": "site_data.lot_area",
        "error": "Missing required field",
        "provided_value": null
      }
    ]
  }
}
```

---

## 🔄 **DATA FLOW**

### **Input Processing Flow:**
1. **JSON Input** → Validation → **Validated Project Data**
2. **Validated Project Data** → Rule Engine → **Compliance Results**
3. **Compliance Results** → Report Generator → **Output JSON/Reports**

### **File-Based Processing:**
```bash
# Input file
project_data.json

# Processing command
python validate_project.py --input project_data.json --output results.json

# Output files
results.json                    # Main validation results
checklist.json                 # Detailed checklist
critical_path.json             # Critical items only
compliance_report.pdf          # Human-readable report
```

---

## 📊 **INTEGRATION FORMATS**

### **API Integration:**

```bash
# REST API Endpoint
POST /api/v1/validate-project

# Request Headers
Content-Type: application/json
Authorization: Bearer {token}

# Request Body
{project_data_json}

# Response
{validation_results_json}
```

### **Database Schema:**

```sql
-- Projects table
CREATE TABLE projects (
    project_id VARCHAR(50) PRIMARY KEY,
    project_name VARCHAR(200),
    zone_district VARCHAR(20),
    lot_area DECIMAL(10,2),
    lot_width DECIMAL(8,2),
    lot_depth DECIMAL(8,2),
    building_height DECIMAL(6,2),
    gross_floor_area DECIMAL(10,2),
    validation_status VARCHAR(20),
    created_date TIMESTAMP,
    updated_date TIMESTAMP
);

-- Validation results table
CREATE TABLE validation_results (
    result_id VARCHAR(50) PRIMARY KEY,
    project_id VARCHAR(50) REFERENCES projects(project_id),
    rule_id VARCHAR(20),
    rule_title VARCHAR(200),
    status VARCHAR(10),
    criticality VARCHAR(10),
    message TEXT,
    validation_date TIMESTAMP
);
```

### **Webhook Format:**

```json
{
  "event": "validation_complete",
  "project_id": "PR-2025-001",
  "status": "PASS",
  "webhook_url": "https://your-system.com/webhook",
  "payload": {
    "validation_summary": {...},
    "detailed_results": [...]
  }
}
```

---

## 🛠️ **USAGE EXAMPLES**

### **Command Line:**
```bash
# Validate single project
python validator.py --project project.json

# Batch validation
python validator.py --batch projects_folder/

# Generate checklist only
python validator.py --checklist-only --zone R-1
```

### **Python Integration:**
```python
from housing_validator import ProjectValidator

# Initialize validator
validator = ProjectValidator()

# Load project data
with open('project.json', 'r') as f:
    project_data = json.load(f)

# Validate project
results = validator.validate_project(project_data)

# Check if project can proceed
if results['can_proceed']:
    print("✅ Project approved for submission")
else:
    print("❌ Project requires revision")
    for failure in results['critical_failures']:
        print(f"  - {failure['message']}")
```

---

## 📋 **SUMMARY**

### **Input Requirements:**
- **Format**: JSON
- **Minimum Fields**: 8 required fields
- **Validation**: Automated input validation
- **Size Limit**: 10MB max file size

### **Output Guarantees:**
- **Format**: JSON (primary), PDF (reports)
- **Response Time**: < 5 seconds for standard projects
- **Accuracy**: Based on 160 extracted rules
- **Traceability**: Every result linked to source rule

### **Integration Ready:**
- REST API compatible
- Database schema provided
- Webhook support available
- Command-line interface included

This format specification ensures consistent, predictable data exchange for automated housing project compliance validation.
