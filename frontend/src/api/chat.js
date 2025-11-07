import apiClient from './client'

export const sendChatMessage = async (message, context = null) => {
  const response = await apiClient.post('/api/chat', { message, context })
  return response.data
}

