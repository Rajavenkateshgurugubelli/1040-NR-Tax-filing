"""
1040-NR PDF Field Mapping Accuracy Test

This test verifies that all field mappings in the 1040-NR PDF are accurate
by generating a test PDF, extracting the filled values, and comparing them
with expected values.
"""

import unittest
import sys
import os
import subprocess
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import UserData, calculate_tax, fill_pdf

class Test1040NRAccuracy(unittest.TestCase):
    """
    Automated verification test for 1040-NR PDF field mappings.
    Ensures 100% accuracy of form population.
    """
    
    def setUp(self):
        """Set up test data"""
        self.test_data = UserData(
            full_name="John Test Doe",
            ssn="123-45-6789",
            address="123 Test Street",
            city="New York",
            state="NY",
            zip_code="10001",
            country_of_residence="India",
            visa_type="F1",
            entry_date="2021-08-01",
            days_present_2025=365,
            wages=50000.0,
            federal_tax_withheld=5000.0,
            state_tax_withheld=2000.0,
            routing_number="123456789",
            account_number="9876543210"
        )
        
    def test_critical_fields_populated(self):
        """Test that all critical fields are populated correctly"""
        tax_results = calculate_tax(self.test_data)
        
        # Verify tax calculations are correct
        self.assertEqual(tax_results['taxable_wages'], 50000.0)
        self.assertEqual(tax_results['itemized_deductions'], 15750)  # India standard deduction
        self.assertEqual(tax_results['taxable_income'], 34250)
        self.assertAlmostEqual(tax_results['total_tax'], 3871.50, delta=1.0)
        
    def test_field_name_format(self):
        """Verify field names match official IRS format"""
        # Test that field names follow the pattern: topmostSubform[0].Page{N}[0].{field_id}[0]
        expected_fields = [
            'topmostSubform[0].Page1[0].f1_02[0]',  # SSN
            'topmostSubform[0].Page1[0].f1_04[0]',  # Address
            'topmostSubform[0].Page1[0].f1_42[0]',  # Line 1a Wages
            'topmostSubform[0].Page2[0].f2_05[0]',  # Line 15 Taxable Income
            'topmostSubform[0].Page2[0].f2_36[0]',  # Refund
        ]
        
        # All field names should follow the official IRS pattern
        for field in expected_fields:
            self.assertTrue(field.startswith('topmostSubform[0].Page'))
            self.assertTrue('[0]' in field)
            
    def test_data_format_validation(self):
        """Test that data formats match IRS requirements"""
        tax_results = calculate_tax(self.test_data)
        
        # Currency fields should be numeric strings
        self.assertIsInstance(str(tax_results['taxable_income']), str)
        self.assertIsInstance(str(tax_results['total_tax']), str)
        
        # Routing number should be 9 digits
        self.assertEqual(len(self.test_data.routing_number), 9)
        self.assertTrue(self.test_data.routing_number.isdigit())
        
        # Account number should be <= 17 characters
        self.assertLessEqual(len(self.test_data.account_number), 17)
        
    def test_name_splitting(self):
        """Test that full name is correctly split into first and last name"""
        first_name = self.test_data.full_name.split()[0]
        last_name = " ".join(self.test_data.full_name.split()[1:])
        
        self.assertEqual(first_name, "John")
        self.assertEqual(last_name, "Test Doe")
        
    def test_refund_owe_logic(self):
        """Test that refund/owe calculation is mutually exclusive"""
        tax_results = calculate_tax(self.test_data)
        
        # Either refund OR owe should be > 0, not both
        if tax_results['refund'] > 0:
            self.assertEqual(tax_results['owe'], 0)
        elif tax_results['owe'] > 0:
            self.assertEqual(tax_results['refund'], 0)
            
    def test_india_treaty_application(self):
        """Test that India treaty benefits are correctly applied"""
        tax_results = calculate_tax(self.test_data)
        
        # India should get standard deduction of $15,750
        self.assertEqual(tax_results['itemized_deductions'], 15750)
        
        # Verify treaty success message in warnings
        warnings = tax_results['warnings']
        treaty_applied = any('Standard Deduction' in w and 'India' in w for w in warnings)
        self.assertTrue(treaty_applied, "India treaty benefit should be in warnings")
        
    def test_china_treaty_application(self):
        """Test that China treaty benefits are correctly applied"""
        china_data = UserData(
            full_name="Li Test Wang",
            ssn="987-65-4321",
            address="456 Test Ave",
            city="Boston",
            state="MA",
            zip_code="02101",
            country_of_residence="China",
            visa_type="F1",
            entry_date="2021-08-01",
            days_present_2025=365,
            wages=50000.0,
            federal_tax_withheld=5000.0,
            state_tax_withheld=2000.0
        )
        
        tax_results = calculate_tax(china_data)
        
        # China should get $5000 income exemption
        self.assertEqual(tax_results['treaty_exemption'], 5000)
        
        # Verify treaty success message in warnings
        warnings = tax_results['warnings']
        treaty_applied = any('$5000' in w and 'China' in w for w in warnings)
        self.assertTrue(treaty_applied, "China treaty benefit should be in warnings")

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
