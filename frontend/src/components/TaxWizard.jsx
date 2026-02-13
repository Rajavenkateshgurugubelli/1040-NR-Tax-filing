
import React, { useState, useEffect } from 'react';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';

const US_STATES = [
    { value: '', label: 'Select State' }, { value: 'AL', label: 'Alabama' }, { value: 'AK', label: 'Alaska' }, { value: 'AZ', label: 'Arizona' }, { value: 'AR', label: 'Arkansas' }, { value: 'CA', label: 'California' }, { value: 'CO', label: 'Colorado' }, { value: 'CT', label: 'Connecticut' }, { value: 'DE', label: 'Delaware' }, { value: 'FL', label: 'Florida' }, { value: 'GA', label: 'Georgia' }, { value: 'HI', label: 'Hawaii' }, { value: 'ID', label: 'Idaho' }, { value: 'IL', label: 'Illinois' }, { value: 'IN', label: 'Indiana' }, { value: 'IA', label: 'Iowa' }, { value: 'KS', label: 'Kansas' }, { value: 'KY', label: 'Kentucky' }, { value: 'LA', label: 'Louisiana' }, { value: 'ME', label: 'Maine' }, { value: 'MD', label: 'Maryland' }, { value: 'MA', label: 'Massachusetts' }, { value: 'MI', label: 'Michigan' }, { value: 'MN', label: 'Minnesota' }, { value: 'MS', label: 'Mississippi' }, { value: 'MO', label: 'Missouri' }, { value: 'MT', label: 'Montana' }, { value: 'NE', label: 'Nebraska' }, { value: 'NV', label: 'Nevada' }, { value: 'NH', label: 'New Hampshire' }, { value: 'NJ', label: 'New Jersey' }, { value: 'NM', label: 'New Mexico' }, { value: 'NY', label: 'New York' }, { value: 'NC', label: 'North Carolina' }, { value: 'ND', label: 'North Dakota' }, { value: 'OH', label: 'Ohio' }, { value: 'OK', label: 'Oklahoma' }, { value: 'OR', label: 'Oregon' }, { value: 'PA', label: 'Pennsylvania' }, { value: 'RI', label: 'Rhode Island' }, { value: 'SC', label: 'South Carolina' }, { value: 'SD', label: 'South Dakota' }, { value: 'TN', label: 'Tennessee' }, { value: 'TX', label: 'Texas' }, { value: 'UT', label: 'Utah' }, { value: 'VT', label: 'Vermont' }, { value: 'VA', label: 'Virginia' }, { value: 'WA', label: 'Washington' }, { value: 'WV', label: 'West Virginia' }, { value: 'WI', label: 'Wisconsin' }, { value: 'WY', label: 'Wyoming' }, { value: 'DC', label: 'District of Columbia' }
];

const VISA_TYPES = [
    { value: 'F1', label: 'F-1 Student' },
    { value: 'J1', label: 'J-1 Exchange Visitor' },
    { value: 'H1B', label: 'H-1B Worker' },
    { value: 'OTHER', label: 'Other' }
];

const FILING_STATUSES = [
    { value: 'Single', label: 'Single' },
    { value: 'Married Filing Separately', label: 'Married Filing Separately' },
    { value: 'Married Filing Jointly', label: 'Married Filing Jointly (Conditions Apply)' }
];

