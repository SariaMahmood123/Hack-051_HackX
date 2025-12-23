'use client'

import { useEffect, useRef } from 'react'
import { formatTimestamp } from '@/lib/utils'
import type { Message } from '@/types'

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto mb-4 space-y-4 min-h-[400px] max-h-[500px] pr-2">
      {messages.length === 0 && (
        <div className="text-center text-gray-400 mt-20 animate-fade-in">
          <div className="mb-4">
            <svg
              className="mx-auto h-16 w-16 text-gray-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <p className="text-lg">Start a conversation with LUMEN</p>
          <p className="text-sm mt-2">Ask me anything!</p>
        </div>
      )}
      
      {messages.map((message, index) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
          style={{ animationDelay: `${index * 0.05}s` }}
        >
          <div
            className={`max-w-[80%] rounded-lg px-4 py-3 ${
              message.role === 'user'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-100'
            } shadow-lg transition-smooth hover:shadow-xl`}
          >
            <div className="flex items-center gap-2 mb-1">
              <p className="text-sm font-medium">
                {message.role === 'user' ? '👤 You' : '🤖 LUMEN'}
              </p>
              {message.videoPath && (
                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                  Video
                </span>
              )}
            </div>
            <p className="whitespace-pre-wrap leading-relaxed">{message.text}</p>
            <p className="text-xs opacity-70 mt-2">
              {formatTimestamp(message.timestamp)}
            </p>
          </div>
        </div>
      ))}
      
      <div ref={messagesEndRef} />
    </div>
  )
}
