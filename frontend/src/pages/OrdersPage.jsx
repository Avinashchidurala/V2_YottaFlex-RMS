import { useState, useEffect } from 'react'
import DataTable from '../components/DataTable'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import { getOrders, getOrderById } from '../api/endpoints'
import { XMarkIcon } from '@heroicons/react/24/outline'

const DEMO_ORDERS = Array.from({ length: 50 }, (_, i) => ({
  order_id: `ORD-2026-${String(i + 1).padStart(6, '0')}`,
  customer_name: ['Priya Sharma', 'Amit Kumar', 'Deepa Nair', 'Rahul Verma', 'Sunita Patel'][i % 5],
  order_date: new Date(Date.now() - Math.random() * 90 * 86400000).toLocaleDateString('en-IN'),
  net_amount_inr: Math.floor(500 + Math.random() * 50000),
  status: ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'][i % 5],
  return_count: Math.floor(Math.random() * 3),
}))

const STATUS_OPTIONS = ['all', 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled']

function formatINR(v) {
  return `₹${Number(v).toLocaleString('en-IN')}`
}

function DemoBanner() {
  return (
    <div className="mb-4 flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3 text-sm text-yellow-800">
      <span>⚠️</span> Using demo data — start backend for live data
    </div>
  )
}

export default function OrdersPage() {
  const [loading, setLoading] = useState(true)
  const [demo, setDemo] = useState(false)
  const [orders, setOrders] = useState([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [orderDetail, setOrderDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const params = {}
        if (statusFilter !== 'all') params.status = statusFilter
        if (dateFrom) params.date_from = dateFrom
        if (dateTo) params.date_to = dateTo
        const res = await getOrders(params)
        setOrders(res.data?.items || res.data || [])
        setDemo(false)
      } catch {
        setOrders(DEMO_ORDERS)
        setDemo(true)
      } finally {
        setLoading(false)
      }
    }
    fetchOrders()
  }, [statusFilter, dateFrom, dateTo])

  const handleRowClick = async (row) => {
    setSelectedOrder(row)
    setOrderDetail(null)
    setDetailLoading(true)
    try {
      const res = await getOrderById(row.order_id)
      setOrderDetail(res.data)
    } catch {
      setOrderDetail({
        ...row,
        order_lines: Array.from({ length: 3 }, (_, i) => ({
          line_id: `LINE-${i + 1}`,
          product_name: ['Samsung Galaxy', 'Cotton Shirt', 'Java Book'][i],
          category: ['electronics', 'clothing', 'books'][i],
          quantity: i + 1,
          unit_price_inr: Math.floor(1000 + Math.random() * 20000),
          line_total_inr: Math.floor(2000 + Math.random() * 20000),
          is_returnable: i < 2,
          return_window_days: [30, 15, 0][i],
        })),
      })
    } finally {
      setDetailLoading(false)
    }
  }

  const filtered = orders.filter(o => statusFilter === 'all' || o.status === statusFilter)

  const columns = [
    { header: 'Order ID', accessor: 'order_id', render: (v) => <span className="font-mono text-xs text-blue-600 font-semibold">{v}</span> },
    { header: 'Customer', accessor: 'customer_name' },
    { header: 'Date', accessor: 'order_date' },
    { header: 'Net Amount', accessor: 'net_amount_inr', render: (v) => <span className="font-semibold text-gray-800">{formatINR(v)}</span> },
    { header: 'Status', accessor: 'status', render: (v) => <StatusBadge status={v} /> },
    { header: '# Returns', accessor: 'return_count', render: (v) => (
      <span className={`font-semibold ${v > 0 ? 'text-orange-600' : 'text-gray-400'}`}>{v}</span>
    )},
  ]

  if (loading) return <LoadingSpinner message="Loading orders..." />

  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Orders</h2>
          <p className="text-sm text-gray-500">All customer orders with return activity</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {STATUS_OPTIONS.map(s => (
              <option key={s} value={s}>{s === 'all' ? 'All Statuses' : s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>
          <input
            type="date"
            value={dateFrom}
            onChange={e => setDateFrom(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="date"
            value={dateTo}
            onChange={e => setDateTo(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        searchPlaceholder="Search by Order ID, Customer..."
        onRowClick={handleRowClick}
      />

      {/* Order Detail Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setSelectedOrder(null)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <div>
                <h3 className="font-bold text-gray-900">Order Details</h3>
                <p className="text-sm text-blue-600 font-mono">{selectedOrder.order_id}</p>
              </div>
              <button onClick={() => setSelectedOrder(null)} className="text-gray-400 hover:text-gray-600">
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Customer:</span> <span className="font-medium">{orderDetail?.customer_name || selectedOrder.customer_name}</span></div>
                <div><span className="text-gray-500">Date:</span> <span className="font-medium">{selectedOrder.order_date}</span></div>
                <div><span className="text-gray-500">Status:</span> <StatusBadge status={selectedOrder.status} /></div>
                <div><span className="text-gray-500">Net Amount:</span> <span className="font-semibold text-green-700">{formatINR(selectedOrder.net_amount_inr)}</span></div>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Order Lines</h4>
                {detailLoading ? (
                  <div className="flex justify-center py-6"><div className="w-6 h-6 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin" /></div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-3 py-2 text-left font-semibold text-gray-500">Product</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-500">Category</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-500">Qty</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-500">Unit Price</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-500">Total</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-500">Returnable</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {(orderDetail?.order_lines || []).map((line, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-3 py-2 font-medium">{line.product_name}</td>
                            <td className="px-3 py-2 text-gray-500 capitalize">{line.category}</td>
                            <td className="px-3 py-2">{line.quantity}</td>
                            <td className="px-3 py-2">{formatINR(line.unit_price_inr)}</td>
                            <td className="px-3 py-2 font-semibold">{formatINR(line.line_total_inr)}</td>
                            <td className="px-3 py-2">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${line.is_returnable ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                {line.is_returnable ? `Yes (${line.return_window_days}d)` : 'No'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
