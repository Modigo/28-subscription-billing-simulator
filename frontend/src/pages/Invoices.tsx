import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import StatusBadge from "../components/StatusBadge";
import { invoicesApi } from "../services/api";
import { Invoice, PaymentAttempt } from "../types";
import { formatCurrency, formatDate } from "../utils/format";

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [attempts, setAttempts] = useState<PaymentAttempt[]>([]);
  const [simulating, setSimulating] = useState(false);

  async function load() {
    try {
      const data = await invoicesApi.list(statusFilter || undefined);
      setInvoices(data.items);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [statusFilter]);

  async function viewInvoice(inv: Invoice) {
    setSelectedInvoice(inv);
    try {
      const att = await invoicesApi.getAttempts(inv.id);
      setAttempts(att);
    } catch {
      setAttempts([]);
    }
  }

  async function simulatePayment(outcome: string) {
    if (!selectedInvoice) return;
    setSimulating(true);
    try {
      await invoicesApi.simulatePayment(selectedInvoice.id, outcome);
      await viewInvoice(selectedInvoice);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSimulating(false);
    }
  }

  if (loading) return <Layout title="Invoices"><p className="text-gray-500">Loading...</p></Layout>;

  return (
    <Layout title="Invoices">
      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded">{error}</div>}

      <div className="mb-4 flex gap-3 flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="paid">Paid</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3">Number</th>
              <th className="text-left px-6 py-3">Amount</th>
              <th className="text-left px-6 py-3">Status</th>
              <th className="text-left px-6 py-3">Period</th>
              <th className="text-left px-6 py-3">Attempts</th>
              <th className="text-left px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-400">No invoices yet</td></tr>
            ) : (
              invoices.map((inv) => (
                <tr key={inv.id} className="border-t">
                  <td className="px-6 py-3 font-mono text-xs">{inv.invoice_number}</td>
                  <td className="px-6 py-3">{formatCurrency(inv.amount, inv.currency)}</td>
                  <td className="px-6 py-3"><StatusBadge status={inv.status} /></td>
                  <td className="px-6 py-3 text-gray-500 text-xs">
                    {formatDate(inv.billing_period_start)}
                  </td>
                  <td className="px-6 py-3">{inv.attempt_count}</td>
                  <td className="px-6 py-3">
                    <button
                      onClick={() => viewInvoice(inv)}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Invoice Detail Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold">{selectedInvoice.invoice_number}</h3>
                <p className="text-gray-500 text-sm">
                  {formatCurrency(selectedInvoice.amount, selectedInvoice.currency)}
                </p>
              </div>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-3 text-sm mb-6">
              <div className="flex justify-between">
                <span className="text-gray-500">Status</span>
                <StatusBadge status={selectedInvoice.status} />
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Plan</span>
                <span>{selectedInvoice.plan_name || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Period</span>
                <span>{formatDate(selectedInvoice.billing_period_start)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Attempts</span>
                <span>{selectedInvoice.attempt_count}</span>
              </div>
              {selectedInvoice.next_retry_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Next Retry</span>
                  <span>{formatDate(selectedInvoice.next_retry_at)}</span>
                </div>
              )}
            </div>

            {/* Simulate Payment */}
            {selectedInvoice.status !== "paid" && (
              <div className="mb-6">
                <h4 className="font-medium mb-2">Simulate Payment</h4>
                <div className="flex gap-2">
                  <button
                    onClick={() => simulatePayment("success")}
                    disabled={simulating}
                    className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    {simulating ? "..." : "Simulate Success"}
                  </button>
                  <button
                    onClick={() => simulatePayment("failure")}
                    disabled={simulating}
                    className="px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
                  >
                    {simulating ? "..." : "Simulate Failure"}
                  </button>
                </div>
              </div>
            )}

            {/* Payment History */}
            <div>
              <h4 className="font-medium mb-2">Payment History</h4>
              {attempts.length === 0 ? (
                <p className="text-gray-400 text-sm">No attempts yet</p>
              ) : (
                <div className="space-y-2">
                  {attempts.map((att) => (
                    <div key={att.id} className="flex justify-between text-sm border-b pb-2">
                      <div>
                        <span className="font-medium">Attempt #{att.attempt_number}</span>
                        <StatusBadge status={att.outcome} />
                      </div>
                      <span className="text-gray-500">{formatDate(att.attempted_at)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
