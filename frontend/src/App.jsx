import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import OrdersPage from './pages/OrdersPage'
import ReturnsPage from './pages/ReturnsPage'
import InspectionsPage from './pages/InspectionsPage'
import RefundsPage from './pages/RefundsPage'
import DispositionsPage from './pages/DispositionsPage'
import AnomaliesPage from './pages/AnomaliesPage'
import AnalyticsPage from './pages/AnalyticsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="orders" element={<OrdersPage />} />
          <Route path="returns" element={<ReturnsPage />} />
          <Route path="inspections" element={<InspectionsPage />} />
          <Route path="refunds" element={<RefundsPage />} />
          <Route path="dispositions" element={<DispositionsPage />} />
          <Route path="anomalies" element={<AnomaliesPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
