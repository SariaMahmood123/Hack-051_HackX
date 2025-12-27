'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import FloatingBackground from '@/components/FloatingBackground'
import GlassCard from '@/components/GlassCard'
import PersonaSelector from '@/components/PersonaSelector'
import Link from 'next/link'

interface Message {
  id: string
  role: 'user' | 'assistant'
  text: string
  timestamp: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export default function ChatPage() {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [showPersonaSelector, setShowPersonaSelector] = useState(false)
  const [pendingPrompt, setPendingPrompt] = useState('')
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const cached = sessionStorage.getItem('lumen_chat_messages')
    if (cached) {
      try {
        const parsed = JSON.parse(cached) as Message[]
        setMessages(parsed)
      } catch {
        sessionStorage.removeItem('lumen_chat_messages')
      }
    }
  }, [])

  useEffect(() => {
    sessionStorage.setItem('lumen_chat_messages', JSON.stringify(messages))
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)

    try {
      const response = await fetch(`${API_BASE_URL}/generate/mkbhd`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: input,
          max_tokens: 800
        })
      })

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}))
        throw new Error(detail?.detail || 'Generation failed')
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: data.request_id || (Date.now() + 1).toString(),
        role: 'assistant',
        text: data.script_text || 'Response received.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        text: error instanceof Error ? error.message : 'Something went wrong.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, assistantMessage])
    } finally {
      setIsTyping(false)
    }

    setInput('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleGenerateClick = (prompt: string) => {
    setPendingPrompt(prompt)
    setShowPersonaSelector(true)
  }

  const handlePersonaSelect = (persona: 'mkbhd' | 'ijustine') => {
    router.push(`/generate?persona=${persona}&prompt=${encodeURIComponent(pendingPrompt)}`)
  }

  const latestPrompt = [...messages].reverse().find(message => message.role === 'user')?.text || input

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#1b2030_0%,_#0a0b11_45%,_#07080b_100%)] relative overflow-hidden">
      <FloatingBackground />
      
      <div className="relative z-10 container mx-auto px-4 py-8 h-screen flex flex-col">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-6"
        >
          <Link href="/">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="text-white hover:text-gray-300 transition-colors"
            >
              ← Back
            </motion.button>
          </Link>
          
          <h1 className="text-3xl font-bold text-white">Chat</h1>
          
          <div className="w-20" />
        </motion.div>

        {/* Chat Container */}
        <GlassCard className="flex-1 flex flex-col p-6 mb-6 overflow-hidden">
          {/* Messages */}
          <div ref={listRef} className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
            <AnimatePresence>
              {messages.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center text-gray-400 mt-20"
                >
                  <p className="text-xl mb-2">👋 Start a conversation</p>
                  <p className="text-sm">Ask me anything about tech!</p>
                </motion.div>
              ) : (
                messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.06 }}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[72%] p-4 rounded-2xl ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-[#6dd5ed] to-[#f7797d] text-white'
                          : 'glass-panel text-white border border-white/10'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.text}</p>
                      
                      {message.role === 'assistant' && (
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleGenerateClick(messages[index - 1]?.text || '')}
                          className="mt-3 px-4 py-2 bg-white/15 hover:bg-white/25 rounded-lg text-sm font-medium transition-colors"
                        >
                          Generate Video Response →
                        </motion.button>
                      )}
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>

            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="glass-panel p-4 rounded-2xl">
                  <motion.div
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="flex gap-2"
                  >
                    <div className="w-2 h-2 bg-white rounded-full" />
                    <div className="w-2 h-2 bg-white rounded-full" />
                    <div className="w-2 h-2 bg-white rounded-full" />
                  </motion.div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Input Box */}
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 px-4 py-3 bg-white/10 backdrop-blur-md border border-white/15 
                         rounded-xl text-white placeholder-gray-400 focus:outline-none 
                         focus:border-[#6dd5ed] transition-colors"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="px-6 py-3 bg-gradient-to-r from-[#6dd5ed] to-[#f7797d] 
                         rounded-xl text-white font-medium disabled:opacity-50 
                         disabled:cursor-not-allowed transition-all shadow-lg"
            >
              Send
            </motion.button>
          </div>

          <div className="mt-4 flex flex-col md:flex-row gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                router.push(`/generate?persona=mkbhd&prompt=${encodeURIComponent(latestPrompt)}`)
              }}
              disabled={!latestPrompt.trim() || isTyping}
              className="flex-1 py-3 rounded-xl text-white font-semibold bg-gradient-to-r from-[#6dd5ed] to-[#8e9eab] disabled:opacity-50"
            >
              Generate as MKBHD
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                router.push(`/generate?persona=ijustine&prompt=${encodeURIComponent(latestPrompt)}`)
              }}
              disabled={!latestPrompt.trim() || isTyping}
              className="flex-1 py-3 rounded-xl text-white font-semibold bg-gradient-to-r from-[#f7797d] to-[#fbd786] disabled:opacity-50"
            >
              Generate as iJustine
            </motion.button>
          </div>
        </GlassCard>

        {/* Persona Selector Modal */}
        <AnimatePresence>
          {showPersonaSelector && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
              onClick={() => setShowPersonaSelector(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="max-w-2xl w-full mx-4"
              >
                <GlassCard className="p-8">
                  <h2 className="text-2xl font-bold text-white mb-6 text-center">
                    Choose a Persona
                  </h2>
                  <PersonaSelector onSelect={handlePersonaSelect} />
                  <button
                    onClick={() => setShowPersonaSelector(false)}
                    className="mt-4 w-full py-2 text-gray-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                </GlassCard>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}