const DiagnosticsSection = ({ values }) => {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        let active = true;
        const fetchDiagnostics = async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await fetch('http://localhost:8000/api/calculate-tax', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(preparePayload(values))
                });
                if (!res.ok) throw new Error('Failed to load diagnostics');
                const data = await res.json();
                if (active) setResult(data);
            } catch (err) {
                if (active) setError(err.message);
            } finally {
                if (active) setLoading(false);
            }
        };
        // Debounce slightly to avoid too many requests
        const timeoutId = setTimeout(() => fetchDiagnostics(), 500);
        return () => { active = false; clearTimeout(timeoutId); };
    }, [values]);

    if (loading) return <div className="text-gray-500 text-sm animate-pulse">Calculating tax details...</div>;
    if (error) return <div className="text-red-500 text-sm">Error checking status: {error}</div>;
    if (!result) return null;

    return (
        <div className="mb-6 space-y-4">
            {result.warnings.length > 0 && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r">
                    <div className="flex">
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-yellow-800">Diagnostics / Warnings</h3>
                            <div className="mt-2 text-sm text-yellow-700 max-h-40 overflow-y-auto">
                                <ul className="list-disc pl-5 space-y-1">
                                    {result.warnings.map((w, i) => (
                                        <li key={i} className={w.includes("CRITICAL") ? "font-bold text-red-700" : ""}>{w}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-white p-4 rounded-lg border shadow-sm">
                <div>
                    <span className="block text-xs text-gray-500 uppercase tracking-wide">Taxable Income</span>
                    <span className="font-mono font-bold text-lg">${result.taxable_income.toFixed(2)}</span>
                </div>
                <div>
                    <span className="block text-xs text-gray-500 uppercase tracking-wide">Total Tax (Est.)</span>
                    <span className="font-mono font-bold text-lg text-slate-700">${result.total_tax.toFixed(2)}</span>
                </div>
                <div>
                    <span className="block text-xs text-gray-500 uppercase tracking-wide">Est. Refund</span>
                    <span className="font-mono font-bold text-lg text-green-600">${result.refund.toFixed(2)}</span>
                </div>
                <div>
                    <span className="block text-xs text-gray-500 uppercase tracking-wide">Est. Owe</span>
                    <span className="font-mono font-bold text-lg text-red-600">${result.owe.toFixed(2)}</span>
                </div>
                {result.treaty_exemption > 0 && (
                    <div className="col-span-2 md:col-span-4 text-xs text-green-700 font-medium bg-green-50 p-2 rounded">
                        ✓ Applied Treaty Exemption: ${result.treaty_exemption.toLocaleString()}
                    </div>
                )}
            </div>
        </div>
    );
};

const preparePayload = (values) => ({
    ...values,
    // Ensure numbers are numbers
    tax_year: parseInt(values.tax_year) || 2025,
    wages: parseFloat(values.wages) || 0,
    federal_tax_withheld: parseFloat(values.federal_tax_withheld) || 0,
    social_security_tax_withheld: parseFloat(values.social_security_tax_withheld) || 0,
    medicare_tax_withheld: parseFloat(values.medicare_tax_withheld) || 0,
    state_tax_withheld: parseFloat(values.state_tax_withheld) || 0,
    dividend_income: parseFloat(values.dividend_income) || 0,
    interest_income: parseFloat(values.interest_income) || 0,
    capital_gains: parseFloat(values.capital_gains) || 0,
    scholarship_grants: parseFloat(values.scholarship_grants) || 0,
    charitable_contributions: parseFloat(values.charitable_contributions) || 0,
});


const COUNTRIES = [
    "India", "China", "Canada", "South Korea", "Japan", "Mexico", "Vietnam", "Taiwan", "Brazil", "Nepal", "Nigeria", "Bangladesh", "Other"
];

// ... (keep existing imports and constants)

// Update TaxWizard Steps
const TaxWizard = () => {
    const [previewUrl, setPreviewUrl] = useState(null);
    const [step, setStep] = useState(0);

    const handlePreview = async (values) => {
        try {
            const response = await fetch('http://localhost:8000/api/download-complete-package', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preparePayload(values)),
            });
            if (!response.ok) throw new Error('Failed to generate preview');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            setPreviewUrl(url);
        } catch (err) {
            alert("Error generating preview: " + err.message);
        }
    };
    const [isSaving, setIsSaving] = useState(false);
    const [lastSaved, setLastSaved] = useState(null);

    const initialValues = {
        // Personal
        tax_year: '2025',
        full_name: '',
        ssn: '',
        date_of_birth: '',
        phone_number: '',
        email: '',
        occupation: 'Student',

        // Address
        address: '',
        city: '',
        state: '',
        zip_code: '',

        // Foreign Address
        has_foreign_address: false,
        foreign_address: '',
        foreign_city: '',
        foreign_province: '',
        foreign_postal_code: '',
        foreign_country: '',

        // Status & Visa
        country_of_residence: '',
        filing_status: 'Single',
        visa_type: 'F1',
        entry_date: '',
        days_present_2025: '365',
        days_present_2024: '0',
        days_present_2023: '0',

        // Income
        wages: '',
        federal_tax_withheld: '',
        social_security_tax_withheld: '0',
        medicare_tax_withheld: '0',
        state_tax_withheld: '0',

        // Additional Income
        dividend_income: '0',
        interest_income: '0',
        capital_gains: '0',
        scholarship_grants: '0',

        // Deductions
        charitable_contributions: '0',

        // Banking
        routing_number: '',
        account_number: '',
        account_type: 'Checking',
        bank_name: ''
    };

    // Load from localStorage on mount
    const [formattedInitialValues, setFormattedInitialValues] = useState(initialValues);

    useEffect(() => {
        const savedData = localStorage.getItem('taxFormData');
        const savedTime = localStorage.getItem('taxFormTimestamp');
        if (savedData) {
            try {
                const parsed = JSON.parse(savedData);
                setFormattedInitialValues({ ...initialValues, ...parsed });
                setLastSaved(new Date(savedTime));
            } catch (e) {
                console.error("Failed to load saved data", e);
            }
        }
    }, []);

    const validationSchemas = [
        // Step 0: Personal
        Yup.object({
            full_name: Yup.string().required('Required'),
            ssn: Yup.string().required('Required'),
            date_of_birth: Yup.date().required('Required').typeError('Invalid date'),
            phone_number: Yup.string().required('Required'),
            email: Yup.string().email('Invalid email').required('Required'),
        }),
        // Step 1: Address & Visa
        Yup.object({
            address: Yup.string().required('Required'),
            city: Yup.string().required('Required'),
            state: Yup.string().required('Required'),
            zip_code: Yup.string().required('Required'),
            country_of_residence: Yup.string().required('Required'),
            visa_type: Yup.string().required('Required'),
            entry_date: Yup.date().required('Required'),
            days_present_2025: Yup.number().required('Required'),
        }),
        // Step 2: Income
        Yup.object({
            wages: Yup.number().required('Required').typeError('Must be a number'),
            federal_tax_withheld: Yup.number().required('Required').typeError('Must be a number'),
        }),
        // Step 3: Additional Income & Deductions (Optional mostly)
        Yup.object({
            dividend_income: Yup.number().typeError('Must be a number'),
            interest_income: Yup.number().typeError('Must be a number'),
            capital_gains: Yup.number().typeError('Must be a number'),
            charitable_contributions: Yup.number().typeError('Must be a number'),
        }),
        // Step 4: Banking & Review
        Yup.object({
            routing_number: Yup.string().matches(/^\d{9}$/, 'Must be 9 digits'),
            account_number: Yup.string().matches(/^\d+$/, 'Must be only digits'),
        })
    ];

    const handleAutoSave = (values) => {
        localStorage.setItem('taxFormData', JSON.stringify(values));
        const now = new Date();
        localStorage.setItem('taxFormTimestamp', now.toISOString());
        setLastSaved(now);
        setIsSaving(true);
        setTimeout(() => setIsSaving(false), 1000);
    };

    const handleClearData = () => {
        if (window.confirm("Are you sure? This will delete all your saved progress.")) {
            localStorage.removeItem('taxFormData');
            localStorage.removeItem('taxFormTimestamp');
            window.location.reload();
        }
    }

    const downloadPackage = async (values) => {
        try {
            const response = await fetch('http://localhost:8000/api/download-complete-package', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preparePayload(values)),
            });
            if (!response.ok) throw new Error('Failed to generate package');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Tax_Package_2025_${values.full_name.replace(/\s+/g, '_')}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            alert("Error downloading package: " + err.message);
        }
    };

    return (
        <div className="max-w-5xl mx-auto bg-white rounded-xl shadow-xl overflow-hidden my-8 border border-slate-200">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-700 to-indigo-800 p-4 md:p-6 text-white flex justify-between items-center flex-wrap gap-4">
                <div>
                    <h2 className="text-2xl font-bold">Enterprise Tax Wizard 2025</h2>
                    <p className="text-blue-200 text-sm">For International Students (F-1/J-1) & Non-Residents</p>
                </div>
                <div className="text-right flex flex-col items-end">
                    <span className="text-xs bg-blue-900 bg-opacity-50 px-3 py-1 rounded-full border border-blue-500">
                        {isSaving ? "Saving..." : lastSaved ? `Saved ${lastSaved.toLocaleTimeString()}` : "Not saved yet"}
                    </span>
                    <button onClick={handleClearData} className="text-xs text-blue-200 hover:text-white underline mt-1">Clear Data</button>
                </div>
            </div>

            <Formik
                initialValues={formattedInitialValues}
                enableReinitialize
                validationSchema={validationSchemas[step]}
                onSubmit={async (values) => { /* Submitting handled by Step 4 buttons */ }}
            >
                {({ values, errors, touched, setFieldValue }) => {
                    // Auto-save logic hooks into render for simplicity or use specific effect
                    // Using effect inside a wrapper component is better, but simple inline here:
                    React.useEffect(() => {
                        const timer = setTimeout(() => handleAutoSave(values), 2000);
                        return () => clearTimeout(timer);
                    }, [values]);

                    return (
                        <Form>
                            {/* Step Progress Bar */}
                            <div className="bg-gray-50 border-b px-4 py-3 md:px-6 md:py-4">
                                <div className="flex items-center justify-between text-sm font-medium text-gray-500">
                                    <div className={`flex items-center ${step >= 0 ? 'text-blue-600' : ''}`}>
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 border-2 ${step >= 0 ? 'border-blue-600 bg-blue-50' : 'border-gray-300'}`}>1</div>
                                        <span className="hidden sm:inline">Personal</span>
                                    </div>
                                    <div className={`w-full h-1 mx-2 bg-gray-200 rounded ${step >= 1 ? 'bg-blue-600' : ''}`}></div>

                                    <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : ''}`}>
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 border-2 ${step >= 1 ? 'border-blue-600 bg-blue-50' : 'border-gray-300'}`}>2</div>
                                        <span className="hidden sm:inline">Address/Visa</span>
                                    </div>
                                    <div className={`w-full h-1 mx-2 bg-gray-200 rounded ${step >= 2 ? 'bg-blue-600' : ''}`}></div>

                                    <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : ''}`}>
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 border-2 ${step >= 2 ? 'border-blue-600 bg-blue-50' : 'border-gray-300'}`}>3</div>
                                        <span className="hidden sm:inline">Income</span>
                                    </div>
                                    <div className={`w-full h-1 mx-2 bg-gray-200 rounded ${step >= 3 ? 'bg-blue-600' : ''}`}></div>

                                    <div className={`flex items-center ${step >= 3 ? 'text-blue-600' : ''}`}>
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 border-2 ${step >= 3 ? 'border-blue-600 bg-blue-50' : 'border-gray-300'}`}>4</div>
                                        <span className="hidden sm:inline">Extra</span>
                                    </div>
                                    <div className={`w-full h-1 mx-2 bg-gray-200 rounded ${step >= 4 ? 'bg-blue-600' : ''}`}></div>

                                    <div className={`flex items-center ${step >= 4 ? 'text-blue-600' : ''}`}>
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 border-2 ${step >= 4 ? 'border-blue-600 bg-blue-50' : 'border-gray-300'}`}>5</div>
                                        <span className="hidden sm:inline">Review</span>
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 md:p-8 min-h-[400px]">
                                {/* Step 1: Personal Info */}
                                {step === 0 && (
                                    <div className="space-y-6 animate-fadeIn">
                                        <h3 className="text-xl font-bold text-gray-800 border-b pb-2">Personal Information</h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Tax Year</label>
                                                <Field as="select" name="tax_year" className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500">
                                                    <option value="2025">2025 (File in 2026)</option>
                                                    <option value="2024">2024 (Past Due)</option>
                                                    <option value="2023">2023 (Past Due)</option>
                                                </Field>
                                                <p className="text-xs text-gray-500 mt-1">Select the year you are filing for.</p>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Full Name (as on Passport)</label>
                                                <Field name="full_name" className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500" placeholder="John Doe" />
                                                <ErrorMessage name="full_name" component="div" className="text-red-500 text-xs mt-1" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">SSN or ITIN</label>
                                                <Field name="ssn" className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500" placeholder="000-00-0000" />
                                                <ErrorMessage name="ssn" component="div" className="text-red-500 text-xs mt-1" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Date of Birth</label>
                                                <Field name="date_of_birth" type="date" className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500" />
                                                <ErrorMessage name="date_of_birth" component="div" className="text-red-500 text-xs mt-1" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Occupation</label>
                                                <Field name="occupation" className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Phone Number</label>
                                                <Field name="phone_number" className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500" placeholder="+1 (555) 000-0000" />
                                                <ErrorMessage name="phone_number" component="div" className="text-red-500 text-xs mt-1" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Email Address</label>
                                                <Field name="email" type="email" className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500" placeholder="john@university.edu" />
                                                <ErrorMessage name="email" component="div" className="text-red-500 text-xs mt-1" />
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Step 2: Address & Visa */}
                                {step === 1 && (
                                    <div className="space-y-6 animate-fadeIn">
                                        <h3 className="text-xl font-bold text-gray-800 border-b pb-2">Address & Immigration Status</h3>

                                        <div className="bg-blue-50 p-4 rounded border border-blue-100">
                                            <h4 className="font-semibold text-blue-800 mb-3">U.S. Mailing Address</h4>
                                            <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                                                <div className="md:col-span-6">
                                                    <label className="block text-xs font-bold text-gray-500 uppercase">Street Address</label>
                                                    <Field name="address" className="w-full p-2 border rounded" placeholder="123 University Ave, Apt 4B" />
                                                    <ErrorMessage name="address" component="div" className="text-red-500 text-xs mt-1" />
                                                </div>
                                                <div className="md:col-span-3">
                                                    <label className="block text-xs font-bold text-gray-500 uppercase">City</label>
                                                    <Field name="city" className="w-full p-2 border rounded" />
                                                    <ErrorMessage name="city" component="div" className="text-red-500 text-xs mt-1" />
                                                </div>
                                                <div className="md:col-span-2">
                                                    <label className="block text-xs font-bold text-gray-500 uppercase">State</label>
                                                    <Field as="select" name="state" className="w-full p-2 border rounded">
                                                        {US_STATES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                                                    </Field>
                                                    <ErrorMessage name="state" component="div" className="text-red-500 text-xs mt-1" />
                                                </div>
                                                <div className="md:col-span-1">
                                                    <label className="block text-xs font-bold text-gray-500 uppercase">Zip</label>
                                                    <Field name="zip_code" className="w-full p-2 border rounded" />
                                                    <ErrorMessage name="zip_code" component="div" className="text-red-500 text-xs mt-1" />
                                                </div>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Country of Citizenship</label>
                                                <Field as="select" name="country_of_residence" className="w-full p-2 border rounded">
                                                    <option value="">Select Country</option>
                                                    {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                                                </Field>
                                                <p className="text-xs text-gray-500 mt-1">Used for Treaty Benefits</p>
                                                <ErrorMessage name="country_of_residence" component="div" className="text-red-500 text-xs mt-1" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Visa Type</label>
                                                <Field as="select" name="visa_type" className="w-full p-2 border rounded">
                                                    {VISA_TYPES.map(v => <option key={v.value} value={v.value}>{v.label}</option>)}
                                                </Field>
                                                <ErrorMessage name="visa_type" component="div" className="text-red-500 text-xs mt-1" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Date of First U.S. Entry</label>
                                                <Field name="entry_date" type="date" className="w-full p-2 border rounded" />
                                                <ErrorMessage name="entry_date" component="div" className="text-red-500 text-xs mt-1" />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-semibold text-gray-700 mb-1">Filing Status</label>
                                                <Field as="select" name="filing_status" className="w-full p-2 border rounded">
                                                    {FILING_STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                                                </Field>
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="font-semibold text-gray-700 mb-2">Days Present in U.S. (for Substantial Presence Test)</h4>
                                            <div className="grid grid-cols-3 gap-4">
                                                <div><label className="text-xs text-gray-500 block">2025</label><Field type="number" name="days_present_2025" className="w-full p-2 border rounded" /></div>
                                                <div><label className="text-xs text-gray-500 block">2024</label><Field type="number" name="days_present_2024" className="w-full p-2 border rounded" /></div>
                                                <div><label className="text-xs text-gray-500 block">2023</label><Field type="number" name="days_present_2023" className="w-full p-2 border rounded" /></div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Step 3: Income */}
                                {step === 2 && (
                                    <div className="space-y-6 animate-fadeIn">
                                        <h3 className="text-xl font-bold text-gray-800 border-b pb-2">Income Information (W-2)</h3>
                                        <p className="text-sm text-gray-600">Enter information exactly as it appears on your Form W-2.</p>

                                        <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                <div>
                                                    <label className="block text-sm font-bold text-gray-800 mb-1">Box 1: Wages, tips, other compensation</label>
                                                    <div className="relative">
                                                        <span className="absolute left-3 top-2 text-gray-500">$</span>
                                                        <Field name="wages" type="number" className="w-full pl-7 p-2 border border-gray-300 rounded font-mono text-lg" placeholder="0.00" />
                                                    </div>
                                                    <ErrorMessage name="wages" component="div" className="text-red-500 text-xs mt-1" />
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-bold text-gray-800 mb-1">Box 2: Federal income tax withheld</label>
                                                    <div className="relative">
                                                        <span className="absolute left-3 top-2 text-gray-500">$</span>
                                                        <Field name="federal_tax_withheld" type="number" className="w-full pl-7 p-2 border border-gray-300 rounded font-mono text-lg" placeholder="0.00" />
                                                    </div>
                                                    <ErrorMessage name="federal_tax_withheld" component="div" className="text-red-500 text-xs mt-1" />
                                                </div>
                                            </div>

                                            <div className="mt-6 pt-6 border-t border-gray-200">
                                                <h4 className="font-semibold text-blue-800 mb-3">State Tax Information</h4>
                                                {values.state === 'TX' || values.state === 'FL' || values.state === 'WA' ? (
                                                    <p className="text-sm text-blue-700 mb-4">Good news! <strong>{values.state}</strong> does not have state income tax.</p>
                                                ) : values.state ? (
                                                    <p className="text-sm text-blue-700 mb-4">
                                                        <strong>{values.state}</strong> has state income tax.
                                                        Please ensure you enter the amount from <strong>Box 17</strong> of your W-2 below.
                                                    </p>
                                                ) : (
                                                    <p className="text-sm text-blue-700 mb-4">Select your state in the Address step to see tax rules.</p>
                                                )}
                                                <div className="md:w-1/2">
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Box 17: State income tax</label>
                                                    <div className="relative">
                                                        <span className="absolute left-3 top-2 text-gray-500">$</span>
                                                        <Field name="state_tax_withheld" type="number" className="w-full pl-7 p-2 border rounded" placeholder="0.00" />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="bg-orange-50 p-6 rounded-lg border border-orange-100">
                                            <h4 className="font-bold text-orange-800 mb-2">FICA Tax Check (Social Security & Medicare)</h4>
                                            <p className="text-xs text-orange-700 mb-4">International students on F-1/J-1 visas are typically EXEMPT from these taxes for their first 5 years.</p>

                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-800 mb-1">Box 4: Social security tax withheld</label>
                                                    <div className="relative">
                                                        <span className="absolute left-3 top-2 text-gray-500">$</span>
                                                        <Field name="social_security_tax_withheld" type="number" className="w-full pl-7 p-2 border rounded" placeholder="0.00" />
                                                    </div>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-800 mb-1">Box 6: Medicare tax withheld</label>
                                                    <div className="relative">
                                                        <span className="absolute left-3 top-2 text-gray-500">$</span>
                                                        <Field name="medicare_tax_withheld" type="number" className="w-full pl-7 p-2 border rounded" placeholder="0.00" />
                                                    </div>
                                                </div>
                                            </div>
                                            {(parseFloat(values.social_security_tax_withheld) > 0 || parseFloat(values.medicare_tax_withheld) > 0) && (
                                                <div className="mt-3 p-2 bg-red-100 border border-red-200 rounded text-red-700 text-sm font-bold flex items-center">
                                                    <span className="text-xl mr-2">⚠️</span> You may verify if these taxes were incorrectly withheld. F-1 students are usually exempt.
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Step 4: Additional Income & Deductions */}
                                {step === 3 && (
                                    <div className="space-y-6 animate-fadeIn">
                                        <h3 className="text-xl font-bold text-gray-800 border-b pb-2">Additional Income & Deductions</h3>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <div className="space-y-4">
                                                <h4 className="font-semibold text-blue-800 border-b border-blue-100 pb-1">Additional Income Sources</h4>

                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Dividends (1099-DIV)</label>
                                                    <div className="relative"><span className="absolute left-3 top-2 text-gray-500">$</span><Field name="dividend_income" type="number" className="w-full pl-7 p-2 border rounded" /></div>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Interest Income (1099-INT)</label>
                                                    <div className="relative"><span className="absolute left-3 top-2 text-gray-500">$</span><Field name="interest_income" type="number" className="w-full pl-7 p-2 border rounded" /></div>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Capital Gains (1099-B)</label>
                                                    <div className="relative"><span className="absolute left-3 top-2 text-gray-500">$</span><Field name="capital_gains" type="number" className="w-full pl-7 p-2 border rounded" /></div>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Taxable Scholarship/Grants</label>
                                                    <div className="relative"><span className="absolute left-3 top-2 text-gray-500">$</span><Field name="scholarship_grants" type="number" className="w-full pl-7 p-2 border rounded" /></div>
                                                </div>
                                            </div>

                                            <div className="space-y-4">
                                                <h4 className="font-semibold text-green-800 border-b border-green-100 pb-1">Deductions</h4>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Charitable Contributions (Cash)</label>
                                                    <div className="relative"><span className="absolute left-3 top-2 text-gray-500">$</span><Field name="charitable_contributions" type="number" className="w-full pl-7 p-2 border rounded" /></div>
                                                    <p className="text-xs text-gray-500 mt-1">Donations to US charities only.</p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="bg-gray-50 p-4 rounded mt-4">
                                            <h4 className="font-semibold text-gray-700 mb-2">Foreign Address (If legally required)</h4>
                                            <label className="flex items-center space-x-2 text-sm text-gray-700 cursor-pointer">
                                                <Field type="checkbox" name="has_foreign_address" className="form-checkbox text-blue-600 rounded" />
                                                <span>I have a foreign address different from my US address</span>
                                            </label>

                                            {values.has_foreign_address && (
                                                <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 animate-fadeIn">
                                                    <Field name="foreign_address" placeholder="Street Address" className="w-full p-2 border rounded" />
                                                    <Field name="foreign_city" placeholder="City" className="w-full p-2 border rounded" />
                                                    <Field name="foreign_province" placeholder="Province/State" className="w-full p-2 border rounded" />
                                                    <Field name="foreign_postal_code" placeholder="Postal Code" className="w-full p-2 border rounded" />
                                                    <Field name="foreign_country" placeholder="Country" className="w-full p-2 border rounded md:col-span-2" />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Step 5: Review & Download */}
                                {step === 4 && (
                                    <div className="space-y-6 animate-fadeIn">
                                        <h3 className="text-xl font-bold text-gray-800 border-b pb-2">Review & Complete</h3>

                                        <DiagnosticsSection values={values} />

                                        <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                                            <h4 className="font-bold text-gray-800 mb-4">Direct Deposit Information</h4>
                                            <p className="text-sm text-gray-600 mb-4">Enter your bank details to receive your refund via direct deposit (faster).</p>

                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Routing Number</label>
                                                    <Field name="routing_number" className="w-full p-2 border rounded" maxLength="9" />
                                                    <ErrorMessage name="routing_number" component="div" className="text-red-500 text-xs mt-1" />
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Account Number</label>
                                                    <Field name="account_number" className="w-full p-2 border rounded" />
                                                    <ErrorMessage name="account_number" component="div" className="text-red-500 text-xs mt-1" />
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">Account Type</label>
                                                    <Field as="select" name="account_type" className="w-full p-2 border rounded">
                                                        <option value="Checking">Checking</option>
                                                        <option value="Savings">Savings</option>
                                                    </Field>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 mt-6">
                                            <h4 className="font-bold text-gray-800 mb-4">Preview Your Return</h4>

                                            {!previewUrl ? (
                                                <div className="text-center py-8">
                                                    <p className="text-gray-600 mb-4">Preview your generated forms before downloading.</p>
                                                    <button
                                                        type="button"
                                                        onClick={() => handlePreview(values)}
                                                        className="w-full sm:w-auto px-6 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition"
                                                    >
                                                        Generate Preview
                                                    </button>
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    <iframe src={previewUrl} className="w-full h-[500px] border rounded shadow-sm" title="PDF Preview"></iframe>
                                                    <div className="text-right">
                                                        <button
                                                            type="button"
                                                            onClick={() => setPreviewUrl(null)}
                                                            className="text-sm text-red-600 underline"
                                                        >
                                                            Close Preview
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        <div className="flex flex-col items-center justify-center p-8 bg-gradient-to-br from-green-50 to-emerald-100 rounded-xl border border-green-200 mt-6">
                                            <h3 className="text-2xl font-bold text-green-800 mb-2">Ready to File!</h3>
                                            <p className="text-green-700 mb-6 text-center max-w-md">
                                                Your returns have been calculated based on IRS 2025 standards.
                                                Download your complete tax package below.
                                            </p>

                                            <button
                                                type="button"
                                                onClick={() => downloadPackage(values)}
                                                className="w-full sm:w-auto justify-center bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-8 rounded-full shadow-lg transform transition hover:scale-105 flex items-center text-lg"
                                            >
                                                <span className="mr-2">📄</span> Download Complete Tax Package (PDF)
                                            </button>
                                            <p className="text-xs text-green-600 mt-3">Includes Form 1040-NR, Form 8843, and Schedule NEC (if applicable)</p>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Footer / Navigation */}
                            <div className="bg-gray-50 border-t p-6 flex flex-col-reverse sm:flex-row justify-between items-center gap-4 rounded-b-xl">
                                {step > 0 ? (
                                    <button
                                        type="button"
                                        onClick={() => setStep(step - 1)}
                                        className="w-full sm:w-auto px-6 py-2 border border-gray-300 rounded text-gray-600 hover:bg-gray-100 font-medium transition"
                                    >
                                        ← Back
                                    </button>
                                ) : (
                                    <div className="hidden sm:block"></div>
                                )}

                                {step < 4 ? (
                                    <button
                                        type="button"
                                        onClick={() => setStep(step + 1)}
                                        className="w-full sm:w-auto px-8 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium shadow transition hover:shadow-md"
                                    >
                                        Next Step →
                                    </button>
                                ) : null}
                            </div>
                        </Form>
                    );
                }}
            </Formik>
        </div>
    );
};

export default TaxWizard;
