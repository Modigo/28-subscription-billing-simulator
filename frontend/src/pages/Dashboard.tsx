import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import StatusBadge from "../components/StatusBadge";
import { dashboardApi, billingApi } from "../services/api";
import { DashboardSummary, BillingRunResult, RetryRunResult } from "../types";
import { formatCurrency, formatDate, formatDateShort } from "../utils/format";

export default function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [billingResult, setBillingResult] = useState<BillingRunResult | null>(null);
  const [retryResult, setRetryResult] = useState<RetryRunResult | null>(null);
  const [running, setRunning] = useState("");

  async function load() {
    try {
      const summary = await dashboardApi.getSummary();
      setData(summary);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function runBilling() {
    setRunning("billing");
    try {
      const result = await billingApi.runScheduler();
      setBillingResult(result);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRunning("");
    }
  }

  async function runRetries() {
    setRunning("retries");
    try {
      const result = await billingApi.runRetries();
      setRetryResult(result);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRunning("");
    }
  }

  if (loading) return <Layout title="Dashboard"><p className="text-gray-500">Loading...</p></Layout>;
  if (error && !data) return <Layout title="Dashboard"><p className="text-red-600">{error}</p></Layout>;
  if (!data) return null;

  const revenueEntries = Object.entries(data.total_revenue);

  return (
    <Layout title="Dashboard">
      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Customers" value={data.total_customers} />
        <MetricCard label="Active Subs" value={data.total_active_subscriptions} />
        <MetricCard label="Paid Invoices" value={data.paid_invoices} />
        <MetricCard label="Failed Invoices" value={data.failed_invoices} color="red" />
      </div>

      {/* Revenue */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Simulated Revenue</h2>
        {revenueEntries.length > 0 ? (
          <div className="space-y-2">
            {revenueEntries.map(([currency, amount]) => (
              <div key={currency} className="flex justify-between">
                <span className="text-gray-600">{currency}</span>
                <span className="font-semibold">{formatCurrency(amount, currency)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400">No revenue yet</p>
        )}
        <p className="text-xs text-gray-400 mt-2">All payments are simulated</p>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={runBilling}
            disabled={!!running}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {running === "billing" ? "Running..." : "Run Billing Scheduler"}
          </button>
          <button
            onClick={runRetries}
            disabled={!!running}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
          >
            {running === "retries" ? "Running..." : "Run Retry Processor"}
          </button>
        </div>
        {billingResult && (
          <div className="mt-3 p-3 bg-green-50 rounded text-sm text-green-800">
            Billing: {billingResult.processed} processed, {billingResult.invoices_created} invoices created
          </div>
        )}
        {retryResult && (
          <div className="mt-3 p-3 bg-green-50 rounded text-sm text-green-800">
            Retries: {retryResult.processed} processed, {retryResult.succeeded} succeeded, {retryResult.failed} failed
          </div>
        )}
      </div>

      {/* Recent Invoices */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Recent Invoices</h2>
        {data.recent_invoices.length === 0 ? (
          <p className="text-gray-400">No invoices yet</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Number</th>
                <th className="text-left py-2">Amount</th>
                <th className="text-left py-2">Status</th>
                <th className="text-left py-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_invoices.map((inv) => (
                <tr key={inv.id} className="border-b border-gray-50">
                  <td className="py-2">{inv.invoice_number}</td>
                  <td className="py-2">{formatCurrency(inv.amount, inv.currency)}</td>
                  <td className="py-2"><StatusBadge status={inv.status} /></td>
                  <td className="py-2 text-gray-500">{formatDateShort(inv.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Recent Events */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Events</h2>
        {data.recent_events.length === 0 ? (
          <p className="text-gray-400">No events yet</p>
        ) : (
          <div className="space-y-2">
            {data.recent_events.map((ev) => (
              <div key={ev.id} className="flex justify-between text-sm">
                <span className="font-medium">{ev.event_type}</span>
                <span className="text-gray-500">{formatDate(ev.created_at)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}

function MetricCard({ label, value, color = "blue" }: { label: string; value: number; color?: string }) {
  const bgColors: Record<string, string> = {
    blue: "bg-blue-50",
    red: "bg-red-50",
  };
  return (
    <div className={`rounded-lg shadow p-4 ${bgColors[color] || bgColors.blue}`}>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
