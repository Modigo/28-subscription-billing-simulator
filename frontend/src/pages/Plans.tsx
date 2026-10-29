import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";
import { plansApi } from "../services/api";
import { Plan } from "../types";
import { formatCurrency } from "../utils/format";

export default function Plans() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Plan | null>(null);
  const [retiring, setRetiring] = useState<Plan | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    currency: "NGN",
    billing_interval: "monthly",
    trial_days: 0,
  });

  async function load() {
    try {
      const data = await plansApi.list();
      setPlans(data);
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
      if (editing) {
        await plansApi.update(editing.id, form);
      } else {
        await plansApi.create(form);
      }
      resetForm();
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  function resetForm() {
    setForm({ name: "", description: "", price: "", currency: "NGN", billing_interval: "monthly", trial_days: 0 });
    setShowForm(false);
    setEditing(null);
  }

  function startEdit(plan: Plan) {
    setEditing(plan);
    setForm({
      name: plan.name,
      description: plan.description || "",
      price: plan.price,
      currency: plan.currency,
      billing_interval: plan.billing_interval,
      trial_days: plan.trial_days,
    });
    setShowForm(true);
  }

  async function handleRetire(plan: Plan) {
    try {
      await plansApi.retire(plan.id);
      setRetiring(null);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  if (loading) return <Layout title="Plans"><p className="text-gray-500">Loading...</p></Layout>;

  return (
    <Layout title="Plans">
      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded">{error}</div>}

      <div className="mb-4">
        <button
          onClick={() => { resetForm(); setShowForm(true); }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          + New Plan
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">{editing ? "Edit Plan" : "Create Plan"}</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              required
              placeholder="Plan name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="border rounded px-3 py-2"
            />
            <input
              placeholder="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="border rounded px-3 py-2"
            />
            <input
              required
              type="number"
              step="0.01"
              min="0.01"
              placeholder="Price"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
              className="border rounded px-3 py-2"
            />
            <select
              value={form.currency}
              onChange={(e) => setForm({ ...form, currency: e.target.value })}
              className="border rounded px-3 py-2"
            >
              <option value="NGN">NGN</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
            </select>
            <select
              value={form.billing_interval}
              onChange={(e) => setForm({ ...form, billing_interval: e.target.value })}
              className="border rounded px-3 py-2"
            >
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
            <input
              type="number"
              min="0"
              placeholder="Trial days"
              value={form.trial_days}
              onChange={(e) => setForm({ ...form, trial_days: parseInt(e.target.value) || 0 })}
              className="border rounded px-3 py-2"
            />
            <div className="flex gap-2 md:col-span-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md">
                {editing ? "Update" : "Create"}
              </button>
              <button type="button" onClick={resetForm} className="px-4 py-2 bg-gray-200 rounded-md">
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
              <th className="text-left px-6 py-3">Price</th>
              <th className="text-left px-6 py-3">Interval</th>
              <th className="text-left px-6 py-3">Trial</th>
              <th className="text-left px-6 py-3">Status</th>
              <th className="text-left px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {plans.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-400">No plans yet</td></tr>
            ) : (
              plans.map((plan) => (
                <tr key={plan.id} className="border-t">
                  <td className="px-6 py-3">
                    <div className="font-medium">{plan.name}</div>
                    {plan.description && <div className="text-gray-500 text-xs">{plan.description}</div>}
                  </td>
                  <td className="px-6 py-3">{formatCurrency(plan.price, plan.currency)}</td>
                  <td className="px-6 py-3 capitalize">{plan.billing_interval}</td>
                  <td className="px-6 py-3">{plan.trial_days} days</td>
                  <td className="px-6 py-3"><StatusBadge status={plan.status} /></td>
                  <td className="px-6 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => startEdit(plan)} className="text-blue-600 hover:underline text-xs">
                        Edit
                      </button>
                      {plan.status === "active" && (
                        <button
                          onClick={() => setRetiring(plan)}
                          className="text-red-600 hover:underline text-xs"
                        >
                          Retire
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {retiring && (
        <ConfirmDialog
          title="Retire Plan"
          message={`Retire "${retiring.name}"? Existing subscriptions will remain, but new ones cannot be created.`}
          onConfirm={() => handleRetire(retiring)}
          onCancel={() => setRetiring(null)}
          confirmText="Retire"
          variant="danger"
        />
      )}
    </Layout>
  );
}
