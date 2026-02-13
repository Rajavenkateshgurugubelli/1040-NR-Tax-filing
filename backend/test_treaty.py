import unittest
from treaty_logic import TaxTreaty
from main import UserData, calculate_tax

class TestTaxTreaty(unittest.TestCase):
    def test_india_benefits(self):
        # Article 21(2) Standard Deduction
        std_deduction = TaxTreaty.get_standard_deduction("India")
        self.assertEqual(std_deduction, 14600)
        
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

    def test_calculate_tax_india(self):
        data = UserData(
            full_name="Raj India", ssn="123", address="Main St", city="NYC", state="NY", zip_code="10001",
            country_of_residence="India", visa_type="F1", entry_date="2021-08-01",
            days_present_2025=365,
            wages=50000.0, federal_tax_withheld=5000.0, state_tax_withheld=2000.0
        )
        result = calculate_tax(data)
        
        # Should have Standard Deduction of 14600
        self.assertEqual(result["itemized_deductions"], 14600)
        # Taxable Income = 50000 - 14600 = 35400
        self.assertEqual(result["taxable_income"], 35400)
        
        # Tax Check (approx):
        # 11600 * 0.10 = 1160
        # (35400 - 11600) = 23800 * 0.12 = 2856
        # Total = 4016
        self.assertAlmostEqual(result["total_tax"], 4016.0, delta=1.0)

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
        
        # Taxable Wages = 45000
        # Deduction? China NO standard deduction.
        # Itemized = State Tax (2000).
        self.assertEqual(result["itemized_deductions"], 2000)
        
        # Taxable Income = 45000 - 2000 = 43000
        self.assertEqual(result["taxable_income"], 43000)
        
        # Tax Check:
        # 11600 * 0.10 = 1160
        # (43000 - 11600) = 31400 * 0.12 = 3768
        # Total = 4928
        self.assertAlmostEqual(result["total_tax"], 4928.0, delta=1.0)

if __name__ == '__main__':
    unittest.main()
