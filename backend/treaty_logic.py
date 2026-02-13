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
                "amount_2025": 15750  # Official IRS 2025 Standard Deduction for Single Filers
            },
            "income_exemption": {
                "amount": 0,  # No specific dollar exemption on wages, just standard deduction
                "note": "Article 21(2) grants same exemptions/deductions as US residents"
            }
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
            }
        }
    }

    @staticmethod
    def get_standard_deduction(country: str, year: int = 2025) -> int:
        country_data = TaxTreaty.TREATIES.get(country)
        if country_data and country_data.get("standard_deduction", {}).get("allowed"):
            return country_data["standard_deduction"]["amount_2025"]
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
