
try:
    with open(r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\forms\1040nr_official_fields.txt', 'r', encoding='utf-16-le') as f:
        content = f.read()
        print("Successfully read file.")
        # Print lines that likely belong to Schedule OI (Page 5)
        for line in content.splitlines():
            if "Page5" in line or "ScheduleOI" in line:
                print(line)
except Exception as e:
    print(f"Error: {e}")
