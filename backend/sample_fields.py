
try:
    with open(r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\forms\1040nr_official_fields.txt', 'r', encoding='utf-16-le') as f:
        print("Reading first 20 lines:")
        for i in range(20):
            print(f.readline().strip())
except Exception as e:
    print(f"Error: {e}")
