import apiClient from './client'

export const investigateAll = async () => {
  const response = await apiClient.post('/api/investigate')
  return response.data
}

export const investigateCustomer = async (customerName) => {
  const response = await apiClient.post(`/api/investigate/by-name/${encodeURIComponent(customerName)}`)
  return response.data
}

export const explainFinding = async (finding) => {
  const response = await apiClient.post('/api/explain', finding)
  return response.data
}

