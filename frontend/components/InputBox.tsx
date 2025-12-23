'use client'

import { useState, KeyboardEvent, useRef, useEffect } from 'react'
import { validatePrompt } from '@/lib/utils'

interface InputBoxProps {
  onSend: (message: string) => void
  disabled: boolean
  isGenerating: boolean
}

export default function InputBox({ onSend, disabled, isGenerating }: InputBoxProps) {
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-focus on mount
  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [disabled])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [input])

  const handleSend = () => {
    const validation = validatePrompt(input)
    
    if (!validation.valid) {
      setError(validation.error || 'Invalid input')
      return
    }

    if (!disabled) {
      onSend(input.trim())
      setInput('')
      setError(null)
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    setError(null)
  }

  return (
    <div className="space-y-2">
      {error && (
        <div className="text-red-400 text-sm px-2 animate-slide-up">
          {error}
        </div>
      )}
      
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleChange}
            onKeyPress={handleKeyPress}
            placeholder={
              isGenerating 
                ? "Generating response..." 
                : "Type your message... (Shift+Enter for newline)"
            }
            disabled={disabled}
            className={`w-full bg-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none transition-smooth min-h-[56px] max-h-[200px] ${
              error ? 'ring-2 ring-red-500' : ''
            } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            rows={1}
            maxLength={2000}
          />
          
          {input.length > 1800 && (
            <div className="absolute bottom-2 right-2 text-xs text-gray-400">
              {input.length}/2000
            </div>
          )}
        </div>
        
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-smooth flex items-center gap-2 min-w-[100px] justify-center"
          title={disabled ? 'Please wait...' : 'Send message (Enter)'}
        >
          {isGenerating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span className="hidden sm:inline">Wait</span>
            </>
          ) : (
            <>
              <span>Send</span>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </>
          )}
        </button>
      </div>
      
      <div className="text-xs text-gray-500 px-2">
        Press Enter to send • Shift+Enter for new line
      </div>
    </div>
  )
}
