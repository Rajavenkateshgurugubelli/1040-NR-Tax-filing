import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from treaty_logic import TaxTreaty
from main import UserData, calculate_tax

class TestTaxTreaty(unittest.TestCase):
    def test_india_benefits(self):
        # Article 21(2) Standard Deduction - 2025 IRS Value
        std_deduction = TaxTreaty.get_standard_deduction("India")
        self.assertEqual(std_deduction, 15750)  # Updated to 2025 standard deduction
        
        article = TaxTreaty.get_treaty_article("India", "standard_deduction")
        self.assertEqual(article, "21(2)")
        
        # Income Exemption (None for wages usually)
        exemption = TaxTreaty.get_income_exemption("India", "wages")
        self.assertEqual(exemption, 0)

    def test_china_benefits(self):
        # Article 20 Income Exemption
        exemption = TaxTreaty.get_income_exemption("China", "wages")
        self.assertEqual(exemption, 5000)
        
        article = TaxTreaty.get_treaty_article("China", "income_exemption")
        self.assertEqual(article, "20(c)")
        
        # Standard Deduction (Not allowed)
        std_deduction = TaxTreaty.get_standard_deduction("China")
        self.assertEqual(std_deduction, 0)
    
    def test_canada_benefits(self):
        # Article XV - $10,000 Income Exemption
        exemption = TaxTreaty.get_income_exemption("Canada", "wages")
        self.assertEqual(exemption, 10000)
        
        article = TaxTreaty.get_treaty_article("Canada", "income_exemption")
        self.assertEqual(article, "XV")
        
        # Standard Deduction (Not allowed)
        std_deduction = TaxTreaty.get_standard_deduction("Canada")
        self.assertEqual(std_deduction, 0)
    
    def test_south_korea_benefits(self):
        # Article 21 - $2,000 Income Exemption
        exemption = TaxTreaty.get_income_exemption("South Korea", "wages")
        self.assertEqual(exemption, 2000)
        
        article = TaxTreaty.get_treaty_article("South Korea", "income_exemption")
        self.assertEqual(article, "21")
        
        # Standard Deduction (Not allowed)
        std_deduction = TaxTreaty.get_standard_deduction("South Korea")
        self.assertEqual(std_deduction, 0)
    
    def test_japan_benefits(self):
        # Article 20 - $2,000 Income Exemption
        exemption = TaxTreaty.get_income_exemption("Japan", "wages")
        self.assertEqual(exemption, 2000)
        
        article = TaxTreaty.get_treaty_article("Japan", "income_exemption")
        self.assertEqual(article, "20")
        
        # Standard Deduction (Not allowed)
        std_deduction = TaxTreaty.get_standard_deduction("Japan")
        self.assertEqual(std_deduction, 0)

    def test_calculate_tax_india(self):
        data = UserData(
            full_name="Raj India", ssn="123", address="Main St", city="NYC", state="NY", zip_code="10001",
            country_of_residence="India", visa_type="F1", entry_date="2021-08-01",
            days_present_2025=365,
            wages=50000.0, federal_tax_withheld=5000.0, state_tax_withheld=2000.0
        )
        result = calculate_tax(data)
        
        # Should have Standard Deduction of $15,750 (2025 value)
        self.assertEqual(result["itemized_deductions"], 15750)
        # Taxable Income = 50000 - 15750 = 34250
        self.assertEqual(result["taxable_income"], 34250)
        
        # Tax Check with 2025 brackets:
        # 10% on first $11,925 = $1,192.50
        # 12% on ($34,250 - $11,925) = 12% on $22,325 = $2,679.00
        # Total = $3,871.50
        self.assertAlmostEqual(result["total_tax"], 3871.50, delta=1.0)

    def test_calculate_tax_china(self):
        data = UserData(
            full_name="Li China", ssn="456", address="Main St", city="NYC", state="NY", zip_code="10001",
            country_of_residence="China", visa_type="F1", entry_date="2021-08-01",
            days_present_2025=365,
            wages=50000.0, federal_tax_withheld=5000.0, state_tax_withheld=2000.0
        )
        result = calculate_tax(data)
        
        # Should have $5000 Exemption
        self.assertEqual(result["treaty_exemption"], 5000)
        
        # Taxable Wages = 45000 (50000 - 5000)
        # Deduction: China NO standard deduction
        # Itemized = State Tax (2000)
        self.assertEqual(result["itemized_deductions"], 2000)
        
        # Taxable Income = 45000 - 2000 = 43000
        self.assertEqual(result["taxable_income"], 43000)
        
        # Tax Check with 2025 brackets:
        # 10% on first $11,925 = $1,192.50
        # 12% on ($43,000 - $11,925) = 12% on $31,075 = $3,729.00
        # Total = $4,921.50
        self.assertAlmostEqual(result["total_tax"], 4921.50, delta=1.0)
    
    def test_calculate_tax_canada(self):
        data = UserData(
            full_name="John Canada", ssn="789", address="Main St", city="NYC", state="NY", zip_code="10001",
            country_of_residence="Canada", visa_type="F1", entry_date="2021-08-01",
            days_present_2025=365,
            wages=50000.0, federal_tax_withheld=5000.0, state_tax_withheld=2000.0
        )
        result = calculate_tax(data)
        
        # Should have $10,000 Exemption
        self.assertEqual(result["treaty_exemption"], 10000)
        
        # Taxable Wages = 40000 (50000 - 10000)
        # Deduction: Canada NO standard deduction
        # Itemized = State Tax (2000)
        self.assertEqual(result["itemized_deductions"], 2000)
        
        # Taxable Income = 40000 - 2000 = 38000
        self.assertEqual(result["taxable_income"], 38000)
        
        # Tax Check with 2025 brackets:
        # 10% on first $11,925 = $1,192.50
        # 12% on ($38,000 - $11,925) = 12% on $26,075 = $3,129.00
        # Total = $4,321.50
        self.assertAlmostEqual(result["total_tax"], 4321.50, delta=1.0)
    
    def test_calculate_tax_south_korea(self):
        data = UserData(
            full_name="Kim Korea", ssn="321", address="Main St", city="NYC", state="NY", zip_code="10001",
            country_of_residence="South Korea", visa_type="F1", entry_date="2021-08-01",
            days_present_2025=365,
            wages=50000.0, federal_tax_withheld=5000.0, state_tax_withheld=2000.0
        )
        result = calculate_tax(data)
        
        # Should have $2,000 Exemption
        self.assertEqual(result["treaty_exemption"], 2000)
        
        # Taxable Wages = 48000 (50000 - 2000)
        # Deduction: South Korea NO standard deduction
        # Itemized = State Tax (2000)
        self.assertEqual(result["itemized_deductions"], 2000)
        
        # Taxable Income = 48000 - 2000 = 46000
        self.assertEqual(result["taxable_income"], 46000)
        
        # Tax Check with 2025 brackets:
        # 10% on first $11,925 = $1,192.50
        # 12% on ($46,000 - $11,925) = 12% on $34,075 = $4,089.00
        # Total = $5,281.50
        self.assertAlmostEqual(result["total_tax"], 5281.50, delta=1.0)
    
    def test_calculate_tax_japan(self):
        data = UserData(
            full_name="Tanaka Japan", ssn="654", address="Main St", city="NYC", state="NY", zip_code="10001",
            country_of_residence="Japan", visa_type="F1", entry_date="2021-08-01",
            days_present_2025=365,
            wages=50000.0, federal_tax_withheld=5000.0, state_tax_withheld=2000.0
        )
        result = calculate_tax(data)
        
        # Should have $2,000 Exemption
        self.assertEqual(result["treaty_exemption"], 2000)
        
        # Taxable Wages = 48000 (50000 - 2000)
        # Deduction: Japan NO standard deduction
        # Itemized = State Tax (2000)
        self.assertEqual(result["itemized_deductions"], 2000)
        
        # Taxable Income = 48000 - 2000 = 46000
        self.assertEqual(result["taxable_income"], 46000)
        
        # Tax Check with 2025 brackets:
        # 10% on first $11,925 = $1,192.50
        # 12% on ($46,000 - $11,925) = 12% on $34,075 = $4,089.00
        # Total = $5,281.50
        self.assertAlmostEqual(result["total_tax"], 5281.50, delta=1.0)

if __name__ == '__main__':
    unittest.main()
