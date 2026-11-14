import { useState, useEffect } from 'react'
import DataTable from '../components/DataTable'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import { getReturnRequests, approveReturn, rejectReturn } from '../api/endpoints'

const REASONS = ['defective', 'wrong_item', 'not_as_described', 'changed_mind', 'damaged_in_transit', 'sizing_issue', 'quality_issue']
const STATUSES = ['pending', 'approved', 'partially_approved', 'rejected', 'cancelled']

const DEMO_RETURNS = Array.from({ length: 40 }, (_, i) => ({
  request_id: `RMA-2026-${String(i + 1).padStart(6, '0')}`,
  customer_name: ['Priya Sharma', 'Amit Kumar', 'Deepa Nair', 'Rahul Verma', 'Sunita Patel'][i % 5],
  order_id: `ORD-2026-${String(i + 1).padStart(6, '0')}`,
  request_date: new Date(Date.now() - Math.random() * 60 * 86400000).toLocaleDateString('en-IN'),
  reason: REASONS[i % REASONS.length],
  status: STATUSES[i % STATUSES.length],
  days_since_delivery: Math.floor(1 + Math.random() * 45),
}))

function DemoBanner() {
  return (
    <div className="mb-4 flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3 text-sm text-yellow-800">
      <span>⚠️</span> Using demo data — start backend for live data
    </div>
  )
}

export default function ReturnsPage() {
  const [loading, setLoading] = useState(true)
  const [demo, setDemo] = useState(false)
  const [returns, setReturns] = useState([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [actionLoading, setActionLoading] = useState(null)
  const [toast, setToast] = useState(null)

  const fetchReturns = async (status = 'all') => {
    try {
      const params = status !== 'all' ? { status } : {}
      const res = await getReturnRequests(params)
      setReturns(res.data?.items || res.data || [])
      setDemo(false)
    } catch {
      setReturns(DEMO_RETURNS)
      setDemo(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchReturns(statusFilter) }, [statusFilter])

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const handleApprove = async (row) => {
    setActionLoading(row.request_id + '_approve')
    try {
      await approveReturn(row.request_id)
      showToast(`Return ${row.request_id} approved successfully`)
      fetchReturns(statusFilter)
    } catch {
      // Demo mode: just update local state
      setReturns(prev => prev.map(r => r.request_id === row.request_id ? { ...r, status: 'approved' } : r))
      showToast(`Return ${row.request_id} approved (demo mode)`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleReject = async (row) => {
    setActionLoading(row.request_id + '_reject')
    try {
      await rejectReturn(row.request_id)
      showToast(`Return ${row.request_id} rejected`, 'error')
      fetchReturns(statusFilter)
    } catch {
      setReturns(prev => prev.map(r => r.request_id === row.request_id ? { ...r, status: 'rejected' } : r))
      showToast(`Return ${row.request_id} rejected (demo mode)`, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const filtered = returns.filter(r => statusFilter === 'all' || r.status === statusFilter)

  const columns = [
    {
      header: 'RMA ID', accessor: 'request_id',
      render: (v) => <span className="font-mono text-xs text-blue-600 font-semibold">{v}</span>
    },
    { header: 'Customer', accessor: 'customer_name' },
    {
      header: 'Order', accessor: 'order_id',
      render: (v) => <span className="font-mono text-xs text-gray-500">{v}</span>
    },
    { header: 'Request Date', accessor: 'request_date' },
    {
      header: 'Reason', accessor: 'reason',
      render: (v) => <span className="capitalize text-gray-700">{v?.replace(/_/g, ' ')}</span>
    },
    { header: 'Status', accessor: 'status', render: (v) => <StatusBadge status={v} /> },
    {
      header: 'Days Since Delivery', accessor: 'days_since_delivery',
      render: (v) => (
        <span className={`font-semibold ${v > 30 ? 'text-red-600' : v > 15 ? 'text-orange-500' : 'text-green-600'}`}>
          {v}d
        </span>
      )
    },
    {
      header: 'Actions', accessor: 'status', key: 'actions', sortable: false,
      render: (status, row) => (
        status === 'pending' ? (
          <div className="flex gap-2">
            <button
              onClick={e => { e.stopPropagation(); handleApprove(row) }}
              disabled={actionLoading === row.request_id + '_approve'}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
            >
              {actionLoading === row.request_id + '_approve' ? '...' : 'Approve'}
            </button>
            <button
              onClick={e => { e.stopPropagation(); handleReject(row) }}
              disabled={actionLoading === row.request_id + '_reject'}
              className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
            >
              {actionLoading === row.request_id + '_reject' ? '...' : 'Reject'}
            </button>
          </div>
        ) : (
          <span className="text-gray-400 text-xs">—</span>
        )
      )
    },
  ]

  if (loading) return <LoadingSpinner message="Loading return requests..." />

  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}

      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium text-white
          ${toast.type === 'error' ? 'bg-red-600' : 'bg-green-600'}`}>
          {toast.msg}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Return Requests</h2>
          <p className="text-sm text-gray-500">Review and act on customer return requests</p>
        </div>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
        </select>
      </div>

      {/* Summary badges */}
      <div className="flex flex-wrap gap-3">
        {['pending', 'approved', 'rejected'].map(s => {
          const count = returns.filter(r => r.status === s).length
          const colors = { pending: 'bg-yellow-100 text-yellow-700', approved: 'bg-green-100 text-green-700', rejected: 'bg-red-100 text-red-700' }
          return (
            <button
              key={s}
              onClick={() => setStatusFilter(statusFilter === s ? 'all' : s)}
              className={`px-4 py-2 rounded-full text-xs font-semibold capitalize transition-all border-2
                ${statusFilter === s ? 'border-current' : 'border-transparent'} ${colors[s]}`}
            >
              {s}: {count}
            </button>
          )
        })}
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        searchPlaceholder="Search RMA ID, Customer, Order..."
        rowClassName={(row) => row.days_since_delivery > 30 ? 'bg-red-50/30' : ''}
      />
    </div>
  )
}
