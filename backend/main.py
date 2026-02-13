from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import io
import subprocess
import tempfile
from fastapi.responses import StreamingResponse

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserData(BaseModel):
    # Personal Info
    full_name: str
    ssn: str
    address: str
    city: str
    state: str
    zip_code: str
    country_of_residence: Optional[str] = ""
    filing_status: Optional[str] = "Single" # Single, Married Filing Separately
    
    # Visa / Enterprise Fields
    visa_type: Optional[str] = "F1" # F1, J1, H1B
    is_student: Optional[bool] = True
    
    # Income
    wages: float # W-2 Box 1
    federal_tax_withheld: float # W-2 Box 2
    social_security_tax_withheld: Optional[float] = 0.0 # Box 4 (Should be 0 for F1)
    medicare_tax_withheld: Optional[float] = 0.0 # Box 6 (Should be 0 for F1)
    state_tax_withheld: Optional[float] = 0.0 # W-2 Box 17 (Deduction)
    
    # Deductions
    charitable_contributions: Optional[float] = 0.0
    
    # Banking
    routing_number: Optional[str] = ""
    account_number: Optional[str] = ""
    account_type: Optional[str] = "Checking"

def calculate_tax(data: UserData):
    """
    Enterprise Tax Calculation Engine for Non-Resident Aliens (F-1/J-1)
    """
    warnings = []
    
    # 1. FICA Exemption Check (Enterprise Feature)
    # F-1/J-1 students are exempt from FICA (Social Security & Medicare) for 5 calendar years.
    total_fica = (data.social_security_tax_withheld or 0) + (data.medicare_tax_withheld or 0)
    if data.visa_type in ["F1", "J1"] and total_fica > 0:
        warnings.append(f"WARNING: You had ${total_fica:.2f} in FICA taxes withheld. As an F-1/J-1 student, you are likely exempt. Ask your employer for a refund or file Form 843.")

    # 2. Deduction Logic
    # NRAs generally cannot claim Standard Deduction.
    # Exception: India (Article 21(2))
    
    itemized_deductions = (data.state_tax_withheld or 0) + (data.charitable_contributions or 0)
    
    standard_deduction = 0
    if data.country_of_residence and "India" in data.country_of_residence:
        # US-India Treaty Article 21(2) allows Standard Deduction for students
        standard_deduction = 14600 # 2025 Value
        
    final_deduction = max(itemized_deductions, standard_deduction)
    
    # 3. Taxable Income
    taxable_income = max(0, data.wages - final_deduction)
    
    # 4. Tax Calculation (2025 Single Brackets - Simplified)
    tax = 0
    income = taxable_income
    
    # 10% on first $11,600
    if income > 11600:
        tax += 11600 * 0.10
        remainder = income - 11600
        # 12% on next chunk up to $47,150
        if remainder > (47150 - 11600):
            tax += (47150 - 11600) * 0.12
            # Simplified: Assuming most students don't exceed this for now
        else:
            tax += remainder * 0.12
    else:
        tax += income * 0.10
        
    total_tax = round(tax, 2)
    
    return {
        "taxable_wages": data.wages,
        "itemized_deductions": final_deduction,
        "taxable_income": taxable_income,
        "total_tax": total_tax,
        "wage_tax": total_tax,
        "refund": max(0, data.federal_tax_withheld - total_tax),
        "owe": max(0, total_tax - data.federal_tax_withheld),
        "warnings": warnings
    }

def generate_fdf(fields):
    """
    Generate FDF content from a dictionary of field names and values.
    """
    fdf = "%FDF-1.2\n1 0 obj\n<<\n/FDF << /Fields [\n"
    for key, value in fields.items():
        if value is None: value = ""
        value_str = str(value).replace("(", "\\(").replace(")", "\\)")
        fdf += f"<< /T ({key}) /V ({value_str}) >>\n"
    fdf += "] >>\n>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    return fdf

