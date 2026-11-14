import { useState, useEffect } from 'react'
import DataTable from '../components/DataTable'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import { getInspections } from '../api/endpoints'

const DEMO_INSPECTIONS = Array.from({ length: 30 }, (_, i) => ({
  inspection_id: `INS-${String(i + 1).padStart(5, '0')}`,
  shipment_id: `RTS-2026-${String(i + 1).padStart(6, '0')}`,
  rts_id: `RTS-2026-${String(i + 1).padStart(6, '0')}`,
  received_date: new Date(Date.now() - Math.random() * 30 * 86400000).toLocaleDateString('en-IN'),
  condition_on_arrival: ['good', 'damaged', 'partial', 'missing'][i % 4],
  inspector_id: ['INS001', 'INS002', 'INS003'][i % 3],
  overall_condition: ['excellent', 'good', 'fair', 'poor', 'unusable'][i % 5],
  recommended_action: ['restock', 'refurbish', 'quarantine', 'scrap'][i % 4],
  status: i % 3 === 0 ? 'pending' : 'completed',
}))

function DemoBanner() {
  return (
    <div className="mb-4 flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3 text-sm text-yellow-800">
      <span>⚠️</span> Using demo data — start backend for live data
    </div>
  )
}

export default function InspectionsPage() {
  const [loading, setLoading] = useState(true)
  const [demo, setDemo] = useState(false)
  const [inspections, setInspections] = useState([])
  const [viewMode, setViewMode] = useState('all')

  useEffect(() => {
    const fetchInspections = async () => {
      try {
        const res = await getInspections()
        setInspections(res.data?.items || res.data || [])
        setDemo(false)
      } catch {
        setInspections(DEMO_INSPECTIONS)
        setDemo(true)
      } finally {
        setLoading(false)
      }
    }
    fetchInspections()
  }, [])

  const filtered = viewMode === 'pending'
    ? inspections.filter(i => i.status === 'pending')
    : inspections

  const columns = [
    {
      header: 'Shipment ID', accessor: 'shipment_id',
      render: (v) => <span className="font-mono text-xs text-blue-600 font-semibold">{v}</span>
    },
    {
      header: 'RTS ID', accessor: 'rts_id',
      render: (v) => <span className="font-mono text-xs text-gray-500">{v}</span>
    },
    { header: 'Received Date', accessor: 'received_date' },
    {
      header: 'Condition on Arrival', accessor: 'condition_on_arrival',
      render: (v) => <StatusBadge status={v} />
    },
    {
      header: 'Inspector', accessor: 'inspector_id',
      render: (v) => (
        <span className="inline-flex items-center gap-1.5">
          <span className="w-6 h-6 bg-blue-100 text-blue-700 rounded-full text-xs flex items-center justify-center font-bold">
            {v?.slice(-2)}
          </span>
          <span className="text-sm">{v}</span>
        </span>
      )
    },
    {
      header: 'Overall Condition', accessor: 'overall_condition',
      render: (v) => <StatusBadge status={v} />
    },
    {
      header: 'Recommended Action', accessor: 'recommended_action',
      render: (v) => <StatusBadge status={v} />
    },
    {
      header: 'Inspection Status', accessor: 'status',
      render: (v) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
          ${v === 'pending' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
          {v === 'pending' ? '⏳ Pending' : '✓ Completed'}
        </span>
      )
    },
  ]

  if (loading) return <LoadingSpinner message="Loading inspections..." />

  const pendingCount = inspections.filter(i => i.status === 'pending').length

  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Inspections</h2>
          <p className="text-sm text-gray-500">Return shipment inspection results</p>
        </div>
        <div className="flex items-center gap-2">
          {pendingCount > 0 && (
            <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-semibold">
              ⚠️ {pendingCount} pending
            </span>
          )}
          <div className="flex border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('all')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              All
            </button>
            <button
              onClick={() => setViewMode('pending')}
              className={`px-4 py-2 text-sm font-medium transition-colors border-l border-gray-200 ${viewMode === 'pending' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              Pending Only
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Restock', count: inspections.filter(i => i.recommended_action === 'restock').length, color: 'bg-green-50 text-green-700 border-green-200' },
          { label: 'Refurbish', count: inspections.filter(i => i.recommended_action === 'refurbish').length, color: 'bg-blue-50 text-blue-700 border-blue-200' },
          { label: 'Quarantine', count: inspections.filter(i => i.recommended_action === 'quarantine').length, color: 'bg-orange-50 text-orange-700 border-orange-200' },
          { label: 'Scrap', count: inspections.filter(i => i.recommended_action === 'scrap').length, color: 'bg-red-50 text-red-700 border-red-200' },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border p-4 ${s.color}`}>
            <p className="text-xs font-medium opacity-75">{s.label}</p>
            <p className="text-2xl font-bold mt-1">{s.count}</p>
          </div>
        ))}
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        searchPlaceholder="Search Shipment ID, Inspector..."
        emptyMessage="No inspections found."
      />
    </div>
  )
}
