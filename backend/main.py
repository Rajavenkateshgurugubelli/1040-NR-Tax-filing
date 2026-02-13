from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import io
import subprocess
import tempfile
from fastapi.responses import StreamingResponse
from PyPDF2 import PdfMerger

try:
    from .treaty_logic import TaxTreaty
except ImportError:
    from treaty_logic import TaxTreaty

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
    date_of_birth: Optional[str] = ""  # YYYY-MM-DD
    phone_number: Optional[str] = ""
    email: Optional[str] = ""
    occupation: Optional[str] = ""
    
    # US Address
    address: str
    city: str
    state: str
    zip_code: str
    
    # Foreign Address (if different from US address)
    has_foreign_address: Optional[bool] = False
    foreign_address: Optional[str] = ""
    foreign_city: Optional[str] = ""
    foreign_province: Optional[str] = ""  # Province/State/County
    foreign_postal_code: Optional[str] = ""
    foreign_country: Optional[str] = ""
    
    # Country & Filing Status
    country_of_residence: Optional[str] = ""
    filing_status: Optional[str] = "Single"  # Single, Married Filing Separately, Married Filing Jointly
    
    # Spouse Information (if married)
    spouse_name: Optional[str] = ""
    spouse_ssn: Optional[str] = ""
    
    # Visa / Immigration Fields
    visa_type: Optional[str] = "F1"  # F1, J1, H1B, Other
    is_student: Optional[bool] = True
    entry_date: Optional[str] = None  # YYYY-MM-DD
    days_present_2025: Optional[int] = 365
    days_present_2024: Optional[int] = 0
    days_present_2023: Optional[int] = 0
    
    # Income - W-2 Wages
    wages: float  # W-2 Box 1
    federal_tax_withheld: float  # W-2 Box 2
    social_security_tax_withheld: Optional[float] = 0.0  # Box 4 (Should be 0 for F1/J1)
    medicare_tax_withheld: Optional[float] = 0.0  # Box 6 (Should be 0 for F1/J1)
    state_tax_withheld: Optional[float] = 0.0  # W-2 Box 17 (Deduction)
    
    # Income - Additional Sources
    dividend_income: Optional[float] = 0.0  # 1099-DIV
    interest_income: Optional[float] = 0.0  # 1099-INT
    capital_gains: Optional[float] = 0.0  # 1099-B (Short-term + Long-term)
    capital_losses: Optional[float] = 0.0  # 1099-B
    scholarship_grants: Optional[float] = 0.0  # Taxable portion only
    fellowship_grants: Optional[float] = 0.0  # Taxable portion only
    other_income: Optional[float] = 0.0  # Other miscellaneous income
    
    # Deductions
    charitable_contributions: Optional[float] = 0.0
    student_loan_interest: Optional[float] = 0.0  # Max $2,500
    moving_expenses: Optional[float] = 0.0  # For military only (post-TCJA)
    
    # Tax Credits
    education_credits: Optional[float] = 0.0  # Form 8863 (American Opportunity, Lifetime Learning)
    
    # Banking - Direct Deposit
    routing_number: Optional[str] = ""
    account_number: Optional[str] = ""
    account_type: Optional[str] = "Checking"  # Checking or Savings
    bank_name: Optional[str] = ""

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
        try:
            entry_year = int(data.entry_date.split('-')[0])
            current_year = 2025
            years_in_us = current_year - entry_year + 1
            
            # F-1 students: exempt for 5 calendar years
            # J-1 students: exempt for 2 years (non-students) or 5 years (students)
            if data.visa_type == 'F1' and years_in_us <= 5:
                is_exempt_individual = True
            elif data.visa_type == 'J1':
                if data.is_student and years_in_us <= 5:
                    is_exempt_individual = True
                elif not data.is_student and years_in_us <= 2:
                    is_exempt_individual = True
        except Exception:
            pass # Invalid date format

    if is_exempt_individual and total_fica > 0:
        warnings.append(f"WARNING: You had ${total_fica:.2f} in FICA taxes withheld. Based on your entry date ({data.entry_date}), you are an Exempt Individual and should not pay FICA. Ask your employer for a refund.")
    
    # 2. Substantial Presence Test (SPT)
    # Exempt Individuals are excluded from SPT calculation
    is_resident_alien = False
    if not is_exempt_individual:
        days_2025 = data.days_present_2025 or 0
        days_2024 = data.days_present_2024 or 0
        days_2023 = data.days_present_2023 or 0
        
        spt_days = days_2025 + (days_2024 / 3) + (days_2023 / 6)
        if days_2025 >= 31 and spt_days >= 183:
            is_resident_alien = True
            warnings.append(f"CRITICAL: You meet the Substantial Presence Test ({spt_days:.1f} weighted days). You are likely a Resident Alien for Tax Purposes. This tool (1040-NR) is NOT for you. You should file Form 1040.")

    if is_resident_alien and total_fica == 0:
        warnings.append("WARNING: You are a Resident Alien (SPT met) but had $0 FICA withheld. You likely owe FICA taxes (Social Security + Medicare).")

    # 3. Income Adjustments (Treaty Exemption)
    # E.g. China $5000 exemption
    treaty_exemption = 0
    if data.country_of_residence:
        treaty_exemption = TaxTreaty.get_income_exemption(data.country_of_residence)
    
    # Adjusted Gross Income for Tax Purposes
    
    taxable_wages_after_treaty = max(0, data.wages - treaty_exemption)

    # 4. State Tax Validation Logic
    NO_INCOME_TAX_STATES = ["TX", "FL", "WA", "TN", "NH", "NV", "SD", "WY", "AK"]
    HIGH_TAX_STATES = ["CA", "NY", "NJ", "OR", "MN", "HI"]
    
    state_tax = data.state_tax_withheld or 0
    state = data.state.upper() if data.state else ""
    
    if state in NO_INCOME_TAX_STATES and state_tax > 0:
        warnings.append(f"WARNING: You entered ${state_tax:.2f} state tax withheld, but {state} has NO state income tax. Please verify Box 17 of your W-2.")
        
    if state in HIGH_TAX_STATES and state_tax == 0:
        warnings.append(f"WARNING: You live in {state} (a high-tax state) but entered $0 state tax withheld. You likely owe state taxes. Check your W-2 Box 17.")

    # 5. Deduction Logic (Itemized vs Standard)
    # NRAs generally cannot claim Standard Deduction.
    # Exception: India (Article 21(2))
    
    itemized_deductions = state_tax + (data.charitable_contributions or 0)
    
    standard_deduction = 0
    if data.country_of_residence:
        standard_deduction = TaxTreaty.get_standard_deduction(data.country_of_residence)
        
    final_deduction = 0
    
    if standard_deduction > 0 and standard_deduction > itemized_deductions:
        final_deduction = standard_deduction
        # Success message already added later
    else:
        final_deduction = itemized_deductions
        if final_deduction > 0:
            warnings.append(f"NOTE: You are claiming Itemized Deductions (${final_deduction:.2f}). You MUST file Schedule A (Form 1040-NR) with your return.")

    # 6. Taxable Income
    taxable_income = max(0, taxable_wages_after_treaty - final_deduction)
    
    # 6. Tax Calculation (2025 Single Filer Tax Brackets - Official IRS)
    # Source: IRS 2025 Tax Brackets
    # 10% on income up to $11,925
    # 12% on income $11,926 to $48,475
    # 22% on income $48,476 to $103,350
    # 24% on income $103,351 to $197,300
    # 32% on income $197,301 to $250,525
    # 35% on income $250,526 to $626,350
    # 37% on income above $626,350
    
    tax = 0
    income = taxable_income
    
    if income <= 11925:
        tax = income * 0.10
    elif income <= 48475:
        tax = 11925 * 0.10 + (income - 11925) * 0.12
    elif income <= 103350:
        tax = 11925 * 0.10 + (48475 - 11925) * 0.12 + (income - 48475) * 0.22
    elif income <= 197300:
        tax = 11925 * 0.10 + (48475 - 11925) * 0.12 + (103350 - 48475) * 0.22 + (income - 103350) * 0.24
    elif income <= 250525:
        tax = 11925 * 0.10 + (48475 - 11925) * 0.12 + (103350 - 48475) * 0.22 + (197300 - 103350) * 0.24 + (income - 197300) * 0.32
    elif income <= 626350:
        tax = 11925 * 0.10 + (48475 - 11925) * 0.12 + (103350 - 48475) * 0.22 + (197300 - 103350) * 0.24 + (250525 - 197300) * 0.32 + (income - 250525) * 0.35
    else:
        tax = 11925 * 0.10 + (48475 - 11925) * 0.12 + (103350 - 48475) * 0.22 + (197300 - 103350) * 0.24 + (250525 - 197300) * 0.32 + (626350 - 250525) * 0.35 + (income - 626350) * 0.37
        
    # 7. NEC Tax Calculation (Schedule NEC)
    # Dividends
    dividend_rate = 0.30 # Default 30%
    if data.country_of_residence:
        dividend_rate = TaxTreaty.get_dividend_rate(data.country_of_residence) / 100.0
        
    dividend_tax = (data.dividend_income or 0) * dividend_rate
    
    # Interest (Default 30% for now, as portfolio interest exemption requires more complex validation)
    interest_tax = (data.interest_income or 0) * 0.30
    
    nec_tax = round(dividend_tax + interest_tax, 2)
    
    total_tax = round(tax + nec_tax, 2)
    
    if treaty_exemption > 0:
        warnings.append(f"SUCCESS: Applied ${treaty_exemption} income exemption based on {data.country_of_residence} tax treaty.")
    if standard_deduction > 0 and final_deduction == standard_deduction:
        warnings.append(f"SUCCESS: Applied Standard Deduction of ${standard_deduction} based on {data.country_of_residence} tax treaty (Article {TaxTreaty.get_treaty_article(data.country_of_residence, 'standard_deduction')}).")
    if nec_tax > 0:
        warnings.append(f"NOTE: You have ${nec_tax} in tax on passive income (Schedule NEC). This is added to your total tax liability.")

    return {
        "taxable_wages": data.wages,
        "treaty_exemption": treaty_exemption,
        "itemized_deductions": final_deduction,
        "taxable_income": taxable_income,
        "total_tax": total_tax,
        "wage_tax": round(tax, 2),
        "nec_tax": nec_tax,
        "refund": max(0, data.federal_tax_withheld - total_tax),
        "owe": max(0, total_tax - data.federal_tax_withheld),
        "warnings": warnings,
        "dividend_rate": int(dividend_rate * 100)
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
            output_bytes = f.read() # Return bytes directly
            
        os.remove(fdf_path)
        os.remove(output_path)
        return output_bytes
    except Exception as e:
        print(f"Error filling PDF: {e}")
        return b"" # Return empty bytes on error instead of BytesIO

def populate_schedule_nec(data: UserData):
    """
    Populate Schedule NEC fields based on Dividend and Interest income.
    """
    fields = {}
    
    # 1. Dividends (Line 1a)
    div_income = data.dividend_income or 0
    if div_income > 0:
        rate = TaxTreaty.get_dividend_rate(data.country_of_residence) if data.country_of_residence else 30
        
        # Map rate to column
        if rate == 10:
            col_field = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_5[0]' # Col A 10%
        elif rate == 15:
            col_field = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_6[0]' # Col B 15%
        elif rate == 30:
            col_field = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_7[0]' # Col C 30%
        else:
             col_field = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_8[0]' # Col D Other
             
        fields[col_field] = str(div_income)
        fields['form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_9[0]'] = str(div_income) # Total
        
    # 2. Interest (Line 2a) - Defaulting to 30% (Col C) for now
    int_income = data.interest_income or 0
    if int_income > 0:
        # Col C (30%)
        fields['form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line2a[0].f1_22[0]'] = str(int_income)
        fields['form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line2a[0].f1_24[0]'] = str(int_income) # Total
        
    return fields

async def generate_pdf_bytes(form_id: str, data: UserData):
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
            'topmostSubform[0].Page2[0].f2_15[0]': str(tax_results['nec_tax']), # Line 23a
            'topmostSubform[0].Page2[0].Line23a_ReadOrder[0].f2_16[0]': str(tax_results['total_tax']), # Line 24
            'topmostSubform[0].Page2[0].Line25_ReadOrder[0].f2_21[0]': str(data.federal_tax_withheld), # Line 25a
            
            'topmostSubform[0].Page2[0].f2_36[0]': str(tax_results['refund']) if tax_results['refund'] > 0 else "", # Refund
            'topmostSubform[0].Page2[0].f2_40[0]': str(tax_results['owe']) if tax_results['owe'] > 0 else "", # Owe
            
            'topmostSubform[0].Page2[0].RoutingNo[0].f2_38[0]': data.routing_number,
            'topmostSubform[0].Page2[0].AccountNo[0].f2_39[0]': data.account_number,
        }
    
    elif form_id == "nec":
        template_path = os.path.join(forms_dir, "f1040nrn.pdf") 
        fields = populate_schedule_nec(data)
        
    elif form_id == "8843":
        template_path = os.path.join(forms_dir, "f8843.pdf")
        fields = {} # Placeholder
        
    else:
        raise HTTPException(status_code=404, detail="Form not found")

    return fill_pdf(template_path, fields)

