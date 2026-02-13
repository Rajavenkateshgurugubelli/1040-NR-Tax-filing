import unittest
from backend.pdf_engine import populate_schedule_nec, generate_pdf_bytes
from backend.models import UserData
from backend.treaty_logic import TaxTreaty
import asyncio

class TestScheduleNEC(unittest.TestCase):
    def get_valid_data(self, **kwargs):
        data = {
            "full_name": "Test User",
            "ssn": "000-00-0000",
            "address": "123 Main St",
            "city": "City",
            "state": "NY",
            "zip_code": "10001",
            "wages": 10000.0,
            "federal_tax_withheld": 1000.0,
            "visa_type": "F1",
            "entry_date": "2021-08-01",
            "days_present_2025": 365,
            # Defaults that can be overridden
            "country_of_residence": "China",
            "dividend_income": 0.0
        }
        data.update(kwargs)
        return UserData(**data)

    def test_populate_schedule_nec_china(self):
        # China: 10% Dividend Rate
        data = self.get_valid_data(
            country_of_residence="China",
            dividend_income=1000.0
        )
        fields = populate_schedule_nec(data)
        
        # Expect 10% column (Col A)
        col_field = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_5[0]'
        self.assertIn(col_field, fields)
        self.assertEqual(fields[col_field], "1000.0")
        
        # Expect Total
        total_field = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_9[0]'
        self.assertEqual(fields[total_field], "1000.0")

    def test_populate_schedule_nec_canada(self):
        # Canada: 15% Dividend Rate
        data = self.get_valid_data(
            country_of_residence="Canada",
            dividend_income=2000.0
        )
        fields = populate_schedule_nec(data)
        
        # Expect 15% column (Col B)
        col_field = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_6[0]'
        self.assertIn(col_field, fields)
        self.assertEqual(fields[col_field], "2000.0")

    def test_populate_schedule_nec_india(self):
        # India: 25% Dividend Rate
        data = self.get_valid_data(
            country_of_residence="India",
            dividend_income=3000.0
        )
        fields = populate_schedule_nec(data)
        
        # Expect Other column (Col D)
        col_field = 'form1040-NR[0].Page1[0].Table_NatureOfIncome[0].Line1a[0].f1_8[0]'
        self.assertIn(col_field, fields)
        self.assertEqual(fields[col_field], "3000.0")

    def test_generate_nec_pdf(self):
        # Async test wrapper
        data = self.get_valid_data(
            country_of_residence="China",
            dividend_income=100.0
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pdf_bytes = loop.run_until_complete(generate_pdf_bytes("nec", data))
        loop.close()
        
        # Verify we got bytes back (starts with %PDF)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

if __name__ == '__main__':
    unittest.main()
