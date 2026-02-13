
import unittest
from main import calculate_tax, UserData

class TestStateTaxLogic(unittest.TestCase):
    def setUp(self):
        self.base_data = {
            "full_name": "Test User",
            "ssn": "000-00-0000",
            "wages": 50000,
            "federal_tax_withheld": 5000,
            "address": "123 Main St",
            "city": "City",
            "zip_code": "12345",
            # Defaults
            "visa_type": "F1",
            "country_of_residence": "India",
            "state_tax_withheld": 0,
            "charitable_contributions": 0,
            "state": ""
        }

    def test_no_tax_state_warning(self):
        """Test warning when state tax is entered for a no-tax state (e.g., TX)"""
        data = UserData(**self.base_data)
        data.state = "TX"
        data.state_tax_withheld = 100
        
        result = calculate_tax(data)
        warnings = result["warnings"]
        
        found = any("TX has NO state income tax" in w for w in warnings)
        self.assertTrue(found, "Should warn about state tax in TX")

    def test_high_tax_state_warning(self):
        """Test warning when no state tax is entered for a high-tax state (e.g., CA)"""
        data = UserData(**self.base_data)
        data.state = "CA"
        data.state_tax_withheld = 0
        
        result = calculate_tax(data)
        warnings = result["warnings"]
        
        found = any("likely owe state taxes" in w for w in warnings)
        self.assertTrue(found, "Should warn about missing state tax in CA")

    def test_schedule_a_warning(self):
        """Test warning for Schedule A requirement when itemized deductions exist"""
        data = UserData(**self.base_data)
        data.country_of_residence = "China" # No standard deduction
        data.state = "NY"
        data.state_tax_withheld = 2000
        
        result = calculate_tax(data)
        warnings = result["warnings"]
        
        found = any("MUST file Schedule A" in w for w in warnings)
        self.assertTrue(found, "Should warn about Schedule A for itemized deductions")

    def test_india_standard_deduction(self):
        """Test that India gets Standard Deduction ($15,000) instead of Itemized"""
        data = UserData(**self.base_data)
        data.country_of_residence = "India"
        data.state = "NY"
        data.state_tax_withheld = 2000 # Less than 15000
        
        result = calculate_tax(data)
        
        self.assertEqual(result["itemized_deductions"], 15000, "Should apply $15,000 Standard Deduction for India")
        self.assertFalse(any("Itemized Deductions" in w for w in result["warnings"]), "Should NOT warn about Itemized Deductions if Standard is used")

if __name__ == '__main__':
    unittest.main()