@app.post("/api/preview-form/{form_id}")
async def preview_form(form_id: str, data: UserData):
    pdf_bytes = await generate_pdf_bytes(form_id, data)
    return StreamingResponse(
        io.BytesIO(pdf_bytes), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={form_id}_Preview.pdf"}
    )

@app.post("/api/calculate-tax")
async def calculate_tax_api(data: UserData):
    """
    Returns the tax calculation summary and warnings (JSON) without generating PDF.
    """
    return calculate_tax(data)

@app.post("/api/generate-tax-return")
async def generate_tax_return(data: UserData):
    return await preview_form("1040nr", data)

@app.post("/api/download-complete-package")
async def download_complete_package(data: UserData):
    """
    Merge all tax forms into a single PDF package for download.
    Includes: 1040-NR, Form 8843, and Schedule NEC (if applicable).
    """
    try:
        merger = PdfMerger()
        
        # Generate 1040-NR
        pdf_1040nr = await generate_pdf_bytes("1040nr", data)
        if pdf_1040nr:
            merger.append(io.BytesIO(pdf_1040nr))
        
        # Check if Schedule NEC is needed
        tax_results = calculate_tax(data)
        if tax_results.get('nec_tax', 0) > 0:
             pdf_nec = await generate_pdf_bytes("nec", data)
             if pdf_nec:
                 merger.append(io.BytesIO(pdf_nec))
        
        # Generate Form 8843
        pdf_8843 = await generate_pdf_bytes("8843", data)
        if pdf_8843:
            merger.append(io.BytesIO(pdf_8843))
        
        # Write merged PDF to BytesIO
        output = io.BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        
        # Return as downloadable PDF
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Tax_Package_2025.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging PDFs: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
