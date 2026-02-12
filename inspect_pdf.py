from pypdf import PdfReader
import os

def list_fields(pdf_path):
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    if fields:
        print(f"--- Fields for {os.path.basename(pdf_path)} ---")
        for field_name, value in fields.items():
            print(f"{field_name}: {value.get('/V', '')}")
    else:
        print(f"No fields found in {os.path.basename(pdf_path)}")

forms_dir = os.path.join("backend", "forms")
list_fields(os.path.join(forms_dir, "f1040nr.pdf"))
list_fields(os.path.join(forms_dir, "f1040nrn.pdf"))
list_fields(os.path.join(forms_dir, "f8843.pdf"))
