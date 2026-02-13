# 🚀 TaxGenie - IRS-Compliant 1040-NR Tax Filing System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18.3+-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-43%2F43%20Passing-success.svg)](backend/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Production-Ready Tax Filing System for International Students (F-1/J-1) on OPT/CPT**  
> IRS-Grade Precision • Premium Glassmorphism UI • 5 Country Tax Treaties • Multi-Year Support

---

## 📋 Table of Contents
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Tax Forms Supported](#-tax-forms-supported)
- [Country Treaties](#-country-treaties)
- [Testing](#-testing)
- [Project Status](#-project-status)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)

---

## ✨ Features

### 🎯 Tax Calculation Engine
- **IRS-Grade Precision**: All calculations use `decimal.Decimal` for exact arithmetic
- **Substantial Presence Test (SPT)**: Automated residency determination
- **FICA Exemption Validation**: 5-year exemption tracking for F-1/J-1 students
- **Tax Treaty Benefits**: Automatic application of income exemptions and standard deductions
- **Multi-Year Support**: File for 2023, 2024, or 2025 tax years

### 📝 Form Generation
- **Form 1040-NR**: Non-Resident Alien Income Tax Return
- **Schedule NEC**: Tax on Income Not Effectively Connected with US Trade
- **Form 8843**: Statement for Exempt Individuals
- **Schedule A**: Itemized Deductions (India only)
- **PDF Merging**: Complete tax package in one file

### 🌍 Tax Treaty Support
| Country | Benefit | Article | Amount |
|---------|---------|---------|--------|
| 🇮🇳 India | Standard Deduction | 21(2) | $15,750 |
| 🇨🇳 China | Income Exemption | 20 | $5,000 |
| 🇨🇦 Canada | Income Exemption | XV | $10,000 |
| 🇰🇷 South Korea | Income Exemption | 21 | $2,000 |
| 🇯🇵 Japan | Income Exemption | 20 | $2,000 |

### 🎨 Premium UI/UX
- **Glassmorphism Design**: Modern frosted-glass aesthetic
- **Animated Backgrounds**: Dynamic mesh gradients
- **Micro-animations**: Smooth transitions and hover effects
- **Mobile Responsive**: Works on all devices
- **Dark Mode Ready**: Prepared for theme switching

### 🔒 Enterprise Security
- **JWT Authentication**: Secure token-based auth
- **BCrypt Password Hashing**: Industry-standard encryption
- **SQL Injection Defense**: SQLAlchemy ORM parameterization
- **Cross-Tenant Isolation**: User data segregation
- **Input Validation**: Pydantic schema enforcement

### 📊 Enterprise Features
- **User Management**: Registration, login, profile
- **Admin Dashboard**: User analytics and management
- **Bulk CSV Upload**: Process multiple returns
- **Email Delivery**: Automated PDF distribution
- **Data Persistence**: SQLite database with SQLAlchemy

---

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 16 or higher
- **PDFtk**: For PDF form filling ([Download](https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/))

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd resonant-opportunity
```

2. **Backend Setup**
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Create database tables
python -c "from backend.database import engine, Base; from backend.models_db import *; Base.metadata.create_all(bind=engine)"
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

### Running the Application

**Start Backend Server** (Terminal 1):
```bash
cd <project-root>
python -m uvicorn backend.main:app --reload --port 8000
```

**Start Frontend Server** (Terminal 2):
```bash
cd frontend
npm run dev
```

**Access the Application**:
- Frontend: http://localhost:5173
- Backend API Docs: http://127.0.0.1:8000/docs
- Backend Health: http://127.0.0.1:8000/health

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│  • Tax Wizard (Multi-step Form)                            │
│  • Glassmorphism UI + Animations                            │
│  • User Auth (Login/Register)                               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│  • Tax Engine (decimal.Decimal precision)                   │
│  • Treaty Logic (5 countries)                               │
│  • PDF Generation (PDFtk)                                   │
│  • JWT Auth + BCrypt                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────┐         ┌────────▼────────┐
│   SQLite DB  │         │  IRS PDF Forms  │
│   • Users    │         │  • f1040nr.pdf  │
│   • Returns  │         │  • f1040nec.pdf │
└──────────────┘         │  • f8843.pdf    │
                         └─────────────────┘
```

### Technology Stack
- **Frontend**: React 18, Vite 5, Tailwind CSS, Formik, Yup
- **Backend**: FastAPI, SQLAlchemy, Pydantic, PyPDF2, PDFtk
- **Database**: SQLite (production should use PostgreSQL)
- **Testing**: Pytest (43 tests), Playwright (E2E)
- **Auth**: JWT (jose), BCrypt (passlib)

---

## 📄 Tax Forms Supported

### Form 1040-NR
**Non-Resident Alien Income Tax Return**
- 669+ field mappings verified
- Automatic calculation of tax liability
- Refund/balance due determination

### Schedule NEC
**Tax on Income Not Effectively Connected**
- Dividends: Country-specific treaty rates (10-30%)
- Interest: Flat 30% (portfolio interest exemption requires manual validation)
- Capital Gains: 30% tax if present >= 183 days

### Form 8843
**Statement for Exempt Individuals**
- Automatic generation for F-1/J-1 students
- Days present validation
- Visa status confirmation

---

## 🧪 Testing

### Run All Tests
```bash
# Backend tests (43 total)
cd <project-root>
python -m pytest backend/ -v

# Frontend E2E tests
cd frontend
npm test
```

### Test Coverage

| Test Suite | Tests | Focus Area |
|------------|-------|------------|
| **Math Core** | 5 | Decimal precision, SPT, Rounding |
| **Personas** | 3 | Complex scenarios (Indian PhD, etc.) |
| **Security** | 3 | SQL injection, isolation, retention |
| 1040-NR Accuracy | 7 | Field mappings, calculations |
| Admin Dashboard | 2 | User management |
| API Endpoints | 5 | CRUD operations |
| Authentication | 2 | Login, registration |
| Bulk Upload | 2 | CSV processing |
| Email Delivery | 1 | SMTP integration |
| Schedule NEC | 2 | Passive income tax |
| State Tax Logic | 3 | Validation rules |
| Tax Year Logic | 3 | Multi-year support |
| Treaty Logic | 4 | Country-specific rules |

**Total**: 43/43 passing ✅

---

## 📊 Project Status

### ✅ Completed Phases (9/10)

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ✅ | Automation & Infrastructure |
| 1-2 | ✅ | Core NRA Backend |
| 3 | ✅ | Treaty Logic (5 countries) |
| 4-5 | ✅ | Frontend Wizard + IRS Compliance |
| 6 | ✅ | Additional Treaties |
| 7 | ✅ | User Experience Features |
| 8 | ✅ | Enterprise Features (DB, Auth) |
| 9 | ✅ | **Premium UI/UX Overhaul** |
| 10 | ✅ | **IRS-Grade QA Protocol** |

### 🔄 Ongoing/Future Work
- [ ] **IRS ATS Scenarios**: Requires official IRS test XML files
- [ ] Schedule OI generation (awaiting IRS PDF template)
- [ ] E-file integration (requires ERO certification)
- [ ] State tax returns
- [ ] Multi-language support

---

## 📚 API Documentation

### Key Endpoints

**Authentication**
```
POST /register          - Create new user account
POST /login            - Authenticate and get JWT token
GET  /users/me         - Get current user profile
```

**Tax Returns**
```
POST /generate-forms   - Generate 1040-NR PDF package
POST /tax-returns      - Save tax return to database
GET  /tax-returns/{id} - Retrieve saved return
```

**Admin** (requires superuser)
```
GET  /admin/users      - List all users
POST /admin/bulk-upload - Upload CSV for bulk processing
```

**Forms**
```
POST /generate-nec     - Generate Schedule NEC
POST /generate-8843    - Generate Form 8843
POST /merge-pdfs       - Merge multiple PDFs
```

Full API documentation available at: `http://127.0.0.1:8000/docs`

---

## 🎓 Use Cases

1. **University Tax Workshops**: Help international students file taxes
2. **Tax Preparation Services**: Quick 1040-NR form generation
3. **Educational Tool**: Interactive tax treaty calculator
4. **Developer Reference**: IRS form automation example

---

## ⚖️ Legal Disclaimer

**This software is for educational and informational purposes only.**

- Not a substitute for professional tax advice
- Users are responsible for verifying accuracy
- Author assumes no liability for tax filing errors
- Always consult a qualified tax professional

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Write tests for new features
- Follow existing code style
- Update documentation
- Use `decimal.Decimal` for all financial calculations

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **IRS**: For providing open-access PDF forms
- **Tax Treaty Sources**: US Treasury Department official publications
- **PDFtk**: Free PDF manipulation tool
- **FastAPI**: Modern Python web framework
- **React**: Frontend library

---

## 📞 Support

For issues and questions:
- Open an [Issue](../../issues)
- Check the [Documentation](docs/)
- Review [Test Files](backend/test_*.py) for examples

---

**Built with ❤️ for International Students**  
*Making US tax filing accessible and accurate*

---

**Version**: 1.0-RC (Release Candidate)  
**Last Updated**: February 2026
