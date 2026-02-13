import sys
import os

# Ensure backend package can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.treaty_logic import TaxTreaty
from backend.tax_engine import calculate_tax
from backend.models import UserData

def verify_compliance():
    print("=" * 60)
    print("      2025 IRS COMPLIANCE VERIFICATION CHECK")
    print("=" * 60)
    
    # 1. Verify Standard Deduction (Rev. Proc. 2024-40)
    std_deduction = TaxTreaty.get_standard_deduction("India")
    expected_std_deduction = 15000
    print(f"\n[1] STANDARD DEDUCTION (Single, 2025)")
    print(f"    Expected (IRS): ${expected_std_deduction:,}")
    print(f"    Actual (Code):  ${std_deduction:,}")
    if std_deduction == expected_std_deduction:
        print("    STATUS: [PASSED] OK")
    else:
        print("    STATUS: [FAILED] ERROR")

    # 2. Verify Tax Brackets (Rev. Proc. 2024-40)
    # Test Point 1: Top of 10% bracket ($11,925)
    # Tax should be $1,192.50
    data_10 = UserData(
        full_name="Test 10%", ssn="000", address="X", city="Y", state="TX", zip_code="00000",
        wages=11925, federal_tax_withheld=0
    )
    res_10 = calculate_tax(data_10)
    tax_10 = res_10["wage_tax"]
    
    print(f"\n[2] TAX BRACKET TEST: 10% Limit ($11,925)")
    print(f"    Expected Tax:   $1,192.50")
    print(f"    Actual Tax:     ${tax_10:,.2f}")
    if tax_10 == 1192.50:
        print("    STATUS: [PASSED] OK")
    else:
        print("    STATUS: [FAILED] ERROR")

    # Test Point 2: Top of 12% bracket ($48,475)
    # Tax = 10% on 11,925 + 12% on (48,475 - 11,925 = 36,550)
    # 1192.50 + 4386.00 = 5578.50
    data_12 = UserData(
         full_name="Test 12%", ssn="000", address="X", city="Y", state="TX", zip_code="00000",
        wages=48475, federal_tax_withheld=0
    )
    res_12 = calculate_tax(data_12)
    tax_12 = res_12["wage_tax"]
    
    print(f"\n[3] TAX BRACKET TEST: 12% Limit ($48,475)")
    print(f"    Expected Tax:   $5,578.50")
    print(f"    Actual Tax:     ${tax_12:,.2f}")
    if tax_12 == 5578.50:
        print("    STATUS: [PASSED] OK")
    else:
        print("    STATUS: [FAILED] ERROR")

    # 3. Verify Treaty Exemption (China)
    china_exemption = TaxTreaty.get_income_exemption("China")
    print(f"\n[4] TREATY EXEMPTION (China Article 20(c))")
    print(f"    Expected:       $5,000")
    print(f"    Actual:         ${china_exemption:,}")
    if china_exemption == 5000:
        print("    STATUS: [PASSED] OK")
    else:
        print("    STATUS: [FAILED] ERROR")
        
    print("\n" + "=" * 60)
    print("ALL COMPLIANCE CHECKS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    verify_compliance()
