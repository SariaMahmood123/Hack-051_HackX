'use client'

import { useState } from 'react'
import MessageList from './MessageList'
import VideoPlayer from './VideoPlayer'
import InputBox from './InputBox'
import Toast from './Toast'
import { generateFullPipeline, generateMKBHDAudio } from '@/lib/api'
import { getErrorMessage, generateId } from '@/lib/utils'
import type { Message } from '@/types'

type GenerationMode = 'full' | 'mkbhd'

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentVideo, setCurrentVideo] = useState<string | null>(null)
  const [currentAudio, setCurrentAudio] = useState<string | null>(null)
  const [mode, setMode] = useState<GenerationMode>('mkbhd')
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
      if (mode === 'mkbhd') {
        // MKBHD audio-only mode
        showToast('Generating MKBHD-style script and audio...', 'info')
        
        const response = await generateMKBHDAudio({
          prompt: userMessage
          // Uses backend default (800 tokens) for full reviews
        })
        
        // Add assistant message with audio
        const assistantMsg: Message = {
          id: response.request_id,
          role: 'assistant',
          text: response.script,
          audioPath: response.audio_url,
          timestamp: response.timestamp
        }
        setMessages(prev => [...prev, assistantMsg])
        setCurrentAudio(response.audio_url)
        setCurrentVideo(null) // Clear video in audio mode
        
        showToast(`MKBHD audio generated (${response.duration.toFixed(1)}s)`, 'success')
        
      } else {
        // Full pipeline mode (original)
        showToast('Generating video response...', 'info')
        
        const response = await generateFullPipeline({
          prompt: userMessage,
          max_tokens: 150,
          temperature: 0.7
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
        setCurrentAudio(null)
        
        showToast('Video response generated successfully!', 'success')
      }
      
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
      setCurrentAudio(null)
      showToast('Chat cleared', 'info')
    }
  }

  return (
    <>
      <div className="max-w-6xl mx-auto">
        {/* Mode Selector */}
        <div className="mb-4 flex justify-center">
          <div className="bg-gray-800 rounded-lg p-1 inline-flex">
            <button
              onClick={() => setMode('mkbhd')}
              disabled={isGenerating}
              className={`px-6 py-2 rounded-md font-medium transition-all ${
                mode === 'mkbhd'
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white'
              } disabled:opacity-50`}
            >
              🎤 MKBHD Voice
            </button>
            <button
              onClick={() => setMode('full')}
              disabled={isGenerating}
              className={`px-6 py-2 rounded-md font-medium transition-all ${
                mode === 'full'
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white'
              } disabled:opacity-50`}
            >
              🎬 Full Video
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Video/Audio Player Section */}
          <div className="bg-gray-800 rounded-lg shadow-2xl p-6 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-300">
                {mode === 'mkbhd' ? 'Audio Player' : 'Video Player'}
              </h2>
              {(currentVideo || currentAudio) && (
                <button
                  onClick={() => {
                    setCurrentVideo(null)
                    setCurrentAudio(null)
                  }}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                  title="Clear media"
                >
                  Clear
                </button>
              )}
            </div>
            
            {mode === 'mkbhd' && currentAudio ? (
              <div className="bg-gray-900 rounded-lg p-6 flex flex-col items-center justify-center min-h-[400px]">
                <div className="text-6xl mb-6">🎙️</div>
                <h3 className="text-xl font-bold text-white mb-4">MKBHD Audio</h3>
                <audio
                  controls
                  src={`http://localhost:8000${currentAudio}`}
                  className="w-full max-w-md"
                  autoPlay
                >
                  Your browser does not support audio playback.
                </audio>
                <p className="text-gray-400 text-sm mt-4">High-quality 24kHz audio</p>
              </div>
            ) : (
              <VideoPlayer videoPath={currentVideo} isGenerating={isGenerating} />
            )}
          </div>

          {/* Chat Section */}
          <div className="bg-gray-800 rounded-lg shadow-2xl p-6 flex flex-col animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-300">
                {mode === 'mkbhd' ? 'MKBHD Tech Review' : 'Chat'}
              </h2>
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
            
            {mode === 'mkbhd' && messages.length === 0 && (
              <div className="mb-4 p-4 bg-purple-900/30 rounded-lg border border-purple-500/30">
                <p className="text-purple-300 text-sm">
                  <strong>MKBHD Mode:</strong> Enter a tech product or topic, and get a review in Marques' style with his voice!
                </p>
                <p className="text-purple-400 text-xs mt-2">
                  Example: "the new iPhone 16 Pro Max camera system"
                </p>
              </div>
            )}
            
            <MessageList messages={messages} />
            
            <InputBox 
              onSend={handleSendMessage} 
              disabled={isGenerating}
              isGenerating={isGenerating}
              placeholder={
                mode === 'mkbhd' 
                  ? "Enter a tech product or topic..." 
                  : "Type your message..."
              }
            />
          </div>
        </div>
      </div>

      {toast && <Toast message={toast.message} type={toast.type} />}
    </>
  )
}
