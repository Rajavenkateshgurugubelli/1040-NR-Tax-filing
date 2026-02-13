import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import TaxWizard from './components/TaxWizard';
import Login from './components/Login';
import Register from './components/Register';
import AdminDashboard from './components/AdminDashboard';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Routes>
          <Route path="/" element={
            <>
              <div className="text-center mb-12">
                <h1 className="text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">
                  US Tax Return Generator <span className="text-blue-600">for International Students</span>
                </h1>
                <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                  Complete Step-by-Step Wizard to generate your Form 1040-NR, Schedule NEC, and Form 8843.
                  Claim Treaty Benefits for Standard Deduction and Dividends.
                </p>
              </div>
              <TaxWizard />
            </>
          } />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>

        <div className="mt-16 text-center text-sm text-slate-500">
          <p>
            Disclaimer: This tool calculates taxes based on 2025 rules for F1/J1 students.
            <br />Verify all generated forms before mailing.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
