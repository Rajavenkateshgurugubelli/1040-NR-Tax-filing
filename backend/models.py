from pydantic import BaseModel
from typing import Optional

class UserData(BaseModel):
    # Personal Info
    tax_year: int = 2025 # Default to current tax year
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
