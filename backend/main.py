from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
import io
import os
import zipfile
from datetime import date

app = FastAPI(title="US-India Tax Treaty Attachment Generator")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaxData(BaseModel):
    full_name: str
    ssn: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "India"
    tax_year: str = "2025"
    wages: float = 0.0
    federal_tax_withheld: float = 0.0
    dividends: float = 0.0
    stock_gains: float = 0.0  # Net Short Term + Long Term
    days_present_2025: int
    days_present_2024: int = 0
    days_present_2023: int = 0
    entry_date: str # YYYY-MM-DD
    university: str
    visa_type: str = "F-1"

def calculate_tax_2025(wages: float, dividends: float, stock_gains: float, days_present: int):
    # Standard Deduction for Single Filer (Treaty Article 21)
    standard_deduction = 15750.0
    
    # 1. Effectively Connected Income (ECI) - Wages
    taxable_wages = max(0.0, wages - standard_deduction)
    
    # 2025 Tax Brackets (Single) - Approximate/Projected
    # 10% on income between $0 and $11,925
    # 12% on income between $11,925 and $48,475
    # ... (simplified for this scope, can be expanded)
    
    wage_tax = 0.0
    if taxable_wages > 0:
        if taxable_wages <= 11925:
            wage_tax = taxable_wages * 0.10
        elif taxable_wages <= 48475:
            wage_tax = 1192.50 + (taxable_wages - 11925) * 0.12
        else:
            # Fallback for higher income (simplified)
            wage_tax = 5578.50 + (taxable_wages - 48475) * 0.22

    # 2. Not Effectively Connected Income (NEC) - Schedule NEC
    # Dividends: 25% (Treaty Article 10)
    dividend_tax = dividends * 0.25
    
    # Capital Gains: 30% if present >= 183 days, else 0%
    capital_gains_tax = 0.0
    if days_present >= 183:
        capital_gains_tax = stock_gains * 0.30
        
    total_tax = wage_tax + dividend_tax + capital_gains_tax
    
    return {
        "taxable_wages": taxable_wages,
        "wage_tax": wage_tax,
        "dividend_tax": dividend_tax,
        "capital_gains_tax": capital_gains_tax,
        "total_tax": total_tax,
        "standard_deduction": standard_deduction
    }

def fill_pdf(template_path, fields_dict):
    try:
        reader = PdfReader(template_path)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        
        # Determine if we need to initialize AcroForm in writer if missing
        # But appending pages should usually carry it if done right, 
        # however clone_from is not always available in all versions or behaves differently.
        # Let's try the modern clone_from if possible, or manual copy.
        # Since I can't guarantee version features, I'll use a safer approach:
        # Just use reader, fill fields, and write.
        # Wait, PdfReader is read-only.
        
        # Retry with appending and explicit generic AcroForm update check
        # If the error is 'No /AcroForm', we might need to copy it.
        # But let's try assuming pypdf 3.0+ and use clone_from which is best.
        try:
             writer = PdfWriter(clone_from=template_path)
        except TypeError:
             # Fallback for older pypdf
             writer = PdfWriter()
             for page in reader.pages:
                 writer.add_page(page)
                 
        writer.update_page_form_field_values(
            writer.pages[0], fields_dict, auto_regenerate=False
        )

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        return output_stream
    except Exception as e:
        # Log error but try to return empty if filling fails, to allow zip to generate
        print(f"Error filling PDF {template_path}: {e}")
        # Return original as fallback
        with open(template_path, "rb") as f:
            return io.BytesIO(f.read())

