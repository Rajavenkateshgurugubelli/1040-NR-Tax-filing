"""
Generate an FDF file to test Page 2 fields using PDFtk.
"""
import os
import subprocess

def create_fdf(fields_dict):
    fdf = "%FDF-1.2\n1 0 obj\n<<\n/FDF << /Fields [\n"
    for key, value in fields_dict.items():
        fdf += f"<< /T ({key}) /V ({value}) >>\n"
    fdf += "] >>\n>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    return fdf

def main():
    # Page 2 fields to test
    page2_fields = [
        "topmostSubform[0].Page2[0].f2_01[0]",
        "topmostSubform[0].Page2[0].f2_02[0]",
        "topmostSubform[0].Page2[0].f2_03[0]",
        "topmostSubform[0].Page2[0].f2_14[0]",
        "topmostSubform[0].Page2[0].f2_15[0]",
        "topmostSubform[0].Page2[0].Line23a_ReadOrder[0].f2_16[0]",
        "topmostSubform[0].Page2[0].Line25_ReadOrder[0].f2_21[0]",
        "topmostSubform[0].Page2[0].f2_17[0]",
        "topmostSubform[0].Page2[0].f2_18[0]",
        "topmostSubform[0].Page2[0].f2_19[0]",
        "topmostSubform[0].Page2[0].f2_20[0]",
        "topmostSubform[0].Page2[0].AccountNo[0].f2_39[0]",
        "topmostSubform[0].Page2[0].RoutingNo[0].f2_38[0]",
    ]

    fields_data = {}
    for field in page2_fields:
        # Extract short name for label
        short_name = field.split('.')[-1].replace('[0]', '')
        if "Line" in field:
            short_name = "LINE_" + short_name
        fields_data[field] = short_name

    fdf_content = create_fdf(fields_data)
    
    with open("page2_test.fdf", "w") as f:
        f.write(fdf_content)
        
    print("Generated page2_test.fdf")
    
    # Run PDFtk
    pdftk_path = r"C:\Program Files (x86)\PDFtk Server\bin\pdftk.exe"
    input_pdf = "backend/forms/f1040nr.pdf"
    output_pdf = "PDFTK_PAGE2_TEST.pdf"
    
    cmd = [
        pdftk_path, 
        input_pdf, 
        "fill_form", "page2_test.fdf", 
        "output", output_pdf, 
        "flatten"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)
    print(f"Generated {output_pdf}")

if __name__ == "__main__":
    main()
