#!/usr/bin/env python3
import json

# Test the JSON fixing logic with the actual problematic response
test_response = '''```json
{
  "page_number": "3",
  "main_heading": "Gross vs. net lot area",
  "text_content": "Gross vs. net lot area\\n\\nGross lot area is the size of the lot—from lot line to lot line. Development potential is based on the net lot area and while gross and net lot area are the same for most lots in Palo Alto, there are some lots for which portions must be excluded from the gross lot area to establish the net lot area.\\n\\nAreas excluded from the gross lot size are:\\n• Street right-of-way (Area A of Fig 1 on this page)\\n• \\"Pole\\" portion of a flag lot (Area B of Fig 2 on this page)\\n• Creek channel (Area C of Fig 3 on this page)\\n\\nFig 1 Gross lot area exclusions: street easements\\n\\nLot with boundaries that extend into the public ROW\\n\\nThe portion of the lot within the public ROW must be subtracted from the gross lot area.\\n\\nNotes: In some areas of Palo Alto, like Barron Park, it is not unusual for the lot to extend to the middle of the street. However, for zoning purposes, the lot i'''

print("Testing JSON fix...")

# Apply our fix
response = test_response.strip()
if response.startswith('```json'):
    response = response[7:]
if response.endswith('```'):
    response = response[:-3]
response = response.strip()

# Fix incomplete string
lines = response.split('\n')
complete_lines = []

for i, line in enumerate(lines):
    stripped = line.strip()
    
    if not stripped:
        complete_lines.append(line)
        continue
    
    if '":' in stripped:
        if not (stripped.endswith('"') or stripped.endswith('",') or 
               stripped.endswith('}') or stripped.endswith('],') or
               stripped.endswith(']')):
            if stripped.count('"') % 2 == 1:  # Odd number of quotes
                if not stripped.endswith('"'):
                    line = line.rstrip() + '"'
                    complete_lines.append(line)
            break
        else:
            complete_lines.append(line)
    else:
        complete_lines.append(line)

fixed_response = '\n'.join(complete_lines)

# Add missing closing braces
open_braces = fixed_response.count('{')
close_braces = fixed_response.count('}')
missing_braces = open_braces - close_braces

if missing_braces > 0:
    fixed_response += '}' * missing_braces

# Test if it parses
try:
    parsed = json.loads(fixed_response)
    print("✅ JSON parsing successful!")
    print(f"Fields: {list(parsed.keys())}")
    print(f"Text content length: {len(parsed.get('text_content', ''))} chars")
    print("✅ Fix works!")
except json.JSONDecodeError as e:
    print(f"❌ Still failing: {e}")
    print(f"Error at position {e.pos}")
    print("Fixed response preview:")
    print(fixed_response[-100:])