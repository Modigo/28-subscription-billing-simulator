// TypeScript types matching backend API schemas

export interface Plan {
  id: number;
  name: string;
  description: string | null;
  price: string;
  currency: string;
  billing_interval: string;
  trial_days: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: number;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
  subscriptions?: Subscription[];
}

export interface Subscription {
  id: number;
  customer_id: number;
  plan_id: number;
  status: string;
  current_period_start: string;
  current_period_end: string;
  trial_end: string | null;
  canceled_at: string | null;
  created_at: string;
  updated_at: string;
  plan?: Plan;
  customer?: Customer;
}

export interface Invoice {
  id: number;
  subscription_id: number;
  invoice_number: string;
  amount: string;
  currency: string;
  status: string;
  billing_period_start: string;
  billing_period_end: string;
  issued_at: string;
  due_at: string;
  paid_at: string | null;
  attempt_count: number;
  next_retry_at: string | null;
  plan_name: string | null;
  plan_price: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentAttempt {
  id: number;
  invoice_id: number;
  attempt_number: number;
  outcome: string;
  failure_reason: string | null;
  attempted_at: string;
}

export interface BillingEvent {
  id: number;
  event_type: string;
  subscription_id: number | null;
  invoice_id: number | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface DashboardSummary {
  total_customers: number;
  total_active_subscriptions: number;
  total_invoices: number;
  paid_invoices: number;
  failed_invoices: number;
  past_due_subscriptions: number;
  suspended_subscriptions: number;
  total_revenue: Record<string, string>;
  recent_invoices: Invoice[];
  recent_events: BillingEvent[];
}

export interface BillingRunResult {
  processed: number;
  invoices_created: number;
  errors: string[];
}

export interface RetryRunResult {
  processed: number;
  succeeded: number;
  failed: number;
  errors: string[];
}
