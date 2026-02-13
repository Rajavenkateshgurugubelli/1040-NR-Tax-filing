import React, { useState } from 'react';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';


const WizardStep = ({ children }) => children;

const PreviewSection = ({ formType, values }) => {
    const [pdfUrl, setPdfUrl] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    React.useEffect(() => {
        let active = true;
        const fetchPreview = async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await fetch(`http://localhost:8000/api/preview-form/${formType}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ...values,
                        wages: parseFloat(values.wages) || 0,
                        federal_tax_withheld: parseFloat(values.federal_tax_withheld) || 0,
                        dividends: parseFloat(values.dividends) || 0,
                        stock_gains: parseFloat(values.stock_gains) || 0,
                        days_present_2025: parseInt(values.days_present_2025) || 0,
                        days_present_2024: parseInt(values.days_present_2024) || 0,
                        days_present_2023: parseInt(values.days_present_2023) || 0,
                    })
                });
                if (!res.ok) throw new Error('Failed to load preview');
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                if (active) setPdfUrl(url);
            } catch (err) {
                if (active) setError(err.message);
            } finally {
                if (active) setLoading(false);
            }
        };
        fetchPreview();
        return () => {
            active = false;
            if (pdfUrl) window.URL.revokeObjectURL(pdfUrl);
        };
    }, [formType]);

    return (
        <div className="border rounded-lg p-4 bg-gray-50">
            <div className="flex justify-between items-center mb-2">
                <h4 className="font-bold text-gray-700 uppercase">{formType} Preview</h4>
                {pdfUrl && (
                    <a
                        href={pdfUrl}
                        download={`${formType}.pdf`}
                        className="text-sm text-blue-600 hover:text-blue-800 underline"
                    >
                        Download PDF
                    </a>
                )}
            </div>
            <div className="aspect-[4/3] w-full bg-gray-200 rounded overflow-hidden border border-gray-300">
                {loading && <div className="h-full w-full flex items-center justify-center text-gray-500">Loading Preview...</div>}
                {error && <div className="h-full w-full flex items-center justify-center text-red-500">{error}</div>}
                {pdfUrl && !loading && (
                    <iframe src={pdfUrl} className="w-full h-full" title={`${formType} Preview`} />
                )}
            </div>
        </div>
    );
};

const US_STATES = [
    { value: '', label: 'Select State' },
    { value: 'AL', label: 'Alabama' },
    { value: 'AK', label: 'Alaska' },
    { value: 'AZ', label: 'Arizona' },
    { value: 'AR', label: 'Arkansas' },
    { value: 'CA', label: 'California' },
    { value: 'CO', label: 'Colorado' },
    { value: 'CT', label: 'Connecticut' },
    { value: 'DE', label: 'Delaware' },
    { value: 'DC', label: 'District of Columbia' },
    { value: 'FL', label: 'Florida' },
    { value: 'GA', label: 'Georgia' },
    { value: 'HI', label: 'Hawaii' },
    { value: 'ID', label: 'Idaho' },
    { value: 'IL', label: 'Illinois' },
    { value: 'IN', label: 'Indiana' },
    { value: 'IA', label: 'Iowa' },
    { value: 'KS', label: 'Kansas' },
    { value: 'KY', label: 'Kentucky' },
    { value: 'LA', label: 'Louisiana' },
    { value: 'ME', label: 'Maine' },
    { value: 'MD', label: 'Maryland' },
    { value: 'MA', label: 'Massachusetts' },
    { value: 'MI', label: 'Michigan' },
    { value: 'MN', label: 'Minnesota' },
    { value: 'MS', label: 'Mississippi' },
    { value: 'MO', label: 'Missouri' },
    { value: 'MT', label: 'Montana' },
    { value: 'NE', label: 'Nebraska' },
    { value: 'NV', label: 'Nevada' },
    { value: 'NH', label: 'New Hampshire' },
    { value: 'NJ', label: 'New Jersey' },
    { value: 'NM', label: 'New Mexico' },
    { value: 'NY', label: 'New York' },
    { value: 'NC', label: 'North Carolina' },
    { value: 'ND', label: 'North Dakota' },
    { value: 'OH', label: 'Ohio' },
    { value: 'OK', label: 'Oklahoma' },
    { value: 'OR', label: 'Oregon' },
    { value: 'PA', label: 'Pennsylvania' },
    { value: 'RI', label: 'Rhode Island' },
    { value: 'SC', label: 'South Carolina' },
    { value: 'SD', label: 'South Dakota' },
    { value: 'TN', label: 'Tennessee' },
    { value: 'TX', label: 'Texas' },
    { value: 'UT', label: 'Utah' },
    { value: 'VT', label: 'Vermont' },
    { value: 'VA', label: 'Virginia' },
    { value: 'WA', label: 'Washington' },
    { value: 'WV', label: 'West Virginia' },
    { value: 'WI', label: 'Wisconsin' },
    { value: 'WY', label: 'Wyoming' }
];

const TaxWizard = () => {
    const [step, setStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const initialValues = {
        full_name: '',
        ssn: '',
        address: '',
        city: '',
        state: '',
        zip_code: '',
        wages: '',
        federal_tax_withheld: '',
        dividends: '0',
        stock_gains: '0',
        days_present_2025: '',
        days_present_2024: '0',
        days_present_2023: '0',
        university: '',
        entry_date: '',
    };

    const validationSchemas = [
        // Step 0: Personal Details
        Yup.object({
            full_name: Yup.string().required('Required'),
            ssn: Yup.string().required('Required'),
            address: Yup.string().required('Required'),
            city: Yup.string().required('Required'),
            state: Yup.string().required('Required').length(2, 'Use 2-letter code'),
            zip_code: Yup.string().required('Required').matches(/^\d{5}$/, 'Must be 5 digits'),
            university: Yup.string().required('Required'),
            entry_date: Yup.date().required('Required'),
        }),
        // Step 1: Presence Test
        Yup.object({
            days_present_2025: Yup.number().required('Required').min(0, 'Cannot be negative').max(366, 'Cannot exceed 366 days'),
            days_present_2024: Yup.number().min(0).max(366),
            days_present_2023: Yup.number().min(0).max(366),
        }),
        // Step 2: Income
        Yup.object({
            wages: Yup.number().required('Required').min(0),
            federal_tax_withheld: Yup.number().required('Required').min(0),
            dividends: Yup.number().min(0),
            stock_gains: Yup.number(),
        }),
    ];

    const handleSubmit = async (values, { setSubmitting }) => {
        setLoading(true);
        setError('');

        try {
            const response = await fetch('http://localhost:8000/api/generate-tax-return', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...values,
                    wages: parseFloat(values.wages) || 0,
                    federal_tax_withheld: parseFloat(values.federal_tax_withheld) || 0,
                    dividends: parseFloat(values.dividends) || 0,
                    stock_gains: parseFloat(values.stock_gains) || 0,
                    days_present_2025: parseInt(values.days_present_2025) || 0,
                    days_present_2024: parseInt(values.days_present_2024) || 0,
                    days_present_2023: parseInt(values.days_present_2023) || 0,
                }),
            });

            if (!response.ok) throw new Error('Failed to generate tax return package.');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Tax_Return_Package_${values.tax_year || '2025'}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
            setSubmitting(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto bg-white p-8 rounded-xl shadow-lg border border-slate-100">
            <h2 className="text-2xl font-bold text-slate-800 mb-6">Tax Filing Wizard</h2>

            {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 border border-red-100">
                    {error}
                </div>
            )}

            <Formik
                initialValues={initialValues}
                validationSchema={validationSchemas[step]}
                onSubmit={handleSubmit}
            >
                {({ values, errors, touched, isSubmitting }) => (
                    <Form className="space-y-6">

                        {step === 0 && (
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-slate-700">Personal Details</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">Full Name</label>
                                        <Field name="full_name" className="w-full px-4 py-2 border rounded-lg" placeholder="John Doe" />
                                        {errors.full_name && touched.full_name && <div className="text-red-500 text-xs">{errors.full_name}</div>}
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">SSN / ITIN</label>
                                        <Field name="ssn" className="w-full px-4 py-2 border rounded-lg" placeholder="XXX-XX-XXXX" />
                                        {errors.ssn && touched.ssn && <div className="text-red-500 text-xs">{errors.ssn}</div>}
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700">Address (US)</label>
                                    <Field name="address" className="w-full px-4 py-2 border rounded-lg" placeholder="123 Main St" />
                                    {errors.address && touched.address && <div className="text-red-500 text-xs">{errors.address}</div>}
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">City</label>
                                        <Field name="city" className="w-full px-4 py-2 border rounded-lg" />
                                        {errors.city && touched.city && <div className="text-red-500 text-xs">{errors.city}</div>}
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">State</label>
                                        <Field as="select" name="state" className="w-full px-4 py-2 border rounded-lg bg-white">
                                            {US_STATES.map(s => (
                                                <option key={s.value} value={s.value}>{s.label}</option>
                                            ))}
                                        </Field>
                                        {errors.state && touched.state && <div className="text-red-500 text-xs">{errors.state}</div>}
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">Zip Code</label>
                                        <Field name="zip_code" className="w-full px-4 py-2 border rounded-lg" />
                                        {errors.zip_code && touched.zip_code && <div className="text-red-500 text-xs">{errors.zip_code}</div>}
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">University</label>
                                        <Field name="university" className="w-full px-4 py-2 border rounded-lg" />
                                        {errors.university && touched.university && <div className="text-red-500 text-xs">{errors.university}</div>}
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">Date of Entry to US</label>
                                        <Field type="date" name="entry_date" className="w-full px-4 py-2 border rounded-lg" />
                                        {errors.entry_date && touched.entry_date && <div className="text-red-500 text-xs">{errors.entry_date}</div>}
                                    </div>
                                </div>
                            </div>
                        )}

                        {step === 1 && (
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-slate-700">Presence Test (Form 8843)</h3>
                                <p className="text-sm text-slate-500">Enter the number of days you were physically present in the US for each year.</p>

                                <div>
                                    <label className="block text-sm font-medium text-slate-700">Days present in 2025</label>
                                    <Field type="number" name="days_present_2025" className="w-full px-4 py-2 border rounded-lg" />
                                    {errors.days_present_2025 && touched.days_present_2025 && <div className="text-red-500 text-xs">{errors.days_present_2025}</div>}
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700">Days present in 2024</label>
                                    <Field type="number" name="days_present_2024" className="w-full px-4 py-2 border rounded-lg" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700">Days present in 2023</label>
                                    <Field type="number" name="days_present_2023" className="w-full px-4 py-2 border rounded-lg" />
                                </div>
                            </div>
                        )}

                        {step === 2 && (
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-slate-700">Income Details (2025)</h3>

                                <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                                    <h4 className="font-medium text-blue-900 mb-2">W-2 Wages</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700">Wages (Box 1)</label>
                                            <Field type="number" name="wages" className="w-full px-4 py-2 border rounded-lg" placeholder="0.00" />
                                            {errors.wages && touched.wages && <div className="text-red-500 text-xs">{errors.wages}</div>}
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700">Federal Tax Withheld (Box 2)</label>
                                            <Field type="number" name="federal_tax_withheld" className="w-full px-4 py-2 border rounded-lg" placeholder="0.00" />
                                            {errors.federal_tax_withheld && touched.federal_tax_withheld && <div className="text-red-500 text-xs">{errors.federal_tax_withheld}</div>}
                                        </div>
                                    </div>
                                </div>

                                <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                                    <h4 className="font-medium text-green-900 mb-2">Investments (Schedule NEC)</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700">Dividends (1099-DIV)</label>
                                            <Field type="number" name="dividends" className="w-full px-4 py-2 border rounded-lg" placeholder="0.00" />
                                            <p className="text-xs text-green-700 mt-1">Taxed at 25% (Treaty)</p>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700">Net Stock Gains (1099-B)</label>
                                            <Field type="number" name="stock_gains" className="w-full px-4 py-2 border rounded-lg" placeholder="0.00" />
                                            <p className="text-xs text-green-700 mt-1">Taxed at 30% only if present {'>'} 183 days</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {step === 3 && (
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-slate-700">Review & Download</h3>
                                <p className="text-sm text-slate-500">Preview your forms below. You can download them individually or as a complete package.</p>

                                <div className="grid grid-cols-1 gap-6">
                                    {['1040nr', 'nec', '8843'].map(form => (
                                        <PreviewSection key={form} formType={form} values={values} />
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="pt-6 flex justify-between">
                            {step > 0 && (
                                <button
                                    type="button"
                                    onClick={() => setStep(step - 1)}
                                    className="px-6 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 font-medium"
                                >
                                    Back
                                </button>
                            )}

                            {step < 3 ? (
                                <button
                                    type="button"
                                    onClick={() => {
                                        // Trigger validation for current step fields before proceeding
                                        // For simplicity in this demo, we assume valid or rely on Formik's strict validation on Submit for now
                                        // Ideally we validate step fields here manually
                                        setStep(step + 1);
                                    }}
                                    className="ml-auto px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-sm"
                                >
                                    Next
                                </button>
                            ) : (
                                <button
                                    type="submit"
                                    disabled={isSubmitting || loading}
                                    className="ml-auto px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium shadow-sm flex items-center"
                                >
                                    {loading ? 'Generating...' : 'Download All as Zip'}
                                </button>
                            )}
                        </div>

                    </Form>
                )}
            </Formik>
        </div>
    );
};

export default TaxWizard;
