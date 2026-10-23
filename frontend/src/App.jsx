import { useEffect, useState } from 'react'
import './App.css'

function formatMoney(kobo) {
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
    maximumFractionDigits: 2,
  }).format((kobo ?? 0) / 100)
}

function formatDate(value) {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return '—'

  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function formatStatus(value) {
  if (!value) return 'Unknown'

  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function statusClass(value) {
  return (value || 'unknown').toLowerCase().replaceAll('_', '-').replaceAll(' ', '-')
}

function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [customers, setCustomers] = useState([])
  const [plans, setPlans] = useState([])
  const [subscriptions, setSubscriptions] = useState([])
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true)
      setError('')

      try {
        const endpoints = [
          '/api/customers',
          '/api/plans',
          '/api/subscriptions',
          '/api/invoices',
        ]

        const responses = await Promise.all(
          endpoints.map((endpoint) => fetch(endpoint))
        )

        const failedResponse = responses.find((response) => !response.ok)

        if (failedResponse) {
          throw new Error(`API request failed (${failedResponse.status}).`)
        }

        const [customerData, planData, subscriptionData, invoiceData] =
          await Promise.all(responses.map((response) => response.json()))

        setCustomers(customerData)
        setPlans(planData)
        setSubscriptions(subscriptionData)
        setInvoices(invoiceData)
      } catch (err) {
        setError(
          `${err.message} Make sure the FastAPI backend is running on port 8000.`
        )
      } finally {
        setLoading(false)
      }
    }

    loadDashboard()
  }, [])

  const navigation = [
    { name: 'Overview', icon: '⌂' },
    { name: 'Plans', icon: '▤' },
    { name: 'Subscriptions', icon: '↻' },
    { name: 'Invoices', icon: '▧' },
  ]

  function renderTable(headers, rows) {
    return (
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              {headers.map((header) => (
                <th key={header}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    )
  }

  function renderContent() {
    if (loading) {
      return <section className="panel"><p style={{ padding: 24 }}>Loading dashboard data...</p></section>
    }

    if (error) {
      return (
        <section className="panel">
          <div style={{ padding: 24 }}>
            <h2>Unable to load dashboard data</h2>
            <p role="alert">{error}</p>
            <button className="text-button" onClick={() => window.location.reload()}>
              Try again
            </button>
          </div>
        </section>
      )
    }

    if (activePage === 'Plans') {
      return (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Subscription Plans</h2>
              <p>Plans retrieved from the backend.</p>
            </div>
            <span className="sample-label">Live API data</span>
          </div>
          {renderTable(
            ['Plan', 'Price', 'Billing Interval', 'Status'],
            plans.map((plan) => (
              <tr key={plan.id}>
                <td><strong>{plan.name}</strong></td>
                <td>{formatMoney(plan.price_kobo)}</td>
                <td>{formatStatus(plan.billing_interval)}</td>
                <td>
                  <span className={`badge ${plan.is_active ? 'active' : 'cancelled'}`}>
                    {plan.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))
          )}
          {plans.length === 0 && <p style={{ padding: 24 }}>No plans found.</p>}
        </section>
      )
    }

    if (activePage === 'Subscriptions') {
      return (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Subscriptions</h2>
              <p>Subscriptions retrieved from the backend.</p>
            </div>
            <span className="sample-label">Live API data</span>
          </div>
          {renderTable(
            ['Subscription', 'Customer ID', 'Plan ID', 'Next Billing', 'Status'],
            subscriptions.map((sub) => (
              <tr key={sub.id}>
                <td>SUB-{String(sub.id).padStart(3, '0')}</td>
                <td>{sub.customer_id}</td>
                <td>{sub.plan_id}</td>
                <td>{formatDate(sub.next_billing_date)}</td>
                <td>
                  <span className={`badge ${statusClass(sub.status)}`}>
                    {formatStatus(sub.status)}
                  </span>
                </td>
              </tr>
            ))
          )}
          {subscriptions.length === 0 && (
            <p style={{ padding: 24 }}>No subscriptions found.</p>
          )}
        </section>
      )
    }

    if (activePage === 'Invoices') {
      return (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Invoices</h2>
              <p>Track invoices and simulated payment statuses.</p>
            </div>
            <span className="sample-label">Live API data</span>
          </div>
          {renderTable(
            ['Invoice', 'Subscription ID', 'Amount', 'Issue Date', 'Status'],
            invoices.map((invoice) => (
              <tr key={invoice.id}>
                <td>{invoice.invoice_number}</td>
                <td>{invoice.subscription_id}</td>
                <td>{formatMoney(invoice.amount_kobo)}</td>
                <td>{formatDate(invoice.issue_date)}</td>
                <td>
                  <span className={`badge ${statusClass(invoice.status)}`}>
                    {formatStatus(invoice.status)}
                  </span>
                </td>
              </tr>
            ))
          )}
          {invoices.length === 0 && (
            <p style={{ padding: 24 }}>No invoices found.</p>
          )}
        </section>
      )
    }

    return (
      <>
        <section className="stats-grid">
          <article className="stat-card">
            <div className="stat-top">
              <span>Total Customers</span>
              <span className="stat-icon">♙</span>
            </div>
            <h2>{customers.length}</h2>
            <p>Customer records in the database</p>
          </article>

          <article className="stat-card">
            <div className="stat-top">
              <span>Active Subscriptions</span>
              <span className="stat-icon">↻</span>
            </div>
            <h2>{subscriptions.filter((sub) => sub.status === 'active').length}</h2>
            <p>Currently active subscriptions</p>
          </article>

          <article className="stat-card">
            <div className="stat-top">
              <span>Paid Invoices</span>
              <span className="stat-icon">✓</span>
            </div>
            <h2>{invoices.filter((invoice) => invoice.status === 'paid').length}</h2>
            <p>Invoices with successful simulated payments</p>
          </article>

          <article className="stat-card">
            <div className="stat-top">
              <span>Available Plans</span>
              <span className="stat-icon">▤</span>
            </div>
            <h2>{plans.filter((plan) => plan.is_active).length}</h2>
            <p>Active subscription plans</p>
          </article>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Recent Subscriptions</h2>
              <p>A quick look at recent customer activity.</p>
            </div>
            <button className="text-button" onClick={() => setActivePage('Subscriptions')}>
              View all →
            </button>
          </div>
          {renderTable(
            ['Subscription', 'Customer ID', 'Plan ID', 'Next Billing', 'Status'],
            [...subscriptions]
              .sort((a, b) => b.id - a.id)
              .slice(0, 5)
              .map((sub) => (
                <tr key={sub.id}>
                  <td>SUB-{String(sub.id).padStart(3, '0')}</td>
                  <td>{sub.customer_id}</td>
                  <td>{sub.plan_id}</td>
                  <td>{formatDate(sub.next_billing_date)}</td>
                  <td>
                    <span className={`badge ${statusClass(sub.status)}`}>
                      {formatStatus(sub.status)}
                    </span>
                  </td>
                </tr>
              ))
          )}
          {subscriptions.length === 0 && (
            <p style={{ padding: 24 }}>No subscriptions found.</p>
          )}
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Recent Invoices</h2>
              <p>Check payment activity at a glance.</p>
            </div>
            <button className="text-button" onClick={() => setActivePage('Invoices')}>
              View all →
            </button>
          </div>
          {renderTable(
            ['Invoice', 'Subscription ID', 'Amount', 'Issue Date', 'Status'],
            [...invoices]
              .sort((a, b) => b.id - a.id)
              .slice(0, 5)
              .map((invoice) => (
                <tr key={invoice.id}>
                  <td>{invoice.invoice_number}</td>
                  <td>{invoice.subscription_id}</td>
                  <td>{formatMoney(invoice.amount_kobo)}</td>
                  <td>{formatDate(invoice.issue_date)}</td>
                  <td>
                    <span className={`badge ${statusClass(invoice.status)}`}>
                      {formatStatus(invoice.status)}
                    </span>
                  </td>
                </tr>
              ))
          )}
          {invoices.length === 0 && (
            <p style={{ padding: 24 }}>No invoices found.</p>
          )}
        </section>
      </>
    )
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">S</div>
          <div>
            <h2>SubBill</h2>
            <span>Billing Simulator</span>
          </div>
        </div>

        <p className="nav-label">WORKSPACE</p>
        <nav>
          {navigation.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${activePage === item.name ? 'selected' : ''}`}
              onClick={() => setActivePage(item.name)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="avatar">TS</div>
          <div>
            <strong>Team Simulator</strong>
            <span>Project workspace</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="breadcrumb">Workspace / {activePage}</p>
            <h1>{activePage}</h1>
          </div>
          <div className="topbar-right">
            <span className="environment">
              <span className="status-dot" /> Demo environment
            </span>
            <div className="avatar">TS</div>
          </div>
        </header>

        <div className="page-content">
          {activePage === 'Overview' && (
            <div className="welcome">
              <div>
                <h2>Welcome to SubBill 👋</h2>
                <p>Monitor plans, subscriptions, invoices, and simulated billing activity.</p>
              </div>
              <span className="demo-tag">LIVE API DATA</span>
            </div>
          )}

          {renderContent()}

          <footer className="page-footer">
            Subscription Billing Simulator · Demo interface · No real payments are processed
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App