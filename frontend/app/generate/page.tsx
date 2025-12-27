'use client'

import { useMemo, useState, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSearchParams } from 'next/navigation'
import FloatingBackground from '@/components/FloatingBackground'
import GlassCard from '@/components/GlassCard'
import MediaPlayer from '@/components/MediaPlayer'
import LoadingOverlay from '@/components/LoadingOverlay'
import Link from 'next/link'

type MediaType = 'audio' | 'video'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
const SERVER_BASE_URL = API_BASE_URL.replace(/\/api\/?$/, '')

function resolveOutputUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  if (path.startsWith('/outputs')) return `${SERVER_BASE_URL}${path}`

  const normalized = path.replace(/\\/g, '/')
  const outputsIndex = normalized.toLowerCase().lastIndexOf('/outputs/')
  if (outputsIndex >= 0) {
    const relative = normalized.slice(outputsIndex)
    return `${SERVER_BASE_URL}${relative}`
  }

  return `${SERVER_BASE_URL}/outputs/${normalized.split('/').pop()}`
}

function GenerateContent() {
  const searchParams = useSearchParams()
  
  const persona = (searchParams.get('persona') || 'mkbhd') as 'mkbhd' | 'ijustine'
  const initialPrompt = searchParams.get('prompt') || ''
  
  const [prompt, setPrompt] = useState(initialPrompt)
  const [mediaType, setMediaType] = useState<MediaType>('video')
  const [isGenerating, setIsGenerating] = useState(false)
  const [loadingStage, setLoadingStage] = useState('')
  const [generatedMedia, setGeneratedMedia] = useState<{
    type: MediaType
    src: string
    script?: string
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const captionLines = useMemo(() => {
    if (!generatedMedia?.script) return []
    const matches = generatedMedia.script.match(/[^.!?]+[.!?]+|[^.!?]+$/g)
    return (matches || [])
      .map(line => line.trim())
      .filter(Boolean)
  }, [generatedMedia?.script])

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setIsGenerating(true)
    setError(null)
    setGeneratedMedia(null)

    try {
      if (mediaType === 'audio') {
        setLoadingStage('Generating script with Gemini...')
        
        const response = await fetch(`${API_BASE_URL}/generate/mkbhd`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            prompt,
            persona,
            max_tokens: 800
          })
        })

        if (!response.ok) {
          const detail = await response.json().catch(() => ({}))
          throw new Error(detail?.detail || 'Audio generation failed')
        }

        const data = await response.json()

        setLoadingStage('Synthesizing audio with XTTS v2...')

        setGeneratedMedia({
          type: 'audio',
          src: resolveOutputUrl(data.audio_path),
          script: data.script_text
        })
      } else {
        setLoadingStage('Generating script with Gemini...')
        
        const response = await fetch(`${API_BASE_URL}/generate/full`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            prompt,
            persona,
            max_tokens: 250,
            temperature: persona === 'ijustine' ? 0.8 : 0.7
          })
        })

        if (!response.ok) {
          const detail = await response.json().catch(() => ({}))
          throw new Error(detail?.detail || 'Video generation failed')
        }

        const data = await response.json()

        setLoadingStage('Rendering video with SadTalker...')

        setGeneratedMedia({
          type: 'video',
          src: resolveOutputUrl(data.video_path),
          script: data.script_text
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed. Please try again.')
    } finally {
      setIsGenerating(false)
      setLoadingStage('')
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#1a2030_0%,_#0a0b11_50%,_#07080b_100%)] relative overflow-hidden">
      <FloatingBackground />
      
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-6"
        >
          <Link href="/chat">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="text-white hover:text-gray-300 transition-colors"
            >
              ← Back to Chat
            </motion.button>
          </Link>
          
          <div className="text-center">
            <h1 className="text-3xl font-bold text-white">Generate</h1>
            <p className="text-gray-400 text-sm mt-1">
              {persona === 'mkbhd' ? '🎥 MKBHD Style' : '✨ iJustine Style'}
            </p>
          </div>
          
          <div className="w-32" />
        </motion.div>

        <div className="max-w-5xl mx-auto space-y-6">
          {/* Controls */}
          <GlassCard className="p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  What would you like to generate?
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Review the iPhone 16 Pro Max"
                  rows={3}
                  className="w-full px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 
                             rounded-xl text-white placeholder-gray-400 focus:outline-none 
                             focus:border-[#6dd5ed] transition-colors resize-none"
                />
              </div>

              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  Output Type
                </label>
                <div className="flex flex-col md:flex-row gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setMediaType('audio')}
                    className={`flex-1 py-3 rounded-xl font-medium transition-all ${
                      mediaType === 'audio'
                        ? 'bg-gradient-to-r from-[#6dd5ed] to-[#8e9eab] text-white'
                        : 'bg-white/10 text-gray-300 hover:bg-white/20'
                    }`}
                  >
                    🎙️ Audio Only
                  </motion.button>
                  
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setMediaType('video')}
                    className={`flex-1 py-3 rounded-xl font-medium transition-all ${
                      mediaType === 'video'
                        ? 'bg-gradient-to-r from-[#f7797d] to-[#fbd786] text-white'
                        : 'bg-white/10 text-gray-300 hover:bg-white/20'
                    }`}
                  >
                    🎬 Video + Audio
                  </motion.button>
                </div>
                {mediaType === 'audio' && persona === 'ijustine' && (
                  <p className="text-xs text-gray-400 mt-2">
                    Audio-only mode uses the MKBHD voice pipeline.
                  </p>
                )}
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim()}
                className="w-full py-4 bg-gradient-to-r from-[#6dd5ed] via-[#8e9eab] to-[#f7797d] 
                           rounded-xl text-white font-semibold text-lg
                           disabled:opacity-50 disabled:cursor-not-allowed 
                           transition-all shadow-lg"
              >
                {isGenerating ? 'Generating...' : 'Generate'}
              </motion.button>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-200"
                >
                  {error}
                </motion.div>
              )}
            </div>
          </GlassCard>

          {/* Generated Content */}
          <AnimatePresence>
            {generatedMedia && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <GlassCard className="p-6">
                  <div className="flex flex-col lg:flex-row gap-6">
                    <div className="flex-1">
                      <h2 className="text-2xl font-bold text-white mb-4">
                        Generated {generatedMedia.type === 'audio' ? 'Audio' : 'Video'}
                      </h2>
                      <MediaPlayer
                        type={generatedMedia.type}
                        src={generatedMedia.src}
                        autoPlay={true}
                      />
                    </div>

                    {generatedMedia.type === 'video' && (
                      <div className="w-full lg:w-[320px]">
                        <div className="glass-panel rounded-2xl p-4 h-full">
                          <h3 className="text-white font-semibold mb-3">Live Captions</h3>
                          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
                            {captionLines.length === 0 ? (
                              <p className="text-gray-400 text-sm">No captions available.</p>
                            ) : (
                              captionLines.map((line, index) => (
                                <div key={`${line}-${index}`} className="text-gray-200 text-sm leading-relaxed">
                                  {line}
                                </div>
                              ))
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {generatedMedia.type === 'audio' && generatedMedia.script && (
                    <div className="mt-6 p-4 bg-white/5 rounded-xl">
                      <h3 className="text-white font-semibold mb-2">Script:</h3>
                      <p className="text-gray-300 whitespace-pre-wrap">{generatedMedia.script}</p>
                    </div>
                  )}
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <AnimatePresence>
        {isGenerating && <LoadingOverlay stage={loadingStage} />}
      </AnimatePresence>
    </main>
  )
}

export default function GeneratePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_#1a2030_0%,_#0a0b11_50%,_#07080b_100%)] flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    }>
      <GenerateContent />
    </Suspense>
  )
}
