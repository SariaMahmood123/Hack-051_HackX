'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import FloatingBackground from '@/components/FloatingBackground'
import GlassCard from '@/components/GlassCard'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 relative overflow-hidden">
      <FloatingBackground />
      
      <div className="relative z-10 container mx-auto px-4 py-16">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-20 pt-20"
        >
          <motion.h1
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-7xl md:text-8xl font-bold text-white mb-6 tracking-tight"
          >
            LUMEN
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-2xl md:text-3xl text-gray-300 mb-4"
          >
            Conversational AI That Speaks and Shows
          </motion.p>
          
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="text-lg text-gray-400 max-w-2xl mx-auto"
          >
            Generate authentic video and audio responses with AI personas
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="mt-12"
          >
            <Link href="/chat">
              <motion.button
                whileHover={{ scale: 1.05, boxShadow: '0 0 40px rgba(99, 102, 241, 0.5)' }}
                whileTap={{ scale: 0.95 }}
                className="px-12 py-4 text-xl font-semibold text-white 
                           bg-gradient-to-r from-indigo-600 to-purple-600 
                           rounded-full shadow-2xl hover:shadow-indigo-500/50 
                           transition-all duration-300"
              >
                Start Chatting →
              </motion.button>
            </Link>
          </motion.div>
        </motion.div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-20">
          {[
            {
              title: 'Intelligent Conversations',
              body: 'Powered by Gemini 2.0 Flash for natural, contextual responses',
              icon: '🧠'
            },
            {
              title: 'Authentic Audio',
              body: 'XTTS v2 voice cloning creates realistic, expressive speech',
              icon: '🎙️'
            },
            {
              title: 'Living Video',
              body: 'SadTalker generates natural lip-sync and facial movements',
              icon: '🎬'
            }
          ].map((card, index) => (
            <GlassCard key={card.title} hover delay={0.2 + index * 0.2}>
              <div className="p-8">
                <div className="text-5xl mb-4">{card.icon}</div>
                <h3 className="text-2xl font-bold text-white mb-3">{card.title}</h3>
                <p className="text-gray-300">{card.body}</p>
              </div>
            </GlassCard>
          ))}
        </div>

        {/* Personas Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="max-w-4xl mx-auto"
        >
          <GlassCard delay={1}>
            <div className="p-12">
              <h2 className="text-3xl font-bold text-white text-center mb-8">
                Choose Your AI Persona
              </h2>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div className="text-center">
                  <div className="text-6xl mb-4">🎥</div>
                  <h3 className="text-2xl font-bold text-white mb-2">MKBHD</h3>
                  <p className="text-gray-300">
                    In-depth tech reviews with professional insights
                  </p>
                </div>

                <div className="text-center">
                  <div className="text-6xl mb-4">✨</div>
                  <h3 className="text-2xl font-bold text-white mb-2">iJustine</h3>
                  <p className="text-gray-300">
                    Energetic, fun takes on the latest tech
                  </p>
                </div>
              </div>
            </div>
          </GlassCard>
        </motion.div>

        {/* Footer */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1.2 }}
          className="text-center mt-20 text-gray-400"
        >
          <p>Built for HackX 2025 | Powered by Gemini, XTTS v2, and SadTalker</p>
        </motion.footer>
      </div>
    </main>
  )
}
