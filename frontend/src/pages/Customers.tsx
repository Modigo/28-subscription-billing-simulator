import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import { customersApi } from "../services/api";
import { Customer } from "../types";
import { formatDateShort } from "../utils/format";

export default function Customers() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "" });

  async function load() {
    try {
      const data = await customersApi.list();
      setCustomers(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await customersApi.create(form);
      setForm({ name: "", email: "" });
      setShowForm(false);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  if (loading) return <Layout title="Customers"><p className="text-gray-500">Loading...</p></Layout>;

  return (
    <Layout title="Customers">
      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded">{error}</div>}

      <div className="mb-4">
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          + New Customer
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Create Customer</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              required
              placeholder="Full name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="border rounded px-3 py-2"
            />
            <input
              required
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="border rounded px-3 py-2"
            />
            <div className="flex gap-2 md:col-span-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md">
                Create
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 bg-gray-200 rounded-md">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3">Name</th>
              <th className="text-left px-6 py-3">Email</th>
              <th className="text-left px-6 py-3">Subscriptions</th>
              <th className="text-left px-6 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {customers.length === 0 ? (
              <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-400">No customers yet</td></tr>
            ) : (
              customers.map((c) => (
                <tr key={c.id} className="border-t">
                  <td className="px-6 py-3 font-medium">{c.name}</td>
                  <td className="px-6 py-3 text-gray-600">{c.email}</td>
                  <td className="px-6 py-3">{c.subscriptions?.length || 0}</td>
                  <td className="px-6 py-3 text-gray-500">{formatDateShort(c.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
