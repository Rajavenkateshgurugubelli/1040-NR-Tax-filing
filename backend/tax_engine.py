from decimal import Decimal, ROUND_HALF_UP
from .models import UserData
from .treaty_logic import TaxTreaty

def calculate_tax(data: UserData):
    """
    Enterprise Tax Calculation Engine for Non-Resident Aliens (F-1/J-1)
    Uses decimal.Decimal for IRS-grade precision.
    """
    warnings = []
    
    # Helper to convert to Decimal safely
    def D(val):
        if val is None:
            return Decimal('0.00')
        return Decimal(str(val))

    # 1. Residency & FICA Exemption Check
    # F-1/J-1 students are exempt from FICA for 5 calendar years.
    total_fica = D(data.social_security_tax_withheld) + D(data.medicare_tax_withheld)
    
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

    if is_exempt_individual and total_fica > Decimal('0'):
        warnings.append(f"WARNING: You had ${total_fica} in FICA taxes withheld. Based on your entry date ({data.entry_date}), you are an Exempt Individual and should not pay FICA. Ask your employer for a refund.")
    
    # 2. Substantial Presence Test (SPT)
    # Exempt Individuals are excluded from SPT calculation
    # Formula: Days_Current + (1/3 * Days_Last) + (1/6 * Days_2Ago)
    is_resident_alien = False
    if not is_exempt_individual:
        days_2025 = D(data.days_present_2025)
        days_2024 = D(data.days_present_2024)
        days_2023 = D(data.days_present_2023)
        
        # Use simple Decimal division for SPT
        spt_days = days_2025 + (days_2024 / Decimal('3')) + (days_2023 / Decimal('6'))
        
        # Round SPT to nearest decimal or just check >= 183? IRS says "at least 183 days". Fraction counts? 
        # Usually checking >= 183 is sufficient.
        if days_2025 >= 31 and spt_days >= 183:
            is_resident_alien = True
            warnings.append(f"CRITICAL: You meet the Substantial Presence Test ({spt_days:.1f} weighted days). You are likely a Resident Alien for Tax Purposes. This tool (1040-NR) is NOT for you. You should file Form 1040.")

    if is_resident_alien and total_fica == Decimal('0'):
        warnings.append("WARNING: You are a Resident Alien (SPT met) but had $0 FICA withheld. You likely owe FICA taxes (Social Security + Medicare).")

    # 3. Income Adjustments (Treaty Exemption)
    # E.g. China $5000 exemption
    treaty_exemption = Decimal('0')
    if data.country_of_residence:
        # Assuming TaxTreaty now returns integer, convert to Decimal
        raw_limit = D(TaxTreaty.get_income_exemption(data.country_of_residence))
        wages_d = D(data.wages)
        treaty_exemption = min(wages_d, raw_limit)
    
    # Adjusted Gross Income for Tax Purposes
    wages = D(data.wages)
    taxable_wages_after_treaty = max(Decimal('0'), wages - treaty_exemption)

    # 4. State Tax Validation Logic
    NO_INCOME_TAX_STATES = ["TX", "FL", "WA", "TN", "NH", "NV", "SD", "WY", "AK"]
    HIGH_TAX_STATES = ["CA", "NY", "NJ", "OR", "MN", "HI"]
    
    state_tax = D(data.state_tax_withheld)
    state = data.state.upper() if data.state else ""
    
    if state in NO_INCOME_TAX_STATES and state_tax > Decimal('0'):
        warnings.append(f"WARNING: You entered ${state_tax} state tax withheld, but {state} has NO state income tax. Please verify Box 17 of your W-2.")
        
    if state in HIGH_TAX_STATES and state_tax == Decimal('0'):
        warnings.append(f"WARNING: You live in {state} (a high-tax state) but entered $0 state tax withheld. You likely owe state taxes. Check your W-2 Box 17.")

    # 5. Deduction Logic (Itemized vs Standard)
    # NRAs generally cannot claim Standard Deduction.
    # Exception: India (Article 21(2))
    
    itemized_deductions = state_tax + D(data.charitable_contributions)
    
    standard_deduction = Decimal('0')
    if data.country_of_residence:
        standard_deduction = D(TaxTreaty.get_standard_deduction(data.country_of_residence, data.tax_year))
        
    final_deduction = Decimal('0')
    
    if standard_deduction > Decimal('0') and standard_deduction > itemized_deductions:
        final_deduction = standard_deduction
        # Success message already added later
    else:
        final_deduction = itemized_deductions
        if final_deduction > Decimal('0'):
            warnings.append(f"NOTE: You are claiming Itemized Deductions (${final_deduction}). You MUST file Schedule A (Form 1040-NR) with your return.")

    # 6. Taxable Income
    # Round to nearest dollar for taxable income? Form 1040 instructions say you CAN round.
    # Let's keep strict precision until final tax calc
    taxable_income = max(Decimal('0'), taxable_wages_after_treaty - final_deduction)
    
    # 6. Tax Calculation (Multi-Year Support)
    # Source: IRS Revenue Procedures for each year
    TAX_BRACKETS = {
        2025: [
            (Decimal('11925'), Decimal('0.10')),
            (Decimal('48475'), Decimal('0.12')),
            (Decimal('103350'), Decimal('0.22')),
            (Decimal('197300'), Decimal('0.24')),
            (Decimal('250525'), Decimal('0.32')),
            (Decimal('626350'), Decimal('0.35')),
            (Decimal('Infinity'), Decimal('0.37'))
        ],
        2024: [
            (Decimal('11600'), Decimal('0.10')),
            (Decimal('47150'), Decimal('0.12')),
            (Decimal('100525'), Decimal('0.22')),
            (Decimal('191950'), Decimal('0.24')),
            (Decimal('243725'), Decimal('0.32')),
            (Decimal('609350'), Decimal('0.35')),
            (Decimal('Infinity'), Decimal('0.37'))
        ],
        2023: [
            (Decimal('11000'), Decimal('0.10')),
            (Decimal('44725'), Decimal('0.12')),
            (Decimal('95375'), Decimal('0.22')),
            (Decimal('182100'), Decimal('0.24')),
            (Decimal('231250'), Decimal('0.32')),
            (Decimal('578125'), Decimal('0.35')),
            (Decimal('Infinity'), Decimal('0.37'))
        ]
    }

    tax = Decimal('0')
    income = taxable_income  # Keep standard for calculation logic
    
    # Get brackets for the specific year, default to 2025
    brackets = TAX_BRACKETS.get(data.tax_year, TAX_BRACKETS[2025])
    
    previous_limit = Decimal('0')
    
    for limit, rate in brackets:
        if income > previous_limit:
            if str(limit) == 'Infinity':
                taxable_amount = income - previous_limit
            else:
                taxable_amount = min(income, limit) - previous_limit
            
            tax += taxable_amount * rate
            previous_limit = limit
        else:
            break
        
    # 7. NEC Tax Calculation (Schedule NEC)
    # Dividends
    dividend_rate = Decimal('0.30') # Default 30%
    if data.country_of_residence:
        dividend_rate = D(TaxTreaty.get_dividend_rate(data.country_of_residence)) / Decimal('100.0')
        
    dividend_tax = D(data.dividend_income) * dividend_rate
    
    # Interest (Default 30% for now, as portfolio interest exemption requires more complex validation)
    interest_tax = D(data.interest_income) * Decimal('0.30')
    
    # Rounding: IRS Requires rounding to nearest dollar using ROUND_HALF_UP (implied by "50 cents or more")
    # Actually, we should round the final lines.
    # Let's use currency precision (2 decimals) for display, but user can round on form.
    # Python rounding: round() is Bankers rounding (nearest even). We need standard rounding.
    def exact_round(val):
        return val.quantize(Decimal('1'), rounding=ROUND_HALF_UP) # Nearest Dollar
        
    def currency_round(val):
        return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) # Cents

    # Capital Gains (NEC)
    # Taxable at 30% ONLY if present >= 183 days in current tax year (even if Exempt Individual)
    # Source: IRS Pub 519, Chapter 4
    capital_gains_tax = Decimal('0')
    days_present = D(data.days_present_2025)
    if days_present >= 183:
        # Note: Losses can typically offset gains if both are 'US source'. Simplified here.
        net_gains = max(Decimal('0'), D(data.capital_gains) - D(data.capital_losses))
        capital_gains_tax = net_gains * Decimal('0.30')
        if capital_gains_tax > Decimal('0'):
            warnings.append(f"NOTE: You were present for {days_present} days (>= 183). Your Capital Gains are subject to flat 30% tax (Schedule NEC).")

    nec_tax = currency_round(dividend_tax + interest_tax + capital_gains_tax)
    wage_tax = currency_round(tax)
    
    # Total Tax - Round to Nearest Dollar as per IRS Requirement
    total_tax_cents = wage_tax + nec_tax 
    total_tax = exact_round(total_tax_cents)
    
    # Refunds/Owe
    federal_withheld = D(data.federal_tax_withheld)
    
    # IRS output should be rounded to dollar? Usually strict forms do.
    refund = max(Decimal('0'), federal_withheld - total_tax)
    owe = max(Decimal('0'), total_tax - federal_withheld)

    if treaty_exemption > Decimal('0'):
        warnings.append(f"SUCCESS: Applied ${treaty_exemption} income exemption based on {data.country_of_residence} tax treaty.")
    if standard_deduction > Decimal('0') and final_deduction == standard_deduction:
        warnings.append(f"SUCCESS: Applied Standard Deduction of ${standard_deduction} based on {data.country_of_residence} tax treaty (Article {TaxTreaty.get_treaty_article(data.country_of_residence, 'standard_deduction')}).")
    if nec_tax > Decimal('0'):
        warnings.append(f"NOTE: You have ${nec_tax} in tax on passive income (Schedule NEC). This is added to your total tax liability.")

    return {
        "taxable_wages": float(wages),
        "treaty_exemption": float(treaty_exemption),
        "itemized_deductions": float(final_deduction),
        "taxable_income": float(taxable_income),
        "total_tax": float(total_tax), # Now integer-like float (x.0)
        "wage_tax": float(wage_tax),
        "nec_tax": float(nec_tax),
        "refund": float(refund),
        "owe": float(owe),
        "warnings": warnings,
        "dividend_rate": int(dividend_rate * 100)
    }
