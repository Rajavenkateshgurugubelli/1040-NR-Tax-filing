# US-India Tax Wizard - Enterprise Deployment Instructions

## Overview
This application is a specialized tax filing assistant for Indian F1/J1 students. It processes sensitive financial data to generate IRS-compliant tax forms (1040-NR, Schedule NEC, Form 8843) filled according to the US-India Tax Treaty.

## Important: Compliance & Standards
1.  **Forms**: This application uses **Official IRS Forms** stored in `backend/forms/`.
    - `f1040nr.pdf`: Form 1040-NR (U.S. Nonresident Alien Income Tax Return)
    - `f1040nrn.pdf`: Schedule NEC (Tax on Income Not Effectively Connected With a U.S. Trade or Business)
    - `f8843.pdf`: Form 8843 (Statement for Exempt Individuals)
    - **Verification**: Always ensure these files match the latest official versions from [IRS.gov](https://www.irs.gov/).

2.  **Data Handling**:
    - **Computed Locally**: All validation and tax calculation happens on the backend server.
    - **No Retention**: The application does **not** store any user data in a database. Data is processed in-memory and discarded after the session.
    - **Validation**: Strict validation rules (Pydantic/Yup) ensure data integrity (e.g., zip codes, date ranges).

## Architecture
- **Backend**: FastAPI (Python)
    - Handles PDF manipulation (using `pypdf`).
    - Implements XFA Stripping for 1040-NR compatibility.
    - Strict Type Checking with Pydantic.
- **Frontend**: React + Vite
    - Modern, responsive UI with TailwindCSS.
    - Real-time validation.
    - Preview capability for all forms.

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
# source .venv/bin/activate

pip install -r requirements.txt
```
**Running the Server**:
```bash
python main.py
```
*Server runs on port 8000.*

### 2. Frontend Setup
```bash
cd frontend
npm install
```
**Running the Client**:
```bash
npm run dev
```
*Client runs on port 5173.*

## Usage Workflow
1.  **Context**: User enters personal details (Name, SSN, Address).
2.  **Presence**: User enters days present in the US (validated < 366).
3.  **Income**: User enters Wages (W-2) and Investments (1099).
4.  **Preview**: User can view each filled form (1040-NR, NEC, 8843) individually.
5.  **Download**: User downloads the complete package (ZIP) or individual PDFs.

## Troubleshooting
- **Empty PDF Fields**: This is caused by XFA architecture in official IRS forms. The backend automatically strips XFA data to force standard AcroForm rendering.
- **Validation Errors**: Ensure dates are in correct ranges and state codes are valid (2 letters).
