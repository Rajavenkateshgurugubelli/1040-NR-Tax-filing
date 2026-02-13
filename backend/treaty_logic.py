from typing import Optional, Dict

class TaxTreaty:
    """
    Handles tax treaty logic for various countries.
    Currently supports: India (Article 21(2)), China (Article 20).
    """
    
    TREATIES = {
        "India": {
            "standard_deduction": {
                "allowed": True,
                "article": "21(2)",
                "amount_2025": 15000  # Official IRS 2025 Standard Deduction for Single Filers
            },
            "income_exemption": {
                "amount": 0,  # No specific dollar exemption on wages, just standard deduction
                "note": "Article 21(2) grants same exemptions/deductions as US residents"
            },
            "dividend_rate": 25 # Article 10
        },
        "China": {
            "standard_deduction": {
                "allowed": False,  # NRAs generally cannot claim standard deduction
                "amount_2025": 0
            },
            "income_exemption": {
                "amount": 5000,  # Article 20(c): $5,000 exemption for students/trainees (confirmed 2025)
                "article": "20(c)",
                "note": "Applies to income from personal services for education/training purposes"
            },
            "dividend_rate": 10 # Article 9
        },
        "Canada": {
            "standard_deduction": {
                "allowed": False,  # NRAs generally cannot claim standard deduction
                "amount_2025": 0
            },
            "income_exemption": {
                "amount": 10000,  # Article XV: Up to $10,000 for personal services
                "article": "XV",
                "note": "Students/trainees exempt on up to $10,000 from personal services; entire amount taxable if exceeds $10,000"
            },
            "dividend_rate": 15 # Article X
        },
        "South Korea": {
            "standard_deduction": {
                "allowed": False,  # NRAs generally cannot claim standard deduction
                "amount_2025": 0
            },
            "income_exemption": {
                "amount": 2000,  # Article 21: $2,000 exemption for students/trainees
                "article": "21",
                "note": "$2,000 annual exemption for students and business apprentices"
            },
            "dividend_rate": 10 # Article 12
        },
        "Japan": {
            "standard_deduction": {
                "allowed": False,  # NRAs generally cannot claim standard deduction
                "amount_2025": 0
            },
            "income_exemption": {
                "amount": 2000,  # Article 20: $2,000 exemption for students/trainees
                "article": "20",
                "note": "$2,000 annual exemption for students and business trainees"
            },
            "dividend_rate": 10 # Article 10
        }
    }

    @staticmethod
    def get_standard_deduction(country: str, year: int = 2025) -> int:
        country_data = TaxTreaty.TREATIES.get(country)
        if country_data and country_data.get("standard_deduction", {}).get("allowed"):
            # India special case: Standard Deduction allowed (Article 21(2))
            # Values based on IRS Revenue Procedures for each year
            if year == 2024:
                return 14600  # Rev. Proc. 2023-34
            elif year == 2023:
                return 13850  # Rev. Proc. 2022-38
            else:
                return 15000  # 2025 Value (Rev. Proc. 2024-40)
        return 0

    @staticmethod
    def get_income_exemption(country: str, income_type: str = "wages", year: int = 2025) -> int:
        country_data = TaxTreaty.TREATIES.get(country)
        if country_data:
             # Basic implementation for wages exemption
             return country_data.get("income_exemption", {}).get("amount", 0)
        return 0

    @staticmethod
    def get_treaty_article(country: str, benefit_type: str) -> Optional[str]:
        country_data = TaxTreaty.TREATIES.get(country)
        if country_data:
            if benefit_type == "standard_deduction":
                return country_data.get("standard_deduction", {}).get("article")
            elif benefit_type == "income_exemption":
                return country_data.get("income_exemption", {}).get("article")
        return None

    @staticmethod
    def get_dividend_rate(country: str) -> int:
        country_data = TaxTreaty.TREATIES.get(country)
        if country_data:
            return country_data.get("dividend_rate", 30) # Default to 30% if not specified
        return 30
