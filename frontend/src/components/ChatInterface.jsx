import { useState, useEffect, useRef } from 'react'
import { streamChatMessage } from '../api/chatStream'
import { Send, MessageSquare, Loader2, Trash2, Wrench, CheckCircle } from 'lucide-react'

function ChatInterface() {
  // Load messages from localStorage on mount
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('chatMessages')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [toolCalls, setToolCalls] = useState([])
  const chatEndRef = useRef(null)

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chatMessages', JSON.stringify(messages))
  }, [messages])

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage, toolCalls])

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    const userMessage = input.trim()
    console.log('[CHAT] Sending message:', userMessage)
    
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setInput('')
    setIsStreaming(true)
    setStreamingMessage('')
    setToolCalls([])

    try {
      let assistantMessage = ''
      const currentToolCalls = []
      let eventCount = 0

      console.log('[CHAT] Starting to receive events')
      
      for await (const event of streamChatMessage(userMessage)) {
        eventCount++
        console.log(`[CHAT] Processing event #${eventCount}:`, event.type, event)
        
        if (event.type === 'text') {
          console.log('[CHAT] Text event:', event.content.substring(0, 50))
          // PydanticAI sends the full message so far, not deltas
          assistantMessage = event.content
          setStreamingMessage(assistantMessage)
        } else if (event.type === 'tool_call') {
          console.log('[CHAT] Tool call event:', event.tool_name)
          const toolCall = {
            id: Date.now() + Math.random(),
            name: event.tool_name,
            args: event.args,
            status: 'calling'
          }
          currentToolCalls.push(toolCall)
          setToolCalls([...currentToolCalls])
        } else if (event.type === 'tool_result') {
          console.log('[CHAT] Tool result event')
          const lastTool = currentToolCalls[currentToolCalls.length - 1]
          if (lastTool) {
            lastTool.status = 'completed'
            lastTool.result = event.result
          }
          setToolCalls([...currentToolCalls])
        } else if (event.type === 'error') {
          console.error('[CHAT] Error event:', event.content)
          assistantMessage += `\n\n[Error: ${event.content}]`
          setStreamingMessage(assistantMessage)
        } else if (event.type === 'done') {
          console.log('[CHAT] Done event received')
          // Finalize the message
          if (assistantMessage) {
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              content: assistantMessage,
              toolCalls: currentToolCalls.length > 0 ? currentToolCalls : undefined
            }])
          }
          setStreamingMessage('')
          setToolCalls([])
        } else {
          console.warn('[CHAT] Unknown event type:', event.type, event)
        }
      }
      
      console.log(`[CHAT] Stream completed with ${eventCount} events`)
    } catch (error) {
      console.error('[CHAT] Error in stream:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message}`
      }])
      setStreamingMessage('')
      setToolCalls([])
    } finally {
      setIsStreaming(false)
      console.log('[CHAT] Streaming finished')
    }
  }

  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      setMessages([])
      localStorage.removeItem('chatMessages')
    }
  }

  return (
    <div className="bg-white rounded-lg shadow h-[600px] flex flex-col">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">Chat with AI Agent</h2>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Ask questions about revenue leakage and investigations
            </p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md flex items-center space-x-1 transition-colors"
              title="Clear chat history"
            >
              <Trash2 className="h-4 w-4" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && !streamingMessage ? (
          <div className="text-center text-gray-500 mt-12">
            <p>Start a conversation by asking a question</p>
            <p className="text-sm mt-2">Example: "What revenue leakage did we find for Sopita?"</p>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} flex-col`}>
                <div
                  className={`max-w-3xl rounded-lg px-4 py-2 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
                
                {/* Show tool calls if any */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mt-2 space-y-1 max-w-3xl">
                    {msg.toolCalls.map((tool) => (
                      <div key={tool.id} className="flex items-center space-x-2 text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">
                        <Wrench className="h-3 w-3" />
                        <span className="font-mono">{tool.name}</span>
                        {tool.status === 'completed' && (
                          <CheckCircle className="h-3 w-3 text-green-600" />
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            
            {/* Show streaming message */}
            {streamingMessage && (
              <div className="flex justify-start flex-col">
                <div className="max-w-3xl bg-gray-100 text-gray-900 rounded-lg px-4 py-2">
                  <p className="text-sm whitespace-pre-wrap">{streamingMessage}</p>
                  <span className="inline-block w-2 h-4 bg-gray-600 animate-pulse ml-1"></span>
                </div>
                
                {/* Show active tool calls */}
                {toolCalls.length > 0 && (
                  <div className="mt-2 space-y-1 max-w-3xl">
                    {toolCalls.map((tool) => (
                      <div key={tool.id} className="flex items-center space-x-2 text-xs bg-blue-50 px-2 py-1 rounded border border-blue-200">
                        {tool.status === 'calling' ? (
                          <>
                            <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
                            <span className="text-blue-700 font-mono">{tool.name}</span>
                            <span className="text-blue-500">calling...</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle className="h-3 w-3 text-green-600" />
                            <span className="font-mono text-green-700">{tool.name}</span>
                            <span className="text-green-600">completed</span>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="px-6 py-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            className="flex-1 border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isStreaming ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface

