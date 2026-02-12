
from pypdf import PdfReader, PdfWriter
import os

def diagnose(pdf_path):
    print(f"--- Diagnosing {os.path.basename(pdf_path)} ---")
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    
    if not fields:
        print("No fields found.")
        return

    print(f"Total fields: {len(fields)}")
    
    # Print first 20 fields to see structure
    for i, (key, value) in enumerate(fields.items()):
        if i < 20:
            print(f"Key: {key}")
            # print(f"  Type: {value.get('/FT')}")
            # print(f"  Parent: {value.get('/Parent')}")

    # Try to find specific fields we care about
    search_terms = ["f1_01", "f1_02", "f1_09", "Address"]
    print("\n--- Searching for specific keys ---")
    for term in search_terms:
        matches = [k for k in fields.keys() if term in k]
        print(f"Matches for '{term}':")
        for m in matches:
            print(f"  {m}")

    # Try filling with a short name and a long name to see what sticks
    print("\n--- Test Filling ---")
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    
    # Pick a target key
    target_key = None
    for k in fields.keys():
        if "f1_01" in k:
            target_key = k
            break
            
    if target_key:
        print(f"Attempting to fill {target_key}...")
        
        # Test 1: Full Name
        writer.update_page_form_field_values(
            writer.pages[0], {target_key: "TEST FULL NAME"}, auto_regenerate=False
        )
        
        # Test 2: Short Name (if applicable, though pypdf usually needs full name for XFA/nested)
        # But let's check if there is a mapping. 
        # For now, just save and check if it stuck.
        
        output_path = "diagnose_output.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)
            
        print("Written to diagnose_output.pdf")
        
        # Verify
        r2 = PdfReader(output_path)
        f2 = r2.get_fields()
        if f2 and target_key in f2:
            print(f"Value in output: {f2[target_key].get('/V')}")
        else:
            print("Target key not found (or value empty) in output.")

if __name__ == "__main__":
    forms_dir = os.path.join("backend", "forms")
    diagnose(os.path.join(forms_dir, "f1040nrn.pdf"))
