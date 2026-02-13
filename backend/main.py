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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserData(BaseModel):
    full_name: str
    ssn: str
    address: str
    city: str
    state: str
    zip_code: str
    wages: float
    federal_tax_withheld: float
    # New banking fields
    routing_number: Optional[str] = ""
    account_number: Optional[str] = ""
    account_type: Optional[str] = "Checking"

def calculate_tax(data: UserData):
    # Simplified tax calculation logic for NRA
    # This would be replaced by the full engine later
    standard_deduction = 0  # NRA usually 0
    taxable_wages = data.wages
    
    # 2025 Tax Brackets (Single) - Approximate
    tax = 0
    income = taxable_wages
    
    if income > 11600:
        tax += (min(income, 47150) - 11600) * 0.12
        tax += 11600 * 0.10
    else:
        tax += income * 0.10
        
    return {
        "taxable_wages": taxable_wages,
        "standard_deduction": standard_deduction,
        "total_tax": round(tax, 2),
        "wage_tax": round(tax, 2), # Assuming only wage income for now
        "refund": max(0, data.federal_tax_withheld - tax),
        "owe": max(0, tax - data.federal_tax_withheld)
    }

def generate_fdf(fields):
    """
    Generate FDF content from a dictionary of field names and values.
    """
    fdf = "%FDF-1.2\n1 0 obj\n<<\n/FDF << /Fields [\n"
    for key, value in fields.items():
        # Handle None
        if value is None:
            value = ""
        # Convert to string and escape parenthesis
        value_str = str(value).replace("(", "\\(").replace(")", "\\)")
        fdf += f"<< /T ({key}) /V ({value_str}) >>\n"
    fdf += "] >>\n>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    return fdf

def fill_pdf(template_path, fields_dict):
    """
    Fill PDF using PDFtk Server.
    """
    try:
        # Create temp FDF file
        fdf_content = generate_fdf(fields_dict)
        fd, fdf_path = tempfile.mkstemp(suffix='.fdf')
        with os.fdopen(fd, 'w') as f:
            f.write(fdf_content)
            
        # Define output path
        output_path = template_path.replace('.pdf', '_filled.pdf')
        
        # PDFtk command
        pdftk_cmd = [
            r"C:\Program Files (x86)\PDFtk Server\bin\pdftk.exe",
            template_path,
            "fill_form", fdf_path,
            "output", output_path,
            "flatten"  # Critical: Flatten form fields
        ]
        
        # Run PDFtk
        subprocess.run(pdftk_cmd, check=True)
        
        # Read the result
        with open(output_path, "rb") as f:
            output_bytes = io.BytesIO(f.read())
            
        # Cleanup
        os.remove(fdf_path)
        os.remove(output_path)
        
        return output_bytes
        
    except Exception as e:
        print(f"Error filling PDF {template_path}: {e}")
        # Return empty on failure to prevent crash
        return io.BytesIO()

@app.post("/api/fill-pdf")
async def generate_filled_pdf(data: UserData):
    # Calculate tax results first
    tax_results = calculate_tax(data)
    
    forms_dir = os.path.join(os.path.dirname(__file__), "forms")
    
    # --- 1. Fill Form 1040-NR ---
    # COMPLETE FIELD MAPPING (User Verified)
    f1040_fields = {
        # --- Page 1 ---
        'topmostSubform[0].Page1[0].f1_02[0]': data.ssn,        # SSN
        'topmostSubform[0].Page1[0].f1_04[0]': data.address,    # Address
        'topmostSubform[0].Page1[0].f1_05[0]': f"{data.city}, {data.state} {data.zip_code}", # City/State/ZIP
        'topmostSubform[0].Page1[0].f1_14[0]': data.full_name.split()[0] if data.full_name else "", # First Name
        'topmostSubform[0].Page1[0].f1_15[0]': " ".join(data.full_name.split()[1:]) if len(data.full_name.split()) > 1 else "", # Last Name
        
        'topmostSubform[0].Page1[0].f1_42[0]': str(data.wages),  # Line 1a: W-2 Wages
        'topmostSubform[0].Page1[0].f1_54[0]': str(data.wages),  # Line 1z: Total (W-2)
        'topmostSubform[0].Page1[0].f1_71[0]': str(tax_results['taxable_wages']),  # Line 11a: AGI (Page 1)
        
        # --- Page 2 ---
        'topmostSubform[0].Page2[0].f2_01[0]': str(tax_results['taxable_wages']), # Line 11b: AGI Carryover
        'topmostSubform[0].Page2[0].f2_03[0]': "0",  # Line 13a: Adjustments
        'topmostSubform[0].Page2[0].f2_14[0]': str(tax_results['wage_tax']), # Line 21: Computed Tax
        
        # Special Containers for Totals
        'topmostSubform[0].Page2[0].Line23a_ReadOrder[0].f2_16[0]': str(tax_results['wage_tax']), # Line 23a: Should be total tax (simplified)
        'topmostSubform[0].Page2[0].Line25_ReadOrder[0].f2_21[0]': str(data.federal_tax_withheld), # Line 25a: Withholding
        
        # Banking (Direct Deposit)
        'topmostSubform[0].Page2[0].RoutingNo[0].f2_38[0]': data.routing_number, # Line 35b
        'topmostSubform[0].Page2[0].AccountNo[0].f2_39[0]': data.account_number, # Line 35d
    }
    
    pdf_1040 = fill_pdf(os.path.join(forms_dir, "f1040nr.pdf"), f1040_fields)
    
    # Return the PDF directly
    return StreamingResponse(
        pdf_1040, 
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=1040NR_Complete.pdf"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
