from .models import UserData
from .treaty_logic import TaxTreaty

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
        standard_deduction = TaxTreaty.get_standard_deduction(data.country_of_residence, data.tax_year)
        
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
    
    # 6. Tax Calculation (Multi-Year Support)
    # Source: IRS Revenue Procedures for each year
    TAX_BRACKETS = {
        2025: [
            (11925, 0.10),
            (48475, 0.12),
            (103350, 0.22),
            (197300, 0.24),
            (250525, 0.32),
            (626350, 0.35),
            (float('inf'), 0.37)
        ],
        2024: [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37)
        ],
        2023: [
            (11000, 0.10),
            (44725, 0.12),
            (95375, 0.22),
            (182100, 0.24),
            (231250, 0.32),
            (578125, 0.35),
            (float('inf'), 0.37)
        ]
    }

    tax = 0
    income = taxable_income
    
    # Get brackets for the specific year, default to 2025
    brackets = TAX_BRACKETS.get(data.tax_year, TAX_BRACKETS[2025])
    
    previous_limit = 0
    
    for limit, rate in brackets:
        if income > previous_limit:
            taxable_amount = min(income, limit) - previous_limit
            tax += taxable_amount * rate
            previous_limit = limit
        else:
            break
        
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
