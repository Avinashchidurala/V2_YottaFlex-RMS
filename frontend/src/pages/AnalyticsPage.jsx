import { useState, useEffect } from 'react'

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    fetch('/api/v1/dashboard/metrics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(console.error)
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Merchandising & Reverse Logistics Analytics</h1>
        <p className="text-sm text-slate-500">Executive financial overview, policy compliance, return rates, and recovery retention in INR (₹).</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200">
          <div className="text-xs font-semibold text-slate-500 uppercase">Gross Sales Revenue</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">₹{metrics ? Number(metrics.gross_revenue_inr).toLocaleString('en-IN') : '...'}</div>
          <div className="text-xs text-slate-400 mt-1">{metrics ? metrics.total_orders.toLocaleString() : '30,000'} orders</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200">
          <div className="text-xs font-semibold text-rose-600 uppercase">Total Refund Outflow</div>
          <div className="text-2xl font-bold text-rose-600 mt-1">₹{metrics ? Number(metrics.total_refunded_inr).toLocaleString('en-IN') : '...'}</div>
          <div className="text-xs text-slate-400 mt-1">Processed reimbursements</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200">
          <div className="text-xs font-semibold text-emerald-600 uppercase">Net Retained Revenue</div>
          <div className="text-2xl font-bold text-emerald-600 mt-1">₹{metrics ? Number(metrics.net_revenue_inr).toLocaleString('en-IN') : '...'}</div>
          <div className="text-xs text-slate-400 mt-1">Post-return revenue</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200">
          <div className="text-xs font-semibold text-amber-600 uppercase">Return Rate</div>
          <div className="text-2xl font-bold text-amber-600 mt-1">{metrics ? metrics.return_rate_pct : '16.7'}%</div>
          <div className="text-xs text-slate-400 mt-1">5,000 total returns</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200">
          <h3 className="font-bold text-slate-900 mb-4">Top Return Reasons Breakdown</h3>
          <div className="space-y-3">
            {[
              { reason: 'Defective / Quality Issue', pct: 28, count: 1400 },
              { reason: 'Changed Mind', pct: 24, count: 1200 },
              { reason: 'Sizing / Fit Issue', pct: 20, count: 1000 },
              { reason: 'Wrong Item Delivered', pct: 15, count: 750 },
              { reason: 'Damaged in Transit', pct: 13, count: 650 },
            ].map(r => (
              <div key={r.reason} className="space-y-1">
                <div className="flex justify-between text-xs font-medium text-slate-700">
                  <span>{r.reason}</span>
                  <span>{r.count} ({r.pct}%)</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${r.pct}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200">
          <h3 className="font-bold text-slate-900 mb-4">Category Return Vulnerability</h3>
          <div className="space-y-3">
            {[
              { cat: 'Clothing & Apparel', rate: '22.4%', window: '7 days', status: 'High Volume' },
              { cat: 'Electronics & Audio', rate: '18.1%', window: '7 days', status: 'High Value' },
              { cat: 'Home Appliances', rate: '14.5%', window: '7 days', status: 'Moderate' },
              { cat: 'Furniture & Decor', rate: '9.2%', window: '7 days', status: 'Low Volume' },
              { cat: 'Perishables & Beauty', rate: '0.0%', window: '0 days', status: 'Non-Returnable' },
            ].map(c => (
              <div key={c.cat} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 text-xs">
                <div>
                  <div className="font-bold text-slate-900">{c.cat}</div>
                  <div className="text-slate-500">Policy: {c.window}</div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-indigo-600">{c.rate} return rate</div>
                  <div className="text-slate-400">{c.status}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
