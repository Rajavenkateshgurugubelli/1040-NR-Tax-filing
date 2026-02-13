"""
Automation Test: Generate Full 1040-NR Test PDF
-------------------------------------------------
This script fills every mapped field in the 1040-NR form with dummy data.
It serves as a visual verification layer to ensure all fields are mapped correctly.

run with: python tests/generate_full_test_pdf.py
"""
import os
import io
import subprocess
import tempfile

def generate_fdf(fields):
    fdf = "%FDF-1.2\n1 0 obj\n<<\n/FDF << /Fields [\n"
    for key, value in fields.items():
        if value is None: value = ""
        value_str = str(value).replace("(", "\\(").replace(")", "\\)")
        fdf += f"<< /T ({key}) /V ({value_str}) >>\n"
    fdf += "] >>\n>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    return fdf

def fill_pdf_test():
    # TEST DATA - Easy to spot visually
    test_fields = {
        # --- Page 1 ---
        'topmostSubform[0].Page1[0].f1_02[0]': "999-99-9999",  # SSN
        'topmostSubform[0].Page1[0].f1_04[0]': "123 TEST ST",  # Address
        'topmostSubform[0].Page1[0].f1_05[0]': "TEST CITY, TS 12345", # City
        'topmostSubform[0].Page1[0].f1_14[0]': "AUTO",         # First Name
        'topmostSubform[0].Page1[0].f1_15[0]': "TESTER",       # Last Name
        
        'topmostSubform[0].Page1[0].f1_42[0]': "100000",       # Line 1a Wages
        'topmostSubform[0].Page1[0].f1_54[0]': "100000",       # Line 1z Total
        'topmostSubform[0].Page1[0].f1_71[0]': "100000",       # Line 11a AGI
        
        # --- Page 2 ---
        'topmostSubform[0].Page2[0].f2_01[0]': "100000",       # Line 11b AGI Carry
        'topmostSubform[0].Page2[0].f2_02[0]': "14600",        # Line 12 Deductions
        'topmostSubform[0].Page2[0].f2_03[0]': "14600",        # Line 13a Total Ded
        'topmostSubform[0].Page2[0].f2_05[0]': "85400",        # Line 15 Taxable
        
        'topmostSubform[0].Page2[0].f2_14[0]': "25000",        # Line 21 Tax
        'topmostSubform[0].Page2[0].Line23a_ReadOrder[0].f2_16[0]': "25000", # Line 24 Total Tax
        'topmostSubform[0].Page2[0].Line25_ReadOrder[0].f2_21[0]': "30000", # Line 25a Withheld
        
        # Refund
        'topmostSubform[0].Page2[0].f2_36[0]': "5000",         # Line 34 Refund
        
        # Banking
        'topmostSubform[0].Page2[0].RoutingNo[0].f2_38[0]': "123456789",
        'topmostSubform[0].Page2[0].AccountNo[0].f2_39[0]': "9876543210",
    }
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, "backend", "forms", "f1040nr.pdf")
    output_path = os.path.join(base_dir, "AUTOMATION_TEST_1040NR.pdf")
    
    # Generate FDF
    fdf_content = generate_fdf(test_fields)
    fd, fdf_path = tempfile.mkstemp(suffix='.fdf')
    with os.fdopen(fd, 'w') as f:
        f.write(fdf_content)
        
    # Run PDFtk
    pdftk_cmd = [
        r"C:\Program Files (x86)\PDFtk Server\bin\pdftk.exe",
        template_path,
        "fill_form", fdf_path,
        "output", output_path,
        "flatten"
    ]
    
    print(f"Running automation test on {template_path}...")
    try:
        subprocess.run(pdftk_cmd, check=True)
        print(f"SUCCESS: Generated {output_path}")
        print("Please open this file to verify all fields are filled correctly.")
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        os.remove(fdf_path)

if __name__ == "__main__":
    fill_pdf_test()
