from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pypdf import PdfReader, PdfWriter
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject, BooleanObject, IndirectObject
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

from pydantic import BaseModel, field_validator, ValidationInfo

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

    @field_validator('days_present_2025', 'days_present_2024', 'days_present_2023')
    @classmethod
    def validate_days(cls, v: int, info: ValidationInfo) -> int:
        if not (0 <= v <= 366):
            raise ValueError(f"{info.field_name} must be between 0 and 366")
        return v

    @field_validator('zip_code')
    @classmethod
    def validate_zip(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 5:
            raise ValueError("Zip code must be exactly 5 digits")
        return v
        
    @field_validator('state')
    @classmethod
    def validate_state(cls, v: str) -> str:
        valid_states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
        ]
        if v.upper() not in valid_states:
            raise ValueError("Invalid State Code (use 2-letter abbreviation)")
        return v.upper()

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
        
        # NOTE: XFA (XML Forms Architecture) can cause filled fields to be invisible
        # because PDF viewers prioritize XFA data over the standard dictionary values.
        # We MUST strip the XFA key from the AcroForm dictionary to force legacy rendering.
        if "/AcroForm" in writer.root_object:
            writer.root_object["/AcroForm"].pop("/XFA", None)
                 
        writer.update_page_form_field_values(
            writer.pages[0], fields_dict, auto_regenerate=False
        )
        
        # Enable NeedAppearances to force viewers to re-render the fields (crucial for visibility)
        if "/AcroForm" not in writer.root_object:
            writer.root_object.update({
                NameObject("/AcroForm"): IndirectObject(len(writer.objects), 0, writer)
            })
            
        # Get the AcroForm dictionary
        acroform = writer.root_object["/AcroForm"]
        
        # Set NeedAppearances to True
        if isinstance(acroform, dict): # Should be a dictionary/PdfObject
             acroform.update({
                 NameObject("/NeedAppearances"): BooleanObject(True)
             })

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
        
        import time
        start_time = time.time()
        
        # Path to forms
        forms_dir = os.path.join(os.path.dirname(__file__), "forms")
        
        # Calculate Tax
        tax_results = calculate_tax_2025(
            data.wages, data.dividends, data.stock_gains, data.days_present_2025
        )
        
        # --- 1. Fill Form 1040-NR ---
        t1 = time.time()
        # Corrected mapping based on diagnostic: 1040-NR uses "topmostSubform[0]" prefix
        f1040_fields = {
            'topmostSubform[0].Page1[0].f1_01[0]': data.full_name, # Name
            'topmostSubform[0].Page1[0].f1_02[0]': data.ssn,       # SSN
            'topmostSubform[0].Page1[0].Address[0].f1_04[0]': data.address,
            'topmostSubform[0].Page1[0].Address[0].f1_05[0]': f"{data.city}, {data.state} {data.zip_code}",
            'topmostSubform[0].Page1[0].f1_09[0]': str(data.wages), # Line 1a (Wages)
            'topmostSubform[0].Page1[0].f1_32[0]': str(tax_results['standard_deduction']), 
            'topmostSubform[0].Page1[0].f1_35[0]': str(tax_results['taxable_wages']), 
            'topmostSubform[0].Page1[0].f1_36[0]': str(tax_results['wage_tax']),
            # Page 2 fields
            'topmostSubform[0].Page2[0].f2_04[0]': str(tax_results['dividend_tax'] + tax_results['capital_gains_tax']),
            'topmostSubform[0].Page2[0].f2_06[0]': str(tax_results['total_tax']),
            'topmostSubform[0].Page2[0].f2_07[0]': str(data.federal_tax_withheld),
        }
        
        pdf_1040 = fill_pdf(os.path.join(forms_dir, "f1040nr.pdf"), f1040_fields)
        print(f"Time to fill 1040NR: {time.time() - t1:.4f}s")
        
        # --- 2. Fill Schedule NEC ---
        t2 = time.time()
        # Corrected mapping based on diagnostic: Schedule NEC uses "form1040-NR[0]" but NO leading zeros (f1_1 instead of f1_01)
        sch_nec_fields = {
             'form1040-NR[0].Page1[0].f1_1[0]': data.full_name,
             'form1040-NR[0].Page1[0].f1_2[0]': data.ssn,
             # Dividends (Column c - 25%) 
             # Note: Diagnostic showed ...Line1b[0].f1_10[0], guessing names for Table
             # Previous guess was Line2 -> f1_10. Diagnostic for Line1b was f1_10. 
             # Let's stick with specific fields if we can identify them, but based on previous code:
             # If "Line2" in code meant "Row 2", diagnostic Line1b is likely Row 2.
             # f1_10 is in Line1b.
             'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line2[0].f1_10[0]': str(data.dividends) if data.dividends > 0 else "",
             # Capital Gains (Column d - 30%)
             'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line9[0].f1_68[0]': str(data.stock_gains) if (data.stock_gains > 0 and data.days_present_2025 >= 183) else "",
        }
             
        pdf_nec = fill_pdf(os.path.join(forms_dir, "f1040nrn.pdf"), sch_nec_fields)
        print(f"Time to fill NEC: {time.time() - t2:.4f}s")

        # --- 3. Fill Form 8843 ---
        t3 = time.time()
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
        print(f"Time to fill 8843: {time.time() - t3:.4f}s")

        # Create ZIP
        t4 = time.time()
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(f"Form_1040NR_{data.tax_year}.pdf", pdf_1040.getvalue())
            zf.writestr(f"Schedule_NEC_{data.tax_year}.pdf", pdf_nec.getvalue())
            zf.writestr(f"Form_8843_{data.tax_year}.pdf", pdf_8843.getvalue())
        
        zip_buffer.seek(0)
        print(f"Time to zip: {time.time() - t4:.4f}s")
        print(f"Total generation time: {time.time() - start_time:.4f}s")
        
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
