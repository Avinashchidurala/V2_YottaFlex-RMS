import client from './client'

// Dashboard
export const getDashboardStats = () => client.get('/dashboard/stats')
export const getReturnTrends = () => client.get('/dashboard/return-trends')
export const getDispositionBreakdown = () => client.get('/dashboard/disposition-breakdown')
export const getReturnsByCategory = () => client.get('/dashboard/returns-by-category')
export const getWorkflowFunnel = () => client.get('/dashboard/workflow-funnel')
export const getAnomalies = () => client.get('/dashboard/anomalies')

// Orders
export const getOrders = (params = {}) => client.get('/orders', { params })
export const getOrderById = (id) => client.get(`/orders/${id}`)

// Returns
export const getReturnRequests = (params = {}) => client.get('/returns', { params })
export const getReturnById = (id) => client.get(`/returns/${id}`)
export const approveReturn = (id, data = {}) => client.post(`/returns/${id}/approve`, data)
export const rejectReturn = (id, data = {}) => client.post(`/returns/${id}/reject`, data)

// Inspections
export const getInspections = (params = {}) => client.get('/inspections', { params })
export const getPendingInspections = () => client.get('/inspections/pending')
export const getInspectionById = (id) => client.get(`/inspections/${id}`)

// Refunds
export const getRefunds = (params = {}) => client.get('/refunds', { params })
export const getRefundStats = () => client.get('/refunds/stats')
export const getRefundById = (id) => client.get(`/refunds/${id}`)

// Dispositions
export const getDispositions = (params = {}) => client.get('/dispositions', { params })
export const getDispositionStats = () => client.get('/dispositions/stats')

// Analytics
export const getEligibilityDecisions = () => client.get('/analytics/eligibility-decisions')
export const getRefundReconciliation = () => client.get('/analytics/refund-reconciliation')
export const getPolicyCompliance = () => client.get('/analytics/policy-compliance')
