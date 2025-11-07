import apiClient from './client'

export const getProposals = async () => {
  const response = await apiClient.get('/api/proposals')
  return response.data
}

export const applyProposal = async (proposal) => {
  const response = await apiClient.post('/api/proposals/apply', { proposal })
  return response.data
}

export const rollbackAction = async (actionId) => {
  const response = await apiClient.post(`/api/proposals/rollback/${actionId}`)
  return response.data
}

export const getAuditLog = async (limit) => {
  const params = limit ? { limit } : {}
  const response = await apiClient.get('/api/audit-log', { params })
  return response.data
}

export const getSandboxStats = async () => {
  const response = await apiClient.get('/api/sandbox/stats')
  return response.data
}

export const getSandboxActions = async () => {
  const response = await apiClient.get('/api/sandbox/actions')
  return response.data
}

