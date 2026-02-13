from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import io
import subprocess
import tempfile
from fastapi.responses import StreamingResponse
from .treaty_logic import TaxTreaty

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
    entry_date: Optional[str] = None # YYYY-MM-DD
    days_present_2025: Optional[int] = 365
    days_present_2024: Optional[int] = 0
    days_present_2023: Optional[int] = 0
    
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
    
    # 1. Residency & FICA Exemption Check
    # F-1/J-1 students are exempt from FICA for 5 calendar years.
    total_fica = (data.social_security_tax_withheld or 0) + (data.medicare_tax_withheld or 0)
    
    is_exempt_individual = False
    if data.entry_date:
        entry_year = int(data.entry_date.split('-')[0])
        current_year = 2025
        years_in_us = current_year - entry_year + 1
        
        # Simplified: F-1 students exempt for 5 calendar years
        if data.visa_type == 'F1' and years_in_us <= 5:
            is_exempt_individual = True
        elif data.visa_type == 'J1' and years_in_us <= 2: # Assuming non-student J1 for conservative check, need refined logic later
             is_exempt_individual = True # actually J-1 students are also 5 years.
             if data.is_student: is_exempt_individual = True if years_in_us <= 5 else False

    if is_exempt_individual and total_fica > 0:
        warnings.append(f"WARNING: You had ${total_fica:.2f} in FICA taxes withheld. Based on your entry date ({data.entry_date}), you are an Exempt Individual and should not pay FICA. Ask your employer for a refund.")
    
    # 2. Substantial Presence Test (SPT)
    # If NOT an Exempt Individual, check days.
    is_resident_alien = False
    if not is_exempt_individual:
        days_2025 = data.days_present_2025 or 0
        days_2024 = data.days_present_2024 or 0 # Note: Frontend doesn't capture this yet, assumming 0 or needs update
        days_2023 = data.days_present_2023 or 0 # Note: Frontend doesn't capture this yet
        
        spt_days = days_2025 + (days_2024 / 3) + (days_2023 / 6)
        if days_2025 >= 31 and spt_days >= 183:
            is_resident_alien = True
            warnings.append(f"CRITICAL: You meet the Substantial Presence Test ({spt_days:.1f} weighted days). You are likely a Resident Alien for Tax Purposes. This tool (1040-NR) is NOT for you. You should file Form 1040.")
        elif total_fica == 0 and data.visa_type in ['F1', 'J1']:
             # Not exempt, but not RA? (e.g. less than 183 days).
             # If less than 183 days, still NRA. FICA applies only if RA?
             # Actually, FICA applies if you are RA.
             # If you are NRA but NOT exempt (e.g. invalid F1 status?), FICA applies?
             # Generally F1/J1 employment authorization implies FICA exemption ONLY if "Nonresident Alien".
             # If NRA but fails 5 year rule? Wait, 5 year rule DETERMINES if you are Exempt Individual (from SPT).
             pass

    if is_resident_alien and total_fica == 0:
         warnings.append("WARNING: You are a Resident Alien (SPT met) but had $0 FICA withheld. You likely owe FICA taxes (Social Security + Medicare).")

    # 3. Income Adjustments (Treaty Exemption)
    # E.g. China $5000 exemption
    treaty_exemption = 0
    if data.country_of_residence:
        treaty_exemption = TaxTreaty.get_income_exemption(data.country_of_residence)
    
    # Adjusted Gross Income for Tax Purposes
    # Subtract treaty exempt income from wages effectively or treat as deduction?
    # Usually: Total Wages -> Subtract Treaty Exempt Income -> AGI on 1040-NR Line 1a vs 1z logic.
    # For now, treat as a reduction in taxable wages via Line 1z (Exempt under treaty).
    
    taxable_wages_after_treaty = max(0, data.wages - treaty_exemption)

    # 4. Deduction Logic
    # NRAs generally cannot claim Standard Deduction.
    # Exception: India (Article 21(2))
    
    itemized_deductions = (data.state_tax_withheld or 0) + (data.charitable_contributions or 0)
    
    standard_deduction = 0
    if data.country_of_residence:
        standard_deduction = TaxTreaty.get_standard_deduction(data.country_of_residence)
        
    final_deduction = max(itemized_deductions, standard_deduction)
    
    # 5. Taxable Income
    taxable_income = max(0, taxable_wages_after_treaty - final_deduction)
    
    # 6. Tax Calculation (2025 Single Brackets - Simplified)
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
    
    if treaty_exemption > 0:
        warnings.append(f"SUCCESS: Applied ${treaty_exemption} income exemption based on {data.country_of_residence} tax treaty.")
    if standard_deduction > 0 and final_deduction == standard_deduction:
        warnings.append(f"SUCCESS: Applied Standard Deduction of ${standard_deduction} based on {data.country_of_residence} tax treaty (Article {TaxTreaty.get_treaty_article(data.country_of_residence, 'standard_deduction')}).")

    return {
        "taxable_wages": data.wages,
        "treaty_exemption": treaty_exemption,
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

@app.post("/api/calculate-tax")
async def calculate_tax_api(data: UserData):
    """
    Returns the tax calculation summary and warnings (JSON) without generating PDF.
    """
    return calculate_tax(data)

@app.post("/api/generate-tax-return")
async def generate_tax_return(data: UserData):
    return await preview_form("1040nr", data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
