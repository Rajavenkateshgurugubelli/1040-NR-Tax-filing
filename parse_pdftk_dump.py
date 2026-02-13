"""
Parse the output of `pdftk dump_data_fields` to find Page 2 fields.
"""
import re

def parse_field_dump(filename):
    with open(filename, 'r', encoding='latin-1') as f:
        content = f.read()

    # Split by '---' which separates fields
    fields = content.split('---')
    
    page2_fields = []
    all_fields = []

    for field_block in fields:
        field_name_match = re.search(r'FieldName: (.+)', field_block)
        if field_name_match:
            name = field_name_match.group(1).strip()
            all_fields.append(name)
            
            if 'Page2' in name:
                page2_fields.append(name)

    print(f"Total fields found: {len(all_fields)}")
    print(f"Page 2 fields found: {len(page2_fields)}")
    print("-" * 40)
    
    print("PAGE 2 FIELDS:")
    for name in sorted(page2_fields):
        print(name)

if __name__ == "__main__":
    parse_field_dump("field_map.txt")
