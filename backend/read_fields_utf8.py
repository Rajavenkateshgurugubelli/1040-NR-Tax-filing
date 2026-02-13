
try:
    with open(r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\forms\1040nr_official_fields.txt', 'r', encoding='utf-16-le') as f:
        content = f.read()
    
    with open(r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\schedule_oi_fields_utf8.txt', 'w', encoding='utf-8') as out:
        # Pring lines that likely belong to Schedule OI (Page 5)
        for line in content.splitlines():
            if "Page5" in line or "ScheduleOI" in line:
                out.write(line + "\n")
        print("Done writing to utf-8 file.")
except Exception as e:
    print(f"Error: {e}")
