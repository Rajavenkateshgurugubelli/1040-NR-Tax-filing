import React, { useState } from 'react';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';

const WizardStep = ({ children }) => children;

const US_STATES = [
    { value: '', label: 'Select State' },
    { value: 'AL', label: 'Alabama' },
    { value: 'AZ', label: 'Arizona' },
    { value: 'CA', label: 'California' },
    { value: 'NY', label: 'New York' },
    { value: 'TX', label: 'Texas' },
    { value: 'WA', label: 'Washington' },
    // Simplified list for brevity, can expand later
];

const VISA_TYPES = [
    { value: 'F1', label: 'F-1 Student' },
    { value: 'J1', label: 'J-1 Exchange Visitor' },
    { value: 'H1B', label: 'H-1B Worker' },
    { value: 'OTHER', label: 'Other' }
];

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
                    body: JSON.stringify(preparePayload(values))
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
    }, [formType, values]);

    return (
        <div className="border rounded-lg p-4 bg-gray-50">
            <div className="flex justify-between items-center mb-2">
                <h4 className="font-bold text-gray-700 uppercase">{formType} Preview</h4>
                {pdfUrl && (
                    <a href={pdfUrl} download={`${formType}.pdf`} className="text-sm text-blue-600 hover:text-blue-800 underline">
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

const preparePayload = (values) => ({
    ...values,
    wages: parseFloat(values.wages) || 0,
    federal_tax_withheld: parseFloat(values.federal_tax_withheld) || 0,
    social_security_tax_withheld: parseFloat(values.social_security_tax_withheld) || 0,
    medicare_tax_withheld: parseFloat(values.medicare_tax_withheld) || 0,
    state_tax_withheld: parseFloat(values.state_tax_withheld) || 0,
    charitable_contributions: parseFloat(values.charitable_contributions) || 0,
});

const TaxWizard = () => {
    const [step, setStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const initialValues = {
        full_name: '', ssn: '', address: '', city: '', state: '', zip_code: '',
        country_of_residence: 'India',

        // Visa Info
        visa_type: 'F1',
        entry_date: '',

        // Income
        wages: '',
        federal_tax_withheld: '',
        social_security_tax_withheld: '0',
        medicare_tax_withheld: '0',
        state_tax_withheld: '0',

        // Deductions
        charitable_contributions: '0',

        // Banking
        routing_number: '',
        account_number: '',
        account_type: 'Checking'
    };

    const validationSchemas = [
        // Step 0: Personal
        Yup.object({
            full_name: Yup.string().required('Required'),
            ssn: Yup.string().required('Required'),
            visa_type: Yup.string().required('Required'),
            state: Yup.string().required('Required'),
        }),
        // Step 1: Income & Taxes
        Yup.object({
            wages: Yup.number().required('Required'),
            federal_tax_withheld: Yup.number().required('Required'),
        }),
        // Step 2: Banking
        Yup.object({
            routing_number: Yup.string().length(9, 'Must be 9 digits'),
            account_number: Yup.string(),
        })
    ];

    const handleSubmit = async (values, { setSubmitting }) => {
        setLoading(true);
        setError('');
        try {
            const response = await fetch('http://localhost:8000/api/generate-tax-return', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preparePayload(values)),
            });
            if (!response.ok) throw new Error('Failed to generate tax return.');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Tax_Return_Package.pdf'; // Assuming single PDF for now
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
        <div className="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow-lg border border-slate-100 my-10">
            <h2 className="text-3xl font-bold text-slate-800 mb-2">Enterprise Tax Wizard (OPT/CPT)</h2>
            <p className="text-slate-500 mb-8">Specialized for International Students & Non-Residents</p>

            {error && <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6">{error}</div>}

            <Formik initialValues={initialValues} validationSchema={validationSchemas[step]} onSubmit={handleSubmit}>
                {({ values, errors, touched, isSubmitting }) => (
                    <Form className="space-y-6">
                        {step === 0 && (
                            <div className="space-y-4">
                                <h3 className="text-xl font-semibold text-slate-700">Personal & Visa Details</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div><label htmlFor="full_name" className="block text-sm font-medium">Full Name</label><Field id="full_name" name="full_name" className="w-full border p-2 rounded" /></div>
                                    <div><label htmlFor="ssn" className="block text-sm font-medium">SSN/ITIN</label><Field id="ssn" name="ssn" className="w-full border p-2 rounded" /></div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label htmlFor="visa_type" className="block text-sm font-medium">Visa Type</label>
                                        <Field as="select" id="visa_type" name="visa_type" className="w-full border p-2 rounded">
                                            {VISA_TYPES.map(v => <option key={v.value} value={v.value}>{v.label}</option>)}
                                        </Field>
                                    </div>
                                    <div><label htmlFor="country_of_residence" className="block text-sm font-medium">Country of Residence</label><Field id="country_of_residence" name="country_of_residence" className="w-full border p-2 rounded" /></div>
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <Field name="address" placeholder="Address" className="col-span-3 w-full border p-2 rounded" />
                                    <Field name="city" placeholder="City" className="w-full border p-2 rounded" />
                                    <Field as="select" name="state" className="w-full border p-2 rounded">
                                        {US_STATES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                                    </Field>
                                    <Field name="zip_code" placeholder="Zip" className="w-full border p-2 rounded" />
                                </div>
                            </div>
                        )}

                        {step === 1 && (
                            <div className="space-y-4">
                                <h3 className="text-xl font-semibold text-slate-700">Income & Taxes (W-2)</h3>
                                <div className="grid grid-cols-2 gap-6">
                                    <div className="bg-blue-50 p-4 rounded border border-blue-100">
                                        <h4 className="font-bold text-blue-800 mb-2">Income</h4>
                                        <label htmlFor="wages" className="block text-sm font-medium">Wages (Box 1)</label>
                                        <Field id="wages" type="number" name="wages" className="w-full border p-2 rounded mb-2" />
                                        <label htmlFor="federal_tax_withheld" className="block text-sm font-medium">Federal Withholding (Box 2)</label>
                                        <Field id="federal_tax_withheld" type="number" name="federal_tax_withheld" className="w-full border p-2 rounded" />
                                    </div>
                                    <div className="bg-orange-50 p-4 rounded border border-orange-100">
                                        <h4 className="font-bold text-orange-800 mb-2">FICA (Check for Refunds)</h4>
                                        <label htmlFor="social_security_tax_withheld" className="block text-sm font-medium">Social Security (Box 4)</label>
                                        <Field id="social_security_tax_withheld" type="number" name="social_security_tax_withheld" className="w-full border p-2 rounded mb-2" />
                                        <label htmlFor="medicare_tax_withheld" className="block text-sm font-medium">Medicare (Box 6)</label>
                                        <Field id="medicare_tax_withheld" type="number" name="medicare_tax_withheld" className="w-full border p-2 rounded" />
                                        {(parseFloat(values.social_security_tax_withheld) > 0 || parseFloat(values.medicare_tax_withheld) > 0) && values.visa_type === 'F1' && (
                                            <p className="text-xs text-red-600 mt-2 font-bold">WARNING: F-1 students are usually exempt! You may need a refund.</p>
                                        )}
                                    </div>
                                </div>
                                <div className="bg-green-50 p-4 rounded border border-green-100">
                                    <h4 className="font-bold text-green-800 mb-2">State Taxes & Deductions</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div><label htmlFor="state_tax_withheld" className="block text-sm font-medium">State Income Tax (Box 17)</label><Field id="state_tax_withheld" type="number" name="state_tax_withheld" className="w-full border p-2 rounded" /></div>
                                        <div><label htmlFor="charitable_contributions" className="block text-sm font-medium">Charitable Contributions</label><Field id="charitable_contributions" type="number" name="charitable_contributions" className="w-full border p-2 rounded" /></div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {step === 2 && (
                            <div className="space-y-4">
                                <h3 className="text-xl font-semibold text-slate-700">Direct Deposit</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div><label htmlFor="routing_number" className="block text-sm font-medium">Routing Number</label><Field id="routing_number" name="routing_number" className="w-full border p-2 rounded" /></div>
                                    <div><label htmlFor="account_number" className="block text-sm font-medium">Account Number</label><Field id="account_number" name="account_number" className="w-full border p-2 rounded" /></div>
                                </div>
                                <h3 className="text-xl font-semibold text-slate-700 mt-6">Preview Return</h3>
                                <PreviewSection formType="1040nr" values={values} />
                            </div>
                        )}

                        <div className="pt-6 flex justify-between">
                            {step > 0 && <button type="button" onClick={() => setStep(step - 1)} className="px-6 py-2 border rounded">Back</button>}
                            {step < 2 ? (
                                <button type="button" onClick={() => setStep(step + 1)} className="ml-auto px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Next</button>
                            ) : (
                                <button type="submit" disabled={isSubmitting || loading} className="ml-auto px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700">Download Official PDF</button>
                            )}
                        </div>
                    </Form>
                )}
            </Formik>
        </div>
    );
};

export default TaxWizard;
