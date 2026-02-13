
import os

def extract_fields(file_path, filter_func, output_file):
    try:
        with open(file_path, 'r', encoding='utf-16-le') as f:
            content = f.read()
            
        with open(output_file, 'w', encoding='utf-8') as out:
            for line in content.splitlines():
                if line.startswith("FieldName:"):
                    field_name = line.split(":", 1)[1].strip()
                    if filter_func(field_name):
                        out.write(field_name + "\n")
        print(f"Extracted fields to {output_file}")
    except Exception as e:
        print(f"Error extracting from {file_path}: {e}")

# Extract Schedule OI fields (Page 5 of 1040NR)
extract_fields(
    r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\forms\1040nr_official_fields.txt',
    lambda x: "Page5" in x,
    r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\schedule_oi_fields_clean.txt'
)

# Extract Schedule NEC fields (Assume all fields in the separate file are relevant)
extract_fields(
    r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\forms\schedule_nec_fields.txt',
    lambda x: True,
    r'c:\Users\rajav\.gemini\antigravity\playground\resonant-opportunity\backend\schedule_nec_fields_clean.txt'
)
