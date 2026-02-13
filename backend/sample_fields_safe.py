
import sys

try:
    # Force utf-8 output
    sys.stdout.reconfigure(encoding='utf-8')
    with open(r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\forms\1040nr_official_fields.txt', 'r', encoding='utf-16-le') as f:
        print("Reading first 20 lines:")
        for i in range(20):
            line = f.readline()
            if not line: break
            # Repr to show hidden chars
            print(repr(line.strip()))
except Exception as e:
    print(f"Error: {e}")
