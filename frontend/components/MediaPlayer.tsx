'use client'

import { motion } from 'framer-motion'
import { useState, useRef, useEffect } from 'react'

interface MediaPlayerProps {
  type: 'audio' | 'video'
  src: string
  autoPlay?: boolean
}

export default function MediaPlayer({ type, src, autoPlay = false }: MediaPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(autoPlay)
  const [progress, setProgress] = useState(0)
  const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement>(null)

  useEffect(() => {
    const media = mediaRef.current
    if (!media) return

    const updateProgress = () => {
      if (!media.duration || Number.isNaN(media.duration)) return
      const nextProgress = (media.currentTime / media.duration) * 100
      setProgress(nextProgress)
    }

    const onPlay = () => setIsPlaying(true)
    const onPause = () => setIsPlaying(false)

    media.addEventListener('timeupdate', updateProgress)
    media.addEventListener('play', onPlay)
    media.addEventListener('pause', onPause)

    return () => {
      media.removeEventListener('timeupdate', updateProgress)
      media.removeEventListener('play', onPlay)
      media.removeEventListener('pause', onPause)
    }
  }, [])

  const togglePlay = () => {
    if (mediaRef.current) {
      if (isPlaying) {
        mediaRef.current.pause()
      } else {
        mediaRef.current.play()
      }
    }
  }

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!mediaRef.current) return
    const rect = e.currentTarget.getBoundingClientRect()
    const percent = (e.clientX - rect.left) / rect.width
    mediaRef.current.currentTime = percent * mediaRef.current.duration
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full"
    >
      {type === 'video' ? (
        <div className="glass-panel rounded-3xl p-3">
          <video
            ref={mediaRef as React.RefObject<HTMLVideoElement>}
            src={src}
            autoPlay={autoPlay}
            controls
            className="w-full rounded-2xl shadow-2xl bg-black"
          />
        </div>
      ) : (
        <div className="glass-panel rounded-3xl p-6">
          <audio ref={mediaRef as React.RefObject<HTMLAudioElement>} src={src} autoPlay={autoPlay} />
          
          <div className="flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={togglePlay}
              className="w-12 h-12 rounded-full bg-white/15 flex items-center justify-center
                         hover:bg-white/25 transition-colors shadow-lg"
            >
              {isPlaying ? (
                <span className="text-2xl">⏸</span>
              ) : (
                <span className="text-2xl">▶</span>
              )}
            </motion.button>

            <div className="flex-1">
              <div 
                onClick={handleSeek}
                className="h-2 bg-white/15 rounded-full cursor-pointer overflow-hidden"
              >
                <motion.div
                  style={{ width: `${progress}%` }}
                  className="h-full bg-gradient-to-r from-[#6dd5ed] to-[#f7797d]"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  )
}
