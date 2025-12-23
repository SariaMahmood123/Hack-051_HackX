'use client'

import { useBackendHealth } from '@/lib/hooks'

export default function StatusIndicator() {
  const { isHealthy, loading, error } = useBackendHealth(10000) // Check every 10s

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
        <span>Connecting...</span>
      </div>
    )
  }

  if (!isHealthy || error) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-400">
        <div className="w-2 h-2 bg-red-500 rounded-full" />
        <span>Backend Offline</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 text-sm text-green-400">
      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
      <span>Connected</span>
    </div>
  )
}
