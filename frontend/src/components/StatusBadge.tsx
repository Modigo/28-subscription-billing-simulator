const statusColors: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  trialing: "bg-blue-100 text-blue-800",
  paid: "bg-green-100 text-green-800",
  success: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  failed: "bg-red-100 text-red-800",
  canceled: "bg-gray-100 text-gray-800",
  cancelled: "bg-gray-100 text-gray-800",
  paused: "bg-orange-100 text-orange-800",
  past_due: "bg-red-100 text-red-800",
  suspended: "bg-red-200 text-red-900",
  retired: "bg-gray-200 text-gray-700",
  void: "bg-gray-100 text-gray-600",
  failure: "bg-red-100 text-red-800",
};

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colorClass = statusColors[status.toLowerCase()] || "bg-gray-100 text-gray-800";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {status}
    </span>
  );
}
