import { useState } from 'react'
import './App.css'

const plans = [
  { id: 1, name: 'Starter', price: '₦5,000', interval: 'month', status: 'Active' },
  { id: 2, name: 'Professional', price: '₦15,000', interval: 'month', status: 'Active' },
  { id: 3, name: 'Enterprise', price: '₦50,000', interval: 'month', status: 'Active' },
]

const subscriptions = [
  { id: 'SUB-001', customer: 'Ada Okafor', plan: 'Professional', status: 'Active', nextBilling: 'Nov 01, 2026' },
  { id: 'SUB-002', customer: 'Tunde Bello', plan: 'Starter', status: 'Active', nextBilling: 'Nov 03, 2026' },
  { id: 'SUB-003', customer: 'Amara James', plan: 'Enterprise', status: 'Past Due', nextBilling: 'Oct 20, 2026' },
  { id: 'SUB-004', customer: 'Chidi Eze', plan: 'Professional', status: 'Cancelled', nextBilling: '—' },
]

const invoices = [
  { id: 'INV-001', customer: 'Ada Okafor', amount: '₦15,000', date: 'Oct 01, 2026', status: 'Paid' },
  { id: 'INV-002', customer: 'Tunde Bello', amount: '₦5,000', date: 'Oct 03, 2026', status: 'Paid' },
  { id: 'INV-003', customer: 'Amara James', amount: '₦50,000', date: 'Oct 20, 2026', status: 'Overdue' },
  { id: 'INV-004', customer: 'Chidi Eze', amount: '₦15,000', date: 'Oct 21, 2026', status: 'Pending' },
]

function App() {
  const [activePage, setActivePage] = useState('Overview')

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
    if (activePage === 'Plans') {
      return (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Subscription Plans</h2>
              <p>Manage the plans available to your customers.</p>
            </div>
            <span className="sample-label">Sample data</span>
          </div>
          {renderTable(
            ['Plan', 'Price', 'Billing Interval', 'Status'],
            plans.map((plan) => (
              <tr key={plan.id}>
                <td><strong>{plan.name}</strong></td>
                <td>{plan.price}</td>
                <td>Monthly</td>
                <td><span className="badge active">{plan.status}</span></td>
              </tr>
            ))
          )}
        </section>
      )
    }

    if (activePage === 'Subscriptions') {
      return (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Subscriptions</h2>
              <p>Review customer subscriptions and their billing dates.</p>
            </div>
            <span className="sample-label">Sample data</span>
          </div>
          {renderTable(
            ['Subscription', 'Customer', 'Plan', 'Next Billing', 'Status'],
            subscriptions.map((sub) => (
              <tr key={sub.id}>
                <td>{sub.id}</td>
                <td><strong>{sub.customer}</strong></td>
                <td>{sub.plan}</td>
                <td>{sub.nextBilling}</td>
                <td>
                  <span className={`badge ${sub.status.toLowerCase().replace(' ', '-')}`}>
                    {sub.status}
                  </span>
                </td>
              </tr>
            ))
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
            <span className="sample-label">Sample data</span>
          </div>
          {renderTable(
            ['Invoice', 'Customer', 'Amount', 'Issue Date', 'Status'],
            invoices.map((invoice) => (
              <tr key={invoice.id}>
                <td>{invoice.id}</td>
                <td><strong>{invoice.customer}</strong></td>
                <td>{invoice.amount}</td>
                <td>{invoice.date}</td>
                <td>
                  <span className={`badge ${invoice.status.toLowerCase()}`}>
                    {invoice.status}
                  </span>
                </td>
              </tr>
            ))
          )}
        </section>
      )
    }

    return (
      <>
        <section className="stats-grid">
          <article className="stat-card">
            <div className="stat-top"><span>Total Customers</span><span className="stat-icon">♙</span></div>
            <h2>4</h2>
            <p>Sample customer records</p>
          </article>
          <article className="stat-card">
            <div className="stat-top"><span>Active Subscriptions</span><span className="stat-icon">↻</span></div>
            <h2>2</h2>
            <p>Currently active in sample data</p>
          </article>
          <article className="stat-card">
            <div className="stat-top"><span>Paid Invoices</span><span className="stat-icon">✓</span></div>
            <h2>2</h2>
            <p>Successfully simulated payments</p>
          </article>
          <article className="stat-card">
            <div className="stat-top"><span>Available Plans</span><span className="stat-icon">▤</span></div>
            <h2>3</h2>
            <p>Monthly subscription plans</p>
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
            ['Subscription', 'Customer', 'Plan', 'Next Billing', 'Status'],
            subscriptions.slice(0, 3).map((sub) => (
              <tr key={sub.id}>
                <td>{sub.id}</td>
                <td><strong>{sub.customer}</strong></td>
                <td>{sub.plan}</td>
                <td>{sub.nextBilling}</td>
                <td>
                  <span className={`badge ${sub.status.toLowerCase().replace(' ', '-')}`}>
                    {sub.status}
                  </span>
                </td>
              </tr>
            ))
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
            ['Invoice', 'Customer', 'Amount', 'Issue Date', 'Status'],
            invoices.slice(0, 3).map((invoice) => (
              <tr key={invoice.id}>
                <td>{invoice.id}</td>
                <td><strong>{invoice.customer}</strong></td>
                <td>{invoice.amount}</td>
                <td>{invoice.date}</td>
                <td>
                  <span className={`badge ${invoice.status.toLowerCase()}`}>
                    {invoice.status}
                  </span>
                </td>
              </tr>
            ))
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
            <span className="environment"><span className="status-dot" /> Demo environment</span>
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
              <span className="demo-tag">DEMO DATA</span>
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
