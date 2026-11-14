import { useState } from 'react'

export default function DispositionsPage() {
  const mockDispositions = [
    { id: 'DISP-2026-000001', prod: 'Samsung Galaxy S24 Ultra', qty: 1, action: 'restock', location: 'WH-BIN-RES-101', recInr: 116999.10, date: '2026-11-13' },
    { id: 'DISP-2026-000002', prod: 'boAt Nirvana ANC Headphones', qty: 1, action: 'refurbish', location: 'WH-BIN-REF-204', recInr: 1999.50, date: '2026-11-12' },
    { id: 'DISP-2026-000003', prod: 'Fabindia Men Khadi Kurta', qty: 1, action: 'restock', location: 'WH-BIN-RES-105', recInr: 2241.00, date: '2026-11-11' },
    { id: 'DISP-2026-000004', prod: 'Wakefit Office Chair', qty: 1, action: 'scrap', location: 'WH-BIN-SCR-901', recInr: 424.95, date: '2026-11-10' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Inventory Dispositions & Item Fate</h1>
        <p className="text-sm text-slate-500">Post-inspection routing: Restock, Refurbish, Quarantine, or Scrap with estimated recovery values.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <div className="text-xs font-semibold text-emerald-600 uppercase">Restock (90% Value)</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">2,840 Items</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <div className="text-xs font-semibold text-blue-600 uppercase">Refurbish (50% Value)</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">820 Items</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <div className="text-xs font-semibold text-amber-600 uppercase">Quarantine (20% Value)</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">260 Items</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <div className="text-xs font-semibold text-rose-600 uppercase">Scrap (5% Value)</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">162 Items</div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-semibold">
              <tr>
                <th className="px-6 py-3">Disposition ID</th>
                <th className="px-6 py-3">Product Name</th>
                <th className="px-6 py-3">Action</th>
                <th className="px-6 py-3">Warehouse Bin Location</th>
                <th className="px-6 py-3">Estimated Recovery (INR)</th>
                <th className="px-6 py-3">Date Disposed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {mockDispositions.map(d => (
                <tr key={d.id} className="hover:bg-slate-50 transition">
                  <td className="px-6 py-4 font-mono font-bold text-slate-900">{d.id}</td>
                  <td className="px-6 py-4 font-medium text-slate-800">{d.prod}</td>
                  <td className="px-6 py-4 capitalize font-semibold text-indigo-600">{d.action}</td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-500">{d.location}</td>
                  <td className="px-6 py-4 font-bold text-emerald-600 font-mono">₹{d.recInr.toLocaleString('en-IN')}</td>
                  <td className="px-6 py-4 text-slate-500 text-xs font-mono">{d.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
