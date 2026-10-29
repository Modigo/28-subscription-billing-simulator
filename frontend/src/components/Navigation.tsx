import { Link, useLocation } from "react-router-dom";

const navItems = [
  { path: "/", label: "Dashboard" },
  { path: "/plans", label: "Plans" },
  { path: "/customers", label: "Customers" },
  { path: "/subscriptions", label: "Subscriptions" },
  { path: "/invoices", label: "Invoices" },
  { path: "/billing", label: "Billing Ops" },
];

export default function Navigation() {
  const location = useLocation();

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-lg font-bold text-blue-600">
              Billing Simulator
            </Link>
            <div className="hidden sm:flex sm:gap-1">
              {navItems.map((item) => {
                const active = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      active
                        ? "bg-blue-50 text-blue-700"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="text-xs text-gray-400">Demo Mode</div>
        </div>
        {/* Mobile nav */}
        <div className="sm:hidden flex gap-1 pb-3 overflow-x-auto">
          {navItems.map((item) => {
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap ${
                  active
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
