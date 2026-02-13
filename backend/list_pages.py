
import re

try:
    with open(r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\forms\1040nr_official_fields.txt', 'r', encoding='utf-16-le') as f:
        content = f.read()
        
    pages = set()
    # Regex to find PageX identifiers
    # Looking for patterns like .Page1[0], .Page2[0], etc.
    matches = re.findall(r'\.Page\d+\[0\]', content)
    for m in matches:
        pages.add(m)
        
    print("Found Pages:", sorted(list(pages)))
    
except Exception as e:
    print(f"Error: {e}")
