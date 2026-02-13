import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import TaxWizard from './components/TaxWizard';
import Login from './components/Login';
import Register from './components/Register';
import AdminDashboard from './components/AdminDashboard';

function App() {
  return (
    <div className="min-h-screen font-sans text-slate-800 relative">
      <div className="bg-mesh"></div>
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
        <Routes>
          <Route path="/" element={
            <>
              <div className="text-center mb-16 animate-fadeInUp">
                <span className="inline-block py-1 px-3 rounded-full bg-indigo-100/80 text-indigo-700 text-xs font-bold tracking-wider mb-4 border border-indigo-200">
                  2025 IRS COMPLIANT
                </span>
                <h1 className="text-5xl md:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-700 mb-6 tracking-tight leading-tight drop-shadow-sm">
                  US Tax Return Generator <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 animate-gradient-x">
                    for International Students
                  </span>
                </h1>
                <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
                  The easiest way to file your <b>1040-NR, Schedule NEC, and Form 8843</b>.
                  Identify treaty benefits and maximize your refund in minutes.
                </p>
              </div>

              <div className="animate-fadeInUp delay-200">
                <TaxWizard />
              </div>
            </>
          } />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>

        <div className="mt-20 text-center text-sm text-slate-500 animate-fadeInUp delay-300">
          <p className="glass-panel inline-block px-6 py-3 text-slate-600">
            🔒 Secure • 🚀 Fast • ✅ Accurate <br />
            <span className="opacity-75 text-xs mt-1 block">Based on 2025 IRS Rules for F-1/J-1 Visa Holders</span>
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
