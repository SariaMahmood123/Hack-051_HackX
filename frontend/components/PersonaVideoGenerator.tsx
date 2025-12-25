'use client'

import { useState } from 'react'
import { Loader2, Sparkles, Video } from 'lucide-react'
import { generatePersonaVideo } from '@/lib/api'
import type { PersonaVideoRequest } from '@/lib/api'

type Persona = 'ijustine' | 'mkbhd'

interface PersonaVideoGeneratorProps {
  onVideoGenerated?: (videoUrl: string) => void
}

export default function PersonaVideoGenerator({ onVideoGenerated }: PersonaVideoGeneratorProps) {
  const [persona, setPersona] = useState<Persona>('mkbhd')
  const [prompt, setPrompt] = useState('')
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<string>('')
  const [processingTime, setProcessingTime] = useState<number | null>(null)

  const generateVideo = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setLoading(true)
    setError(null)
    setVideoUrl(null)
    setProgress('Starting pipeline...')
    setProcessingTime(null)

    try {
      const request: PersonaVideoRequest = {
        prompt: prompt.trim(),
        persona,
        temperature: persona === 'ijustine' ? 0.8 : 0.7,
        max_tokens: 300
      }

      const result = await generatePersonaVideo(request)
      
      setVideoUrl(result.video_url)
      setProcessingTime(result.processing_time || null)
      setProgress('✅ Video generated successfully!')
      
      if (onVideoGenerated) {
        onVideoGenerated(result.video_url)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setError(`Video generation failed: ${message}`)
      setProgress('')
    } finally {
      setLoading(false)
    }
  }

  const personaInfo = {
    mkbhd: {
      name: 'MKBHD',
      fullName: 'Marques Brownlee',
      style: 'Professional & Measured',
      color: 'from-red-500 to-orange-500',
      description: 'Smooth, deliberate tech reviews with strategic pauses'
    },
    ijustine: {
      name: 'iJustine',
      fullName: 'Justine Ezarik',
      style: 'Energetic & Enthusiastic',
      color: 'from-pink-500 to-purple-500',
      description: 'Fast-paced, expressive reactions with lots of emphasis'
    }
  }

  const currentPersona = personaInfo[persona]

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <Video className="w-8 h-8" />
          Persona Video Generator
        </h1>
        <p className="text-gray-600">
          Generate AI-powered talking head videos with persona-specific styles
        </p>
      </div>

      {/* Persona Selector */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Select Persona
        </label>
        <div className="grid grid-cols-2 gap-4">
          {(Object.keys(personaInfo) as Persona[]).map((p) => {
            const info = personaInfo[p]
            const isSelected = persona === p
            return (
              <button
                key={p}
                onClick={() => setPersona(p)}
                disabled={loading}
                className={`
                  p-4 rounded-lg border-2 transition-all duration-200
                  ${isSelected 
                    ? 'border-blue-500 bg-blue-50 shadow-md' 
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                  }
                  ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <div className={`inline-block px-3 py-1 rounded-full bg-gradient-to-r ${info.color} text-white text-sm font-semibold mb-2`}>
                  {info.name}
                </div>
                <p className="text-xs text-gray-600 font-medium">{info.fullName}</p>
                <p className="text-xs text-gray-500 mt-1">{info.style}</p>
                <p className="text-xs text-gray-400 mt-2">{info.description}</p>
              </button>
            )
          })}
        </div>
      </div>

      {/* Prompt Input */}
      <div className="space-y-2">
        <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
          What should {currentPersona.name} talk about?
        </label>
        <textarea
          id="prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={loading}
          placeholder={`E.g., "Explain why the new M4 Mac Mini is the best value" or "Tell me about the latest iPhone features"`}
          className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
        <p className="text-xs text-gray-500">
          {prompt.length} / 2000 characters
        </p>
      </div>

      {/* Generate Button */}
      <button
        onClick={generateVideo}
        disabled={loading || !prompt.trim()}
        className={`
          w-full py-4 rounded-lg font-semibold text-white transition-all duration-200
          flex items-center justify-center gap-2
          ${loading || !prompt.trim()
            ? 'bg-gray-400 cursor-not-allowed'
            : `bg-gradient-to-r ${currentPersona.color} hover:opacity-90 hover:shadow-lg`
          }
        `}
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating Video...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Generate {currentPersona.name} Video
          </>
        )}
      </button>

      {/* Progress */}
      {loading && progress && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">{progress}</p>
          <p className="text-xs text-blue-600 mt-1">
            This may take 3-7 minutes. Please wait...
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800 font-medium">Error</p>
          <p className="text-sm text-red-600 mt-1">{error}</p>
        </div>
      )}

      {/* Video Player */}
      {videoUrl && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Generated Video</h3>
            {processingTime && (
              <span className="text-sm text-gray-500">
                Processed in {processingTime.toFixed(1)}s
              </span>
            )}
          </div>
          <video
            src={videoUrl}
            controls
            autoPlay
            className="w-full rounded-lg shadow-lg border border-gray-200"
          >
            Your browser does not support the video tag.
          </video>
          <div className="flex gap-2">
            <a
              href={videoUrl}
              download
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
            >
              Download Video
            </a>
            <button
              onClick={() => {
                setVideoUrl(null)
                setPrompt('')
                setProgress('')
              }}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
            >
              Generate Another
            </button>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">How it works:</h4>
        <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
          <li>Gemini generates a persona-specific script with emphasis & pause markers</li>
          <li>XTTS synthesizes audio matching the selected voice style</li>
          <li>SadTalker creates a talking head video with Motion Governor for natural motion</li>
          <li>GFPGAN enhances facial details for higher quality output</li>
        </ol>
      </div>
    </div>
  )
}
