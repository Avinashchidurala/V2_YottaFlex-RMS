import clsx from 'clsx'

const statusConfig = {
  // Order statuses
  pending: { label: 'Pending', cls: 'bg-yellow-100 text-yellow-700' },
  confirmed: { label: 'Confirmed', cls: 'bg-blue-100 text-blue-700' },
  shipped: { label: 'Shipped', cls: 'bg-indigo-100 text-indigo-700' },
  delivered: { label: 'Delivered', cls: 'bg-green-100 text-green-700' },
  cancelled: { label: 'Cancelled', cls: 'bg-gray-100 text-gray-600' },

  // Return statuses
  approved: { label: 'Approved', cls: 'bg-green-100 text-green-700' },
  partially_approved: { label: 'Partial', cls: 'bg-blue-100 text-blue-700' },
  rejected: { label: 'Rejected', cls: 'bg-red-100 text-red-700' },

  // Inspection / condition
  excellent: { label: 'Excellent', cls: 'bg-green-100 text-green-700' },
  good: { label: 'Good', cls: 'bg-green-100 text-green-600' },
  fair: { label: 'Fair', cls: 'bg-yellow-100 text-yellow-700' },
  poor: { label: 'Poor', cls: 'bg-orange-100 text-orange-700' },
  unusable: { label: 'Unusable', cls: 'bg-red-100 text-red-700' },

  // Arrival condition
  damaged: { label: 'Damaged', cls: 'bg-red-100 text-red-700' },
  partial: { label: 'Partial', cls: 'bg-orange-100 text-orange-700' },
  missing: { label: 'Missing', cls: 'bg-red-100 text-red-800' },

  // Disposition actions
  restock: { label: 'Restock', cls: 'bg-green-100 text-green-700' },
  refurbish: { label: 'Refurbish', cls: 'bg-blue-100 text-blue-700' },
  quarantine: { label: 'Quarantine', cls: 'bg-orange-100 text-orange-700' },
  scrap: { label: 'Scrap', cls: 'bg-red-100 text-red-700' },

  // Refund statuses
  processed: { label: 'Processed', cls: 'bg-green-100 text-green-700' },
  duplicate: { label: 'Duplicate', cls: 'bg-red-100 text-red-700' },

  // Shipment statuses
  in_transit: { label: 'In Transit', cls: 'bg-blue-100 text-blue-700' },
  received: { label: 'Received', cls: 'bg-green-100 text-green-700' },
  lost: { label: 'Lost', cls: 'bg-red-100 text-red-700' },

  // Auth statuses
  active: { label: 'Active', cls: 'bg-green-100 text-green-700' },
  expired: { label: 'Expired', cls: 'bg-gray-100 text-gray-600' },
  used: { label: 'Used', cls: 'bg-blue-100 text-blue-700' },
}

export default function StatusBadge({ status }) {
  if (!status) return <span className="text-gray-400 text-xs">—</span>
  const cfg = statusConfig[status.toLowerCase()] || {
    label: status,
    cls: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', cfg.cls)}>
      {cfg.label}
    </span>
  )
}
