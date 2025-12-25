'use client'

import { useEffect, useRef, useState } from 'react'
import LoadingSpinner from './LoadingSpinner'

interface VideoPlayerProps {
  videoPath: string | null
  isGenerating: boolean
}

export default function VideoPlayer({ videoPath, isGenerating }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [videoError, setVideoError] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (videoPath && videoRef.current) {
      setIsLoading(true)
      setVideoError(false)
      
      // Reload video when path changes
      videoRef.current.load()
      
      videoRef.current.play().catch(err => {
        console.warn('Autoplay prevented:', err)
      })
    }
  }, [videoPath])

  const handleVideoLoaded = () => {
    setIsLoading(false)
    setVideoError(false)
  }

  const handleVideoError = () => {
    setIsLoading(false)
    setVideoError(true)
  }

  if (isGenerating) {
    return (
      <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
        <LoadingSpinner size="lg" message="Generating your video response..." />
        <div className="absolute bottom-4 text-center">
          <p className="text-sm text-gray-400 mt-2">This may take 30-90 seconds</p>
        </div>
      </div>
    )
  }

  if (!videoPath) {
    return (
      <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
        <div className="text-center text-gray-500">
          <svg
            className="mx-auto h-12 w-12 mb-3 opacity-50"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          <p className="text-sm">Video response will appear here</p>
        </div>
      </div>
    )
  }

  return (
    <div className="aspect-video bg-black rounded-lg overflow-hidden relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
          <LoadingSpinner size="md" message="Loading video..." />
        </div>
      )}
      
      {videoError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
          <div className="text-center text-red-400">
            <svg
              className="mx-auto h-12 w-12 mb-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <p>Failed to load video</p>
            <p className="text-sm mt-1">The video may not be ready yet</p>
          </div>
        </div>
      )}
      
      <video
        ref={videoRef}
        className="w-full h-full object-contain"
        controls
        autoPlay
        playsInline
        onLoadedData={handleVideoLoaded}
        onError={handleVideoError}
      >
        <source src={`${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '')}${videoPath}`} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>
  )
}
