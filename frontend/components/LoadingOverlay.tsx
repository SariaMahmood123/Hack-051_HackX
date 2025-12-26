'use client'

import { motion } from 'framer-motion'

interface LoadingOverlayProps {
  stage?: string
  progress?: number
}

export default function LoadingOverlay({ stage = 'Processing...', progress }: LoadingOverlayProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
    >
      <div className="text-center glass-bright rounded-3xl px-8 py-10 w-[min(92vw,420px)]">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 mx-auto mb-4 border-4 border-white/20 border-t-white rounded-full"
        />
        
        <motion.p
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="text-white text-lg font-medium"
        >
          {stage}
        </motion.p>

        {progress !== undefined && (
          <div className="mt-4 w-64 h-2 bg-white/20 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
              className="h-full bg-gradient-to-r from-[#6dd5ed] to-[#f7797d]"
            />
          </div>
        )}
      </div>
    </motion.div>
  )
}
