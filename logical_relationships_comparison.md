# Logical Relationships in Zoning Rules - Comparison of Approaches

## The Problem
The original `manual_rules.json` was ambiguous about logical relationships between requirements within each rule. This creates issues for:
- **Human interpretation**: Unclear whether all requirements must be met (AND) or any one (OR)  
- **Programmatic compliance**: Cannot build automated validation without explicit logic
- **Legal clarity**: Ambiguous enforcement when multiple requirements exist

## Analysis Results
Out of 32 total rules, we identified 4 distinct logical patterns:

- **OR_CONDITIONS (5 rules)**: Any one requirement satisfies the rule
- **AND_CONDITIONS (14 rules)**: All requirements must be satisfied simultaneously  
- **CONDITIONAL_OR (3 rules)**: Only one set applies based on zone/condition
- **CONDITIONAL_AND (10 rules)**: All requirements apply IF condition is met

## Solution: Two Approaches

### Option A: Minimal Schema Enhancement
**Approach**: Add a `"logic"` field to existing schema
**Benefits**: 
- ✅ Minimal disruption to existing structure
- ✅ Easy to understand and implement
- ✅ Backwards compatible
- ✅ Clear for human readers

**Example**:
```json
{
  "id": "LS-2",
  "title": "Exceptions to Maximum Lot Size", 
  "category": "Lot Size & Lot Area",
  "logic": "OR",
  "requirements": [
    "Exception - Where underlying lot lines must be removed...",
    "Exception - Where an adjacent substandard lot...",
    "Exception - Where the resultant number of lots..."
  ],
  "notes": "LOGIC: Any ONE requirement satisfies this rule"
}
```

### Option B: Explicit Logical Operators
**Approach**: Restructure requirements with explicit logical operators
**Benefits**:
- ✅ Machine-readable logical structure
- ✅ Supports complex nested conditions
- ✅ Unambiguous programmatic interpretation
- ✅ Enables advanced rule engines

**Example**:
```json
{
  "id": "LS-1",
  "title": "Minimum & Maximum Lot Sizes by Zone",
  "requirements": {
    "type": "conditional_or",
    "conditions": [
      {"condition": "zone == 'R-1'", "rule": "minimum 6,000 sf, maximum varies"},
      {"condition": "zone == 'R-1(7000)'", "rule": "minimum 7,000 sf, maximum varies"},
      {"condition": "zone == 'R-1(8000)'", "rule": "minimum 8,000 sf, maximum varies"}
    ]
  }
}
```

## Logic Types Defined

| Logic Type | Description | Example Use Case |
|------------|-------------|------------------|
| **AND** | All requirements must be satisfied | Parking standards - need space count AND dimensions AND coverage |
| **OR** | Any one requirement satisfies | Exceptions - any exception allows waiver |
| **CONDITIONAL_OR** | Only one set applies based on condition | Zone-specific rules - different minimums per zone |
| **CONDITIONAL_AND** | All requirements apply IF condition met | Substandard lot rules - all apply IF lot is substandard |

## Implementation Recommendations

### For Human Use (Planning Staff, Developers)
**Recommend: Option A**
- Clear, readable format
- Easy to understand logical relationships
- Minimal learning curve

### For Automated Systems (Compliance Software, APIs)
**Recommend: Option B** 
- Machine-parseable structure
- Supports complex rule engines
- Enables automated validation

### Hybrid Approach
Consider maintaining both:
- **Option A** for human-readable documentation
- **Option B** for system integration
- Auto-generate one from the other

## Files Created
1. `manual_rules_option_a.json` - Original schema + logic field
2. `manual_rules_option_b.json` - Restructured with explicit operators  
3. `improved_schema_example.json` - Detailed examples of both approaches
4. This comparison document

## Next Steps
1. **Review and approve** the logical relationship classifications
2. **Choose approach** based on intended use cases
3. **Update tooling** to handle the new schema
4. **Validate** with real-world test cases



