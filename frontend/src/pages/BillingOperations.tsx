import { useState } from "react";
import Layout from "../components/Layout";
import { billingApi } from "../services/api";
import { BillingRunResult, RetryRunResult } from "../types";

export default function BillingOperations() {
  const [billingResult, setBillingResult] = useState<BillingRunResult | null>(null);
  const [retryResult, setRetryResult] = useState<RetryRunResult | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState("");

  async function runBilling() {
    setRunning("billing");
    setError("");
    try {
      const result = await billingApi.runScheduler();
      setBillingResult(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRunning("");
    }
  }

  async function runRetries() {
    setRunning("retries");
    setError("");
    try {
      const result = await billingApi.runRetries();
      setRetryResult(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRunning("");
    }
  }

  return (
    <Layout title="Billing Operations">
      <div className="max-w-2xl">
        <p className="text-gray-600 mb-6">
          Manually trigger billing operations. These actions process subscriptions and invoices
          in the database. All payments are simulated.
        </p>

        {error && (
          <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg">{error}</div>
        )}

        {/* Billing Scheduler */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-2">Billing Scheduler</h3>
          <p className="text-sm text-gray-500 mb-4">
            Processes subscriptions whose billing period has ended. Generates new invoices and
            advances billing periods.
          </p>
          <button
            onClick={runBilling}
            disabled={!!running}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {running === "billing" ? "Running..." : "Run Billing Scheduler"}
          </button>

          {billingResult && (
            <div className="mt-4 p-4 bg-green-50 rounded-lg">
              <h4 className="font-medium text-green-800 mb-2">Results</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Processed:</span>{" "}
                  <span className="font-semibold">{billingResult.processed}</span>
                </div>
                <div>
                  <span className="text-gray-500">Invoices Created:</span>{" "}
                  <span className="font-semibold">{billingResult.invoices_created}</span>
                </div>
              </div>
              {billingResult.errors.length > 0 && (
                <div className="mt-2 text-red-600 text-sm">
                  <strong>Errors:</strong>
                  <ul className="list-disc ml-4">
                    {billingResult.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Retry Processor */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-2">Retry Processor</h3>
          <p className="text-sm text-gray-500 mb-4">
            Processes failed invoices that are eligible for retry based on the configured schedule
            (3, 7, 14 days).
          </p>
          <button
            onClick={runRetries}
            disabled={!!running}
            className="px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 font-medium"
          >
            {running === "retries" ? "Running..." : "Run Retry Processor"}
          </button>

          {retryResult && (
            <div className="mt-4 p-4 bg-green-50 rounded-lg">
              <h4 className="font-medium text-green-800 mb-2">Results</h4>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Processed:</span>{" "}
                  <span className="font-semibold">{retryResult.processed}</span>
                </div>
                <div>
                  <span className="text-gray-500">Succeeded:</span>{" "}
                  <span className="font-semibold text-green-700">{retryResult.succeeded}</span>
                </div>
                <div>
                  <span className="text-gray-500">Failed:</span>{" "}
                  <span className="font-semibold text-red-700">{retryResult.failed}</span>
                </div>
              </div>
              {retryResult.errors.length > 0 && (
                <div className="mt-2 text-red-600 text-sm">
                  <strong>Errors:</strong>
                  <ul className="list-disc ml-4">
                    {retryResult.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-800">
          <h4 className="font-medium mb-1">How it works</h4>
          <ul className="list-disc ml-4 space-y-1">
            <li><strong>Billing Scheduler</strong> — Finds subscriptions with expired periods and generates new invoices</li>
            <li><strong>Retry Processor</strong> — Retries failed invoices when their retry time is due</li>
            <li>Retry schedule: 3 days, 7 days, 14 days after each failure</li>
            <li>After all retries are exhausted, the subscription is marked as past_due</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}
