import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'LUMEN - AI Video Chatbot',
  description: 'Generative AI platform for video-based conversational chatbots',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
