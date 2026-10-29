import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Plans from "./pages/Plans";
import Customers from "./pages/Customers";
import Subscriptions from "./pages/Subscriptions";
import Invoices from "./pages/Invoices";
import BillingOperations from "./pages/BillingOperations";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/plans" element={<Plans />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/subscriptions" element={<Subscriptions />} />
        <Route path="/invoices" element={<Invoices />} />
        <Route path="/billing" element={<BillingOperations />} />
      </Routes>
    </BrowserRouter>
  );
}
