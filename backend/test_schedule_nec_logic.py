
import unittest
from main import calculate_tax, populate_schedule_nec, UserData

class TestScheduleNEC(unittest.TestCase):
    def setUp(self):
        self.base_data = {
            "full_name": "Test User",
            "ssn": "000-00-0000",
            "wages": 50000,
            "federal_tax_withheld": 5000,
            "address": "123 Main St",
            "city": "City",
            "state": "NY",
            "zip_code": "10001",
            "visa_type": "F1",
            "country_of_residence": "India",
            
            # Passive Income
            "dividend_income": 100.0,
            "interest_income": 0.0
        }

    def test_nec_tax_calculation_india(self):
        """Test NEC tax for India (25% dividend rate)"""
        data = UserData(**self.base_data)
        result = calculate_tax(data)
        
        # India Dividend Rate = 25%
        expected_tax = 100.0 * 0.25
        self.assertEqual(result["nec_tax"], expected_tax, f"Expected ${expected_tax} NEC tax, got ${result['nec_tax']}")
        self.assertIn("passive income", result["warnings"][-1], "Should have warning about passive income tax")

    def test_nec_tax_calculation_china(self):
        """Test NEC tax for China (10% dividend rate)"""
        data = UserData(**self.base_data)
        data.country_of_residence = "China"
        result = calculate_tax(data)
        
        # China Dividend Rate = 10%
        expected_tax = 100.0 * 0.10
        self.assertEqual(result["nec_tax"], expected_tax, f"Expected ${expected_tax} NEC tax, got ${result['nec_tax']}")

    def test_populate_schedule_nec_fields(self):
        """Test that correct fields are populated for 10% rate (China)"""
        data = UserData(**self.base_data)
        data.country_of_residence = "China" 
        
        fields = populate_schedule_nec(data)
        
        # Check if 10% column (Column A) is populated
        # 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_5[0]'
        col_a_key = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_5[0]'
        self.assertIn(col_a_key, fields)
        self.assertEqual(fields[col_a_key], "100.0")

    def test_interest_income_logic(self):
        """Test Interest Income (30% default)"""
        data = UserData(**self.base_data)
        data.dividend_income = 0
        data.interest_income = 200.0
        
        result = calculate_tax(data)
        expected_tax = 200.0 * 0.30
        self.assertEqual(result["nec_tax"], expected_tax)
        
        fields = populate_schedule_nec(data)
        # Interest Line 2a, Col C (30%)
        col_c_key = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line2a[0].f1_22[0]'
        self.assertIn(col_c_key, fields)
        self.assertEqual(fields[col_c_key], "200.0")

if __name__ == '__main__':
    unittest.main()
