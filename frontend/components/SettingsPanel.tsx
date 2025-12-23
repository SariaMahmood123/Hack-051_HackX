'use client'

import { useState } from 'react'
import { useBackendHealth } from '@/lib/hooks'

export default function SettingsPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const { health } = useBackendHealth()
  const [temperature, setTemperature] = useState(0.7)

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed top-4 right-4 bg-gray-800 text-white p-3 rounded-lg hover:bg-gray-700 transition-colors z-40"
        title="Settings"
      >
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>
    )
  }

  return (
    <div className="fixed top-4 right-4 bg-gray-800 text-white p-6 rounded-lg shadow-2xl w-80 z-40">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold">Settings</h3>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-white"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {/* Backend Status */}
        <div className="border-b border-gray-700 pb-3">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Backend Status</h4>
          {health ? (
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Status:</span>
                <span className="text-green-400">{health.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">GPU:</span>
                <span>{health.gpu_available ? '✓ Available' : '✗ Not Available'}</span>
              </div>
              {health.gpu_info && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Device:</span>
                  <span className="text-xs">{health.gpu_info.device_name.split(' ').slice(-2).join(' ')}</span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-red-400">Backend offline</p>
          )}
        </div>

        {/* Temperature Control */}
        <div>
          <label className="text-sm font-medium text-gray-400 block mb-2">
            Temperature: {temperature.toFixed(2)}
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>More Focused</span>
            <span>More Creative</span>
          </div>
        </div>

        {/* Info */}
        <div className="text-xs text-gray-500 pt-3 border-t border-gray-700">
          <p>Temperature controls response creativity.</p>
          <p className="mt-1">Higher values = more random responses.</p>
        </div>
      </div>
    </div>
  )
}
