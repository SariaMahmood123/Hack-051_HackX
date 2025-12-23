'use client'

import { useState } from 'react'
import MessageList from './MessageList'
import VideoPlayer from './VideoPlayer'
import InputBox from './InputBox'
import Toast from './Toast'
import { generateFullPipeline } from '@/lib/api'
import { getErrorMessage, generateId } from '@/lib/utils'
import type { Message } from '@/types'

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentVideo, setCurrentVideo] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null)

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const handleSendMessage = async (userMessage: string) => {
    // Add user message
    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      text: userMessage,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMsg])
    
    // Start generation
    setIsGenerating(true)
    
    try {
      // Call backend API
      const response = await generateFullPipeline({
        prompt: userMessage,
        conversation_history: messages.map(m => ({
          role: m.role === 'user' ? 'user' : 'model',
          parts: [m.text]
        }))
      })
      
      // Add assistant message with video
      const assistantMsg: Message = {
        id: response.request_id,
        role: 'assistant',
        text: response.text,
        videoPath: response.video_url,
        audioPath: response.audio_url,
        timestamp: response.timestamp
      }
      setMessages(prev => [...prev, assistantMsg])
      setCurrentVideo(response.video_url)
      
      showToast('Video response generated successfully!', 'success')
      
    } catch (error) {
      console.error('Generation failed:', error)
      
      const errorMessage = getErrorMessage(error)
      showToast(errorMessage, 'error')
      
      // Add error message
      const errorMsg: Message = {
        id: generateId(),
        role: 'assistant',
        text: `❌ Sorry, something went wrong: ${errorMessage}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsGenerating(false)
    }
  }

  const handleClearChat = () => {
    if (confirm('Clear all messages?')) {
      setMessages([])
      setCurrentVideo(null)
      showToast('Chat cleared', 'info')
    }
  }

  return (
    <>
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Video Player Section */}
        <div className="bg-gray-800 rounded-lg shadow-2xl p-6 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-300">Video</h2>
            {currentVideo && (
              <button
                onClick={() => setCurrentVideo(null)}
                className="text-sm text-gray-400 hover:text-white transition-colors"
                title="Clear video"
              >
                Clear
              </button>
            )}
          </div>
          <VideoPlayer videoPath={currentVideo} isGenerating={isGenerating} />
        </div>

        {/* Chat Section */}
        <div className="bg-gray-800 rounded-lg shadow-2xl p-6 flex flex-col animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-300">Chat</h2>
            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                className="text-sm text-gray-400 hover:text-white transition-colors"
                disabled={isGenerating}
              >
                Clear Chat
              </button>
            )}
          </div>
          
          <MessageList messages={messages} />
          
          <InputBox 
            onSend={handleSendMessage} 
            disabled={isGenerating}
            isGenerating={isGenerating}
          />
        </div>
      </div>

      {toast && <Toast message={toast.message} type={toast.type} />}
    </>
  )
}
