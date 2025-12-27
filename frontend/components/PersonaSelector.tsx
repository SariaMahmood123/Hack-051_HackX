'use client'

import { motion } from 'framer-motion'

interface PersonaSelectorProps {
  onSelect: (persona: 'mkbhd' | 'ijustine') => void
  disabled?: boolean
}

export default function PersonaSelector({ onSelect, disabled = false }: PersonaSelectorProps) {
  return (
    <div className="flex gap-4">
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        disabled={disabled}
        onClick={() => onSelect('mkbhd')}
        className="flex-1 p-6 glass-panel rounded-2xl border border-white/10
                   hover:border-white/30 hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <div className="text-center">
          <div className="text-4xl mb-2">🎥</div>
          <h3 className="text-xl font-bold text-white mb-1">MKBHD</h3>
          <p className="text-sm text-gray-300">Tech reviews & deep dives</p>
        </div>
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        disabled={disabled}
        onClick={() => onSelect('ijustine')}
        className="flex-1 p-6 glass-panel rounded-2xl border border-white/10
                   hover:border-white/30 hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <div className="text-center">
          <div className="text-4xl mb-2">✨</div>
          <h3 className="text-xl font-bold text-white mb-1">iJustine</h3>
          <p className="text-sm text-gray-300">Fun & energetic content</p>
        </div>
      </motion.button>
    </div>
  )
}
