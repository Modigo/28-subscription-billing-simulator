import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";
import { subscriptionsApi, customersApi, plansApi } from "../services/api";
import { Subscription, Customer, Plan } from "../types";
import { formatDateShort } from "../utils/format";

export default function Subscriptions() {
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ customer_id: "", plan_id: "" });
  const [canceling, setCanceling] = useState<Subscription | null>(null);
  const [actionLoading, setActionLoading] = useState("");

  async function load() {
    try {
      const [subsData, custData, plansData] = await Promise.all([
        subscriptionsApi.list(),
        customersApi.list(),
        plansApi.list("active"),
      ]);
      setSubs(subsData);
      setCustomers(custData);
      setPlans(plansData);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.customer_id || !form.plan_id) return;
    try {
      await subscriptionsApi.create({
        customer_id: parseInt(form.customer_id),
        plan_id: parseInt(form.plan_id),
      });
      setForm({ customer_id: "", plan_id: "" });
      setShowForm(false);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function handleAction(action: string, sub: Subscription) {
    setActionLoading(action);
    try {
      if (action === "pause") await subscriptionsApi.pause(sub.id);
      else if (action === "resume") await subscriptionsApi.resume(sub.id);
      else if (action === "cancel") {
        await subscriptionsApi.cancel(sub.id);
        setCanceling(null);
      }
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActionLoading("");
    }
  }

  if (loading) return <Layout title="Subscriptions"><p className="text-gray-500">Loading...</p></Layout>;

  return (
    <Layout title="Subscriptions">
      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded">{error}</div>}

      <div className="mb-4">
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          + New Subscription
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Create Subscription</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select
              required
              value={form.customer_id}
              onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
              className="border rounded px-3 py-2"
            >
              <option value="">Select customer</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>{c.name} ({c.email})</option>
              ))}
            </select>
            <select
              required
              value={form.plan_id}
              onChange={(e) => setForm({ ...form, plan_id: e.target.value })}
              className="border rounded px-3 py-2"
            >
              <option value="">Select plan</option>
              {plans.map((p) => (
                <option key={p.id} value={p.id}>{p.name} - {p.currency} {p.price}/{p.billing_interval}</option>
              ))}
            </select>
            <div className="flex gap-2 md:col-span-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md">
                Subscribe
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
              <th className="text-left px-6 py-3">ID</th>
              <th className="text-left px-6 py-3">Status</th>
              <th className="text-left px-6 py-3">Plan</th>
              <th className="text-left px-6 py-3">Period</th>
              <th className="text-left px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {subs.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-400">No subscriptions yet</td></tr>
            ) : (
              subs.map((sub) => (
                <tr key={sub.id} className="border-t">
                  <td className="px-6 py-3">#{sub.id}</td>
                  <td className="px-6 py-3"><StatusBadge status={sub.status} /></td>
                  <td className="px-6 py-3">{sub.plan?.name || "—"}</td>
                  <td className="px-6 py-3 text-gray-500">
                    {formatDateShort(sub.current_period_start)} – {formatDateShort(sub.current_period_end)}
                  </td>
                  <td className="px-6 py-3">
                    <div className="flex gap-2 flex-wrap">
                      {sub.status === "active" && (
                        <button
                          onClick={() => handleAction("pause", sub)}
                          disabled={!!actionLoading}
                          className="text-orange-600 hover:underline text-xs"
                        >
                          Pause
                        </button>
                      )}
                      {sub.status === "paused" && (
                        <button
                          onClick={() => handleAction("resume", sub)}
                          disabled={!!actionLoading}
                          className="text-green-600 hover:underline text-xs"
                        >
                          Resume
                        </button>
                      )}
                      {["active", "paused", "trialing"].includes(sub.status) && (
                        <button
                          onClick={() => setCanceling(sub)}
                          className="text-red-600 hover:underline text-xs"
                        >
                          Cancel
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

      {canceling && (
        <ConfirmDialog
          title="Cancel Subscription"
          message="This will immediately cancel the subscription. Continue?"
          onConfirm={() => handleAction("cancel", canceling)}
          onCancel={() => setCanceling(null)}
          confirmText="Cancel"
          variant="danger"
        />
      )}
    </Layout>
  );
}
