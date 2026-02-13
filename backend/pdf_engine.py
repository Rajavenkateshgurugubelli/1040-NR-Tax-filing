
import os
import io
import subprocess
import tempfile
from fastapi import HTTPException
from .models import UserData
from .tax_engine import calculate_tax
from .treaty_logic import TaxTreaty

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
