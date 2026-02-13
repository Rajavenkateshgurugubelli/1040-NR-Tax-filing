import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const AdminDashboard = () => {
    const { user, token } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState({ user_count: 0, tax_return_count: 0 });
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user || !user.is_superuser) {
            navigate('/');
            return;
        }

        const fetchData = async () => {
            try {
                const statsRes = await fetch('http://localhost:8000/api/admin/stats', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (statsRes.ok) setStats(await statsRes.json());

                const usersRes = await fetch('http://localhost:8000/api/admin/users', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (usersRes.ok) setUsers(await usersRes.json());

            } catch (err) {
                console.error("Failed to fetch admin data", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [user, navigate, token]);

    if (loading) return <div className="p-8 text-center">Loading Admin Dashboard...</div>;

    return (
        <div className="max-w-6xl mx-auto p-6">
            <h1 className="text-3xl font-bold mb-6 text-gray-800">Admin Dashboard</h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow border border-blue-100">
                    <h3 className="text-gray-500 text-sm uppercase">Total Users</h3>
                    <p className="text-3xl font-bold text-blue-600">{stats.user_count}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow border border-green-100">
                    <h3 className="text-gray-500 text-sm uppercase">Tax Returns Started</h3>
                    <p className="text-3xl font-bold text-green-600">{stats.tax_return_count}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow border border-purple-100">
                    <h3 className="text-gray-500 text-sm uppercase">System Status</h3>
                    <p className="text-3xl font-bold text-purple-600">Active</p>
                </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Bulk Processing</h2>
                <div className="flex items-center space-x-4">
                    <input
                        type="file"
                        accept=".csv"
                        className="block w-full text-sm text-slate-500
                        file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold
                        file:bg-blue-50 file:text-blue-700
                        hover:file:bg-blue-100"
                        onChange={async (e) => {
                            const file = e.target.files[0];
                            if (!file) return;

                            const formData = new FormData();
                            formData.append('file', file);

                            try {
                                const res = await fetch('http://localhost:8000/api/admin/bulk-upload', {
                                    method: 'POST',
                                    headers: { 'Authorization': `Bearer ${token}` },
                                    body: formData
                                });

                                if (res.ok) {
                                    const blob = await res.blob();
                                    const url = window.URL.createObjectURL(blob);
                                    const a = document.createElement('a');
                                    a.href = url;
                                    a.download = `Bulk_Tax_Forms_${new Date().toISOString().slice(0, 10)}.zip`;
                                    document.body.appendChild(a);
                                    a.click();
                                    window.URL.revokeObjectURL(url);
                                    alert("Bulk processing complete! Downloading ZIP.");
                                } else {
                                    alert("Upload failed.");
                                }
                            } catch (err) {
                                console.error(err);
                                alert("Error uploading file.");
                            }
                        }}
                    />
                    <div className="text-sm text-gray-500">
                        Upload a CSV file with student data to generate tax forms in bulk.
                    </div>
                </div>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-800">User Management</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {users.map((u) => (
                                <tr key={u.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">#{u.id}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{u.full_name || "N/A"}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${u.is_superuser ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}`}>
                                            {u.is_superuser ? 'Admin' : 'User'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(u.created_at).toLocaleDateString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