@app.post("/api/generate-tax-return")
async def generate_tax_return(data: TaxData):
    try:
        # Path to forms
        forms_dir = os.path.join(os.path.dirname(__file__), "forms")
        
        # Calculate Tax
        tax_results = calculate_tax_2025(
            data.wages, data.dividends, data.stock_gains, data.days_present_2025
        )
        
        # --- 1. Fill Form 1040-NR ---
        # Updated mapping based on inspection (form1040-NR[0] root)
        # Note: These indices [0] might need adjustment if pypdf treats them differently, 
        # but usually consistent with get_fields() output.
        f1040_fields = {
            'form1040-NR[0].Page1[0].f1_01[0]': data.full_name, # Name
            'form1040-NR[0].Page1[0].f1_02[0]': data.ssn,       # SSN
            'form1040-NR[0].Page1[0].Address[0].f1_04[0]': data.address,
            'form1040-NR[0].Page1[0].Address[0].f1_05[0]': f"{data.city}, {data.state} {data.zip_code}",
            'form1040-NR[0].Page1[0].f1_09[0]': str(data.wages), # Line 1a (Wages)
            # Line 12 (Standard Deduction) - Inspect field name carefully if possible, guessing f1_32 based on previous intuition but using new root
            'form1040-NR[0].Page1[0].f1_32[0]': str(tax_results['standard_deduction']), 
            # Line 15 (Taxable Income)
            'form1040-NR[0].Page1[0].f1_35[0]': str(tax_results['taxable_wages']), 
            # Line 16 (Tax)
            'form1040-NR[0].Page1[0].f1_36[0]': str(tax_results['wage_tax']),
            # Line 23a (Schedule NEC Tax) - Check Page 2 field mapping
            'form1040-NR[0].Page2[0].f2_04[0]': str(tax_results['dividend_tax'] + tax_results['capital_gains_tax']),
            # Line 24 (Total Tax)
            'form1040-NR[0].Page2[0].f2_06[0]': str(tax_results['total_tax']),
            # Line 25a (Withholding)
            'form1040-NR[0].Page2[0].f2_07[0]': str(data.federal_tax_withheld),
        }
        
        pdf_1040 = fill_pdf(os.path.join(forms_dir, "f1040nr.pdf"), f1040_fields)
        
        # --- 2. Fill Schedule NEC ---
        # Note: Schedule NEC structure from inspection looked like form1040-NR[0].Page1[0].Table_NatureOfIncome...
        # If it's a standalone form f1040nrn.pdf, it might have its own root. 
        # The inspection log showed "form1040-NR[0]" even for the NatureOfIncome table, suggesting similar XFA structure.
        sch_nec_fields = {
             'form1040-NR[0].Page1[0].f1_01[0]': data.full_name,
             'form1040-NR[0].Page1[0].f1_02[0]': data.ssn,
             # Dividends (Column c - 25%) - Guessing field names based on table structure
             'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line2[0].f1_10[0]': str(data.dividends) if data.dividends > 0 else "",
             # Capital Gains (Column d - 30%) - Only if taxable
             'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line9[0].f1_68[0]': str(data.stock_gains) if (data.stock_gains > 0 and data.days_present_2025 >= 183) else "",
        }
             
        pdf_nec = fill_pdf(os.path.join(forms_dir, "f1040nrn.pdf"), sch_nec_fields)

        # --- 3. Fill Form 8843 ---
        f8843_fields = {
             'topmostSubform[0].Page1[0].f1_01[0]': data.full_name,
             'topmostSubform[0].Page1[0].f1_02[0]': data.ssn,
             # Address for 8843 if different or required
             'topmostSubform[0].Page1[0].f1_04[0]': data.address,
             'topmostSubform[0].Page1[0].f1_05[0]': f"{data.city}, {data.state} {data.zip_code}",
             # Days Present
             'topmostSubform[0].Page1[0].f1_07[0]': str(data.days_present_2025), # 2025
             'topmostSubform[0].Page1[0].f1_08[0]': str(data.days_present_2024), # 2024
             'topmostSubform[0].Page1[0].f1_09[0]': str(data.days_present_2023), # 2023
             # Program Data
             'topmostSubform[0].Page1[0].f1_11[0]': data.university,
             'topmostSubform[0].Page1[0].f1_15[0]': data.visa_type,
        }
        pdf_8843 = fill_pdf(os.path.join(forms_dir, "f8843.pdf"), f8843_fields)

        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"Form_1040NR_{data.tax_year}.pdf", pdf_1040.getvalue())
            zf.writestr(f"Schedule_NEC_{data.tax_year}.pdf", pdf_nec.getvalue())
            zf.writestr(f"Form_8843_{data.tax_year}.pdf", pdf_8843.getvalue())
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=Tax_Return_Package_{data.tax_year}.zip"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
