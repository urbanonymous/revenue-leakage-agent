/**
 * Stream chat messages using Server-Sent Events
 */
export async function* streamChatMessage(message, context = null) {
  console.log('[STREAM-CLIENT] Starting stream for message:', message)
  
  const response = await fetch('http://localhost:8000/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, context }),
  })

  console.log('[STREAM-CLIENT] Response status:', response.status)
  
  if (!response.ok) {
    console.error('[STREAM-CLIENT] Response not OK:', response.status)
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let eventCount = 0

  console.log('[STREAM-CLIENT] Starting to read stream')

  while (true) {
    const { done, value } = await reader.read()
    
    if (done) {
      console.log('[STREAM-CLIENT] Stream done, total events:', eventCount)
      break
    }
    
    const chunk = decoder.decode(value, { stream: true })
    console.log('[STREAM-CLIENT] Raw chunk received:', chunk.substring(0, 100))
    
    buffer += chunk
    const lines = buffer.split('\n')
    
    // Keep the last partial line in the buffer
    buffer = lines.pop() || ''
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        console.log('[STREAM-CLIENT] SSE data:', data.substring(0, 100))
        try {
          const event = JSON.parse(data)
          eventCount++
          console.log(`[STREAM-CLIENT] Event #${eventCount}:`, event.type, event)
          yield event
        } catch (e) {
          console.error('[STREAM-CLIENT] Failed to parse SSE data:', data, e)
        }
      }
    }
  }
  
  console.log('[STREAM-CLIENT] Stream completed')
}

