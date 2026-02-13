
import re

try:
    with open(r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\forms\1040nr_official_fields.txt', 'r', encoding='utf-16-le') as f:
        content = f.read()
        
    lines = content.splitlines()
    for line in lines:
        if "FieldName:" in line and "Page2" in line:
            # Check for interesting keywords or just print them all if not too many
            # But let's look for "23", "24", "Total", "Tax"
            if "23" in line or "24" in line or "f2_" in line:
                 print(line.strip())

except Exception as e:
    print(f"Error: {e}")
