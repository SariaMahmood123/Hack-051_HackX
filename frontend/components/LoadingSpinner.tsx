'use client'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  message?: string
}

export default function LoadingSpinner({ size = 'md', message }: LoadingSpinnerProps) {
  const sizes = {
    sm: 'h-6 w-6',
    md: 'h-12 w-12',
    lg: 'h-16 w-16'
  }

  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className={`${sizes[size]} border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin`}
      />
      {message && (
        <p className="text-gray-300 text-sm">{message}</p>
      )}
    </div>
  )
}