def fill_pdf(template_path, fields_dict):
    """
    Fill PDF using PDFtk Server.
    """
    try:
        fdf_content = generate_fdf(fields_dict)
        fd, fdf_path = tempfile.mkstemp(suffix='.fdf')
        with os.fdopen(fd, 'w') as f:
            f.write(fdf_content)
            
        output_path = template_path.replace('.pdf', '_filled.pdf')
        
        pdftk_cmd = [
            r"C:\Program Files (x86)\PDFtk Server\bin\pdftk.exe",
            template_path,
            "fill_form", fdf_path,
            "output", output_path,
            "flatten"
        ]
        subprocess.run(pdftk_cmd, check=True)
        
        with open(output_path, "rb") as f:
            output_bytes = io.BytesIO(f.read())
            
        os.remove(fdf_path)
        os.remove(output_path)
        return output_bytes
    except Exception as e:
        print(f"Error filling PDF: {e}")
        return io.BytesIO()

@app.post("/api/preview-form/{form_id}")
async def preview_form(form_id: str, data: UserData):
    tax_results = calculate_tax(data)
    forms_dir = os.path.join(os.path.dirname(__file__), "forms")
    
    if form_id == "1040nr":
        template_path = os.path.join(forms_dir, "f1040nr.pdf")
        
        fields = {
            # Page 1
            'topmostSubform[0].Page1[0].f1_02[0]': data.ssn,
            'topmostSubform[0].Page1[0].f1_04[0]': data.address,
            'topmostSubform[0].Page1[0].f1_05[0]': f"{data.city}, {data.state} {data.zip_code}",
            'topmostSubform[0].Page1[0].f1_14[0]': data.full_name.split()[0] if data.full_name else "",
            'topmostSubform[0].Page1[0].f1_15[0]': " ".join(data.full_name.split()[1:]) if len(data.full_name.split()) > 1 else "",
            
            'topmostSubform[0].Page1[0].f1_42[0]': str(data.wages),  # Line 1a
            'topmostSubform[0].Page1[0].f1_54[0]': str(data.wages),  # Line 1z
            'topmostSubform[0].Page1[0].f1_71[0]': str(data.wages),  # Line 11a
            
            # Page 2
            'topmostSubform[0].Page2[0].f2_01[0]': str(data.wages), # Line 11b
            'topmostSubform[0].Page2[0].f2_02[0]': str(tax_results['itemized_deductions']), # Line 12
            'topmostSubform[0].Page2[0].f2_03[0]': str(tax_results['itemized_deductions']), # Line 13a
            'topmostSubform[0].Page2[0].f2_05[0]': str(tax_results['taxable_income']), # Line 15
            
            'topmostSubform[0].Page2[0].f2_14[0]': str(tax_results['wage_tax']), # Line 21
            'topmostSubform[0].Page2[0].Line23a_ReadOrder[0].f2_16[0]': str(tax_results['wage_tax']), # Line 24
            'topmostSubform[0].Page2[0].Line25_ReadOrder[0].f2_21[0]': str(data.federal_tax_withheld), # Line 25a
            
            'topmostSubform[0].Page2[0].f2_36[0]': str(tax_results['refund']) if tax_results['refund'] > 0 else "", # Refund
            'topmostSubform[0].Page2[0].f2_40[0]': str(tax_results['owe']) if tax_results['owe'] > 0 else "", # Owe
            
            'topmostSubform[0].Page2[0].RoutingNo[0].f2_38[0]': data.routing_number,
            'topmostSubform[0].Page2[0].AccountNo[0].f2_39[0]': data.account_number,
        }
    
    elif form_id == "nec":
        template_path = os.path.join(forms_dir, "f1040nrn.pdf") 
        fields = {} # Placeholder
        
    elif form_id == "8843":
        template_path = os.path.join(forms_dir, "f8843.pdf")
        fields = {} # Placeholder
        
    else:
        raise HTTPException(status_code=404, detail="Form not found")

    pdf_bytes = fill_pdf(template_path, fields)
    return StreamingResponse(pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={form_id}_Preview.pdf"})

@app.post("/api/generate-tax-return")
async def generate_tax_return(data: UserData):
    return await preview_form("1040nr", data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
