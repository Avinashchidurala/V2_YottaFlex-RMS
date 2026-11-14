import { useState, useEffect } from 'react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import {
  ShoppingCartIcon, ArrowUturnLeftIcon, PercentBadgeIcon,
  CurrencyRupeeIcon, ClockIcon, ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import StatCard from '../components/StatCard'
import LoadingSpinner from '../components/LoadingSpinner'
import {
  getDashboardStats, getReturnTrends, getDispositionBreakdown,
  getReturnsByCategory, getWorkflowFunnel, getAnomalies
} from '../api/endpoints'

const DEMO_STATS = {
  total_orders: 2847,
  return_requests: 423,
  return_rate: 14.9,
  total_refunded_inr: 1823450,
  pending_approvals: 38,
  anomaly_count: 12,
}

const DEMO_TRENDS = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 86400000).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
  returns: Math.floor(5 + Math.random() * 20),
  approvals: Math.floor(3 + Math.random() * 15),
}))

const DEMO_DISPOSITION = [
  { name: 'Restock', value: 182 },
  { name: 'Refurbish', value: 97 },
  { name: 'Quarantine', value: 64 },
  { name: 'Scrap', value: 80 },
]

const DEMO_CATEGORIES = [
  { category: 'Electronics', returns: 98 },
  { category: 'Clothing', returns: 112 },
  { category: 'Home Appliances', returns: 67 },
  { category: 'Books', returns: 23 },
  { category: 'Furniture', returns: 44 },
  { category: 'Beauty', returns: 38 },
  { category: 'Sports', returns: 29 },
  { category: 'Toys', returns: 12 },
]

const DEMO_FUNNEL = [
  { stage: 'Return Requested', count: 423 },
  { stage: 'Authorized', count: 371 },
  { stage: 'Shipped Back', count: 334 },
  { stage: 'Received', count: 310 },
  { stage: 'Inspected', count: 284 },
  { stage: 'Refund Processed', count: 261 },
]

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']

function DemoBanner() {
  return (
    <div className="mb-4 flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3 text-sm text-yellow-800">
      <span className="text-base">⚠️</span>
      <span>Using demo data — start backend for live data</span>
    </div>
  )
}

function formatINR(value) {
  if (value === undefined || value === null) return '—'
  return `₹${Number(value).toLocaleString('en-IN')}`
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [demo, setDemo] = useState(false)
  const [stats, setStats] = useState(DEMO_STATS)
  const [trends, setTrends] = useState(DEMO_TRENDS)
  const [disposition, setDisposition] = useState(DEMO_DISPOSITION)
  const [categories, setCategories] = useState(DEMO_CATEGORIES)
  const [funnel, setFunnel] = useState(DEMO_FUNNEL)

  useEffect(() => {
    let isDemo = false
    const fetchAll = async () => {
      try {
        const [sRes, tRes, dRes, cRes, fRes] = await Promise.allSettled([
          getDashboardStats(),
          getReturnTrends(),
          getDispositionBreakdown(),
          getReturnsByCategory(),
          getWorkflowFunnel(),
        ])
        if (sRes.status === 'fulfilled') setStats(sRes.value.data)
        else isDemo = true
        if (tRes.status === 'fulfilled') setTrends(tRes.value.data)
        if (dRes.status === 'fulfilled') setDisposition(dRes.value.data)
        if (cRes.status === 'fulfilled') setCategories(cRes.value.data)
        if (fRes.status === 'fulfilled') setFunnel(fRes.value.data)
        setDemo(isDemo)
      } catch {
        setDemo(true)
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [])

  if (loading) return <LoadingSpinner message="Loading dashboard..." />

  return (
    <div className="space-y-6">
      {demo && <DemoBanner />}

      {/* Page title */}
      <div>
        <h2 className="text-xl font-bold text-gray-900">Dashboard Overview</h2>
        <p className="text-sm text-gray-500 mt-1">Returns management KPIs and workflow status</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          label="Total Orders"
          value={stats.total_orders?.toLocaleString('en-IN')}
          icon={ShoppingCartIcon}
          color="blue"
          trend={3.2}
          trendLabel="vs last month"
        />
        <StatCard
          label="Return Requests"
          value={stats.return_requests?.toLocaleString('en-IN')}
          icon={ArrowUturnLeftIcon}
          color="orange"
          trend={-5.1}
          trendLabel="vs last month"
        />
        <StatCard
          label="Return Rate"
          value={`${stats.return_rate ?? 0}%`}
          icon={PercentBadgeIcon}
          color="purple"
          trend={-0.8}
          trendLabel="vs last month"
        />
        <StatCard
          label="Total Refunded"
          value={formatINR(stats.total_refunded_inr)}
          icon={CurrencyRupeeIcon}
          color="green"
          subtitle="Net refunds processed"
        />
        <StatCard
          label="Pending Approvals"
          value={stats.pending_approvals}
          icon={ClockIcon}
          color="yellow"
        />
        <StatCard
          label="Anomalies"
          value={stats.anomaly_count}
          icon={ExclamationTriangleIcon}
          color="red"
        />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Return Trends */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Return Trends (Last 30 Days)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="returns" stroke="#3b82f6" strokeWidth={2} dot={false} name="Returns" />
              <Line type="monotone" dataKey="approvals" stroke="#10b981" strokeWidth={2} dot={false} name="Approvals" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Disposition PieChart */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Disposition Breakdown</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={disposition}
                cx="50%"
                cy="50%"
                outerRadius={90}
                dataKey="value"
                nameKey="name"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {disposition.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Returns by Category */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Returns by Category</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={categories} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} />
              <YAxis dataKey="category" type="category" tick={{ fontSize: 11 }} width={100} tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="returns" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Returns" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Workflow Funnel */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Return Workflow Funnel</h3>
          <div className="space-y-3 mt-2">
            {funnel.map((step, i) => {
              const max = funnel[0]?.count || 1
              const pct = Math.round((step.count / max) * 100)
              return (
                <div key={i}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-600 font-medium">{step.stage}</span>
                    <span className="text-xs font-bold text-gray-800">{step.count?.toLocaleString('en-IN')}</span>
                  </div>
                  <div className="h-6 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full flex items-center justify-end pr-2 text-xs text-white font-medium transition-all duration-500"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: `hsl(${220 - i * 15}, 80%, ${55 - i * 3}%)`,
                        minWidth: '40px',
                      }}
                    >
                      {pct}%
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
