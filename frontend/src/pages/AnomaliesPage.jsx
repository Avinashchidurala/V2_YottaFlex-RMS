import { useState, useEffect } from 'react'

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/v1/dashboard/metrics')
      .then(res => res.json())
      .then(data => {
        if (data.recent_anomalies) setAnomalies(data.recent_anomalies)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Synthetic Ground Truth Anomaly Radar</h1>
        <p className="text-sm text-slate-500">Deliberately injected edge cases strictly isolated in ground_truth.csv without corrupting valid records.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl">
          <div className="text-xs font-bold text-rose-700 uppercase">Return Qty &gt; Purchased</div>
          <div className="text-2xl font-bold text-rose-900 mt-1">50 Cases</div>
        </div>
        <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl">
          <div className="text-xs font-bold text-rose-700 uppercase">Refund &gt; Paid Amount</div>
          <div className="text-2xl font-bold text-rose-900 mt-1">30 Cases</div>
        </div>
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl">
          <div className="text-xs font-bold text-amber-700 uppercase">Restock Before Inspection</div>
          <div className="text-2xl font-bold text-amber-900 mt-1">25 Cases</div>
        </div>
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl">
          <div className="text-xs font-bold text-amber-700 uppercase">Late Return (No Override)</div>
          <div className="text-2xl font-bold text-amber-900 mt-1">40 Cases</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 p-4 rounded-xl">
          <div className="text-xs font-bold text-purple-700 uppercase">Duplicate Refund Attempts</div>
          <div className="text-2xl font-bold text-purple-900 mt-1">35 Cases</div>
        </div>
        <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl">
          <div className="text-xs font-bold text-blue-700 uppercase">Lost / Missing Shipments</div>
          <div className="text-2xl font-bold text-blue-900 mt-1">20 Cases</div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">Ground Truth Anomalies Log</h2>
          <span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-600">Total: 200 Records</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-semibold">
              <tr>
                <th className="px-6 py-3">Anomaly ID</th>
                <th className="px-6 py-3">Entity Type & ID</th>
                <th className="px-6 py-3">Issue Type</th>
                <th className="px-6 py-3">Severity</th>
                <th className="px-6 py-3">Anomaly Description</th>
                <th className="px-6 py-3">Detection Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {anomalies.map(a => (
                <tr key={a.anomaly_id} className="hover:bg-slate-50 transition">
                  <td className="px-6 py-4 font-mono font-bold text-rose-600">{a.anomaly_id}</td>
                  <td className="px-6 py-4 font-mono text-slate-600">{a.entity_type}: {a.entity_id}</td>
                  <td className="px-6 py-4 font-semibold text-slate-800">{a.anomaly_type}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${a.severity === 'critical' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'}`}>
                      {a.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-600">{a.description}</td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-400">{a.detected_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
