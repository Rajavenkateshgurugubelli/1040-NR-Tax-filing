import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models import UserData
from backend.tax_engine import calculate_tax

class TestTaxYearLogic(unittest.TestCase):
    def setUp(self):
        self.base_data = {
            "full_name": "Test User",
            "ssn": "000-00-0000",
            "address": "123 Main St",
            "city": "Test City",
            "state": "TX",
            "zip_code": "12345",
            "visa_type": "F1",
            "entry_date": "2021-01-01",
            "wages": 50000,
            "federal_tax_withheld": 5000
        }

    def test_india_standard_deduction_2025(self):
        """Test India standard deduction for 2025 is $15,000"""
        data = UserData(**self.base_data, country_of_residence="India", tax_year=2025)
        result = calculate_tax(data)
        self.assertEqual(result["itemized_deductions"], 15000, "Should be $15,000 for 2025")

    def test_india_standard_deduction_2024(self):
        """Test India standard deduction for 2024 is $14,600"""
        data = UserData(**self.base_data, country_of_residence="India", tax_year=2024)
        result = calculate_tax(data)
        self.assertEqual(result["itemized_deductions"], 14600, "Should be $14,600 for 2024")

    def test_india_standard_deduction_2023(self):
        """Test India standard deduction for 2023 is $13,850"""
        data = UserData(**self.base_data, country_of_residence="India", tax_year=2023)
        result = calculate_tax(data)
        self.assertEqual(result["itemized_deductions"], 13850, "Should be $13,850 for 2023")

    def test_tax_brackets_2024_vs_2025(self):
        """Test that tax amount differs between years for same income due to bracket shifts"""
        # Income $50,000
        # 2025 Tax (approx): $11,925 @ 10% + ($38,075) @ 12% = 1192.5 + 4569 = 5761.5
        # 2024 Tax (approx): $11,600 @ 10% + ($38,400) @ 12% = 1160 + 4608 = 5768
        
        # Using a country without standard deduction to isolate bracket changes
        data_2025 = UserData(**self.base_data, country_of_residence="Other", tax_year=2025)
        res_2025 = calculate_tax(data_2025)
        
        data_2024 = UserData(**self.base_data, country_of_residence="Other", tax_year=2024)
        res_2024 = calculate_tax(data_2024)
        
        self.assertNotEqual(res_2025["total_tax"], res_2024["total_tax"], "Tax should differ between years")
        # 2025 tax should be slightly lower due to inflation adjustment
        self.assertLess(res_2025["total_tax"], res_2024["total_tax"], "2025 tax should be lower than 2024 for same income")

if __name__ == "__main__":
    unittest.main()
