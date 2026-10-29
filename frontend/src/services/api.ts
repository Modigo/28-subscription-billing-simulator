// API client layer
import {
  Plan,
  Customer,
  Subscription,
  Invoice,
  PaymentAttempt,
  BillingEvent,
  DashboardSummary,
  BillingRunResult,
  RetryRunResult,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }
  return response.json();
}

// Plans
export const plansApi = {
  list: (status?: string) => {
    const q = status ? `?status=${status}` : "";
    return request<Plan[]>(`/api/v1/plans${q}`);
  },
  get: (id: number) => request<Plan>(`/api/v1/plans/${id}`),
  create: (data: { name: string; description?: string; price: string; currency?: string; billing_interval?: string; trial_days?: number }) =>
    request<Plan>("/api/v1/plans", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Plan>) =>
    request<Plan>(`/api/v1/plans/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  retire: (id: number) =>
    request<Plan>(`/api/v1/plans/${id}/retire`, { method: "POST" }),
};

// Customers
export const customersApi = {
  list: (skip = 0, limit = 100) =>
    request<Customer[]>(`/api/v1/customers?skip=${skip}&limit=${limit}`),
  get: (id: number) => request<Customer>(`/api/v1/customers/${id}`),
  create: (data: { name: string; email: string }) =>
    request<Customer>("/api/v1/customers", { method: "POST", body: JSON.stringify(data) }),
};

// Subscriptions
export const subscriptionsApi = {
  list: (customer_id?: number, status?: string) => {
    const params = new URLSearchParams();
    if (customer_id) params.set("customer_id", String(customer_id));
    if (status) params.set("status", status);
    return request<Subscription[]>(`/api/v1/subscriptions?${params}`);
  },
  get: (id: number) => request<Subscription>(`/api/v1/subscriptions/${id}`),
  create: (data: { customer_id: number; plan_id: number }) =>
    request<Subscription>("/api/v1/subscriptions", { method: "POST", body: JSON.stringify(data) }),
  pause: (id: number) =>
    request<Subscription>(`/api/v1/subscriptions/${id}/pause`, { method: "POST" }),
  resume: (id: number) =>
    request<Subscription>(`/api/v1/subscriptions/${id}/resume`, { method: "POST" }),
  cancel: (id: number) =>
    request<Subscription>(`/api/v1/subscriptions/${id}/cancel`, { method: "POST" }),
  changePlan: (id: number, data: { plan_id: number; change_type?: string }) =>
    request<Subscription>(`/api/v1/subscriptions/${id}/change-plan`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// Invoices
export const invoicesApi = {
  list: (status?: string, subscription_id?: number) => {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (subscription_id) params.set("subscription_id", String(subscription_id));
    return request<{ items: Invoice[]; total: number }>(`/api/v1/invoices?${params}`);
  },
  get: (id: number) => request<Invoice>(`/api/v1/invoices/${id}`),
  simulatePayment: (id: number, outcome: string) =>
    request<PaymentAttempt>(`/api/v1/invoices/${id}/simulate-payment`, {
      method: "POST",
      body: JSON.stringify({ outcome }),
    }),
  getAttempts: (id: number) => request<PaymentAttempt[]>(`/api/v1/invoices/${id}/attempts`),
};

// Billing
export const billingApi = {
  runScheduler: () =>
    request<BillingRunResult>("/api/v1/billing/run", { method: "POST" }),
  runRetries: () =>
    request<RetryRunResult>("/api/v1/retries/run", { method: "POST" }),
};

// Dashboard
export const dashboardApi = {
  getSummary: () => request<DashboardSummary>("/api/v1/dashboard/summary"),
  getEvents: (event_type?: string) => {
    const q = event_type ? `?event_type=${event_type}` : "";
    return request<BillingEvent[]>(`/api/v1/events${q}`);
  },
};
