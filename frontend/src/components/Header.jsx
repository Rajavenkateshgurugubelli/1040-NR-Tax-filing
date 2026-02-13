import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Header = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <header className="bg-white border-b border-slate-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <Link to="/" className="flex items-center space-x-3">
                    <div className="bg-blue-600 w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xl">
                        T
                    </div>
                    <span className="text-xl font-bold text-slate-900 tracking-tight">TaxTreatyGeneric</span>
                </Link>
                <div className="flex items-center space-x-4">
                    {user ? (
                        <>
                            <span className="text-sm text-slate-600">Welcome, {user.full_name || user.email}</span>
                            {user.is_superuser && (
                                <Link to="/admin" className="text-sm font-medium text-purple-600 hover:text-purple-800">
                                    Admin Dashboard
                                </Link>
                            )}
                            <button
                                onClick={handleLogout}
                                className="text-sm font-medium text-slate-500 hover:text-slate-900"
                            >
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="text-sm font-medium text-slate-500 hover:text-slate-900">Login</Link>
                            <Link to="/register" className="text-sm font-medium bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Sign Up</Link>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
};

export default Header;
