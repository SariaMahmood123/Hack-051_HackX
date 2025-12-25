import ChatInterface from '@/components/ChatInterface'
import StatusIndicator from '@/components/StatusIndicator'
import SettingsPanel from '@/components/SettingsPanel'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8 relative">
          <div className="absolute top-0 right-0">
            <StatusIndicator />
          </div>
          
          <h1 className="text-5xl font-bold text-white mb-2 animate-fade-in">
            LUMEN
          </h1>
          <p className="text-gray-300 text-lg animate-fade-in" style={{ animationDelay: '0.1s' }}>
            AI-Powered Video Chatbot
          </p>
          <p className="text-gray-400 text-sm mt-2 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            Powered by Gemini 2.0 Flash, XTTS v2, and SadTalker
          </p>
        </header>
        
        <ChatInterface />
        
        <footer className="text-center mt-8 text-gray-400 text-sm">
          <p>Built for HackX 2025 | MVP Demo</p>
        </footer>
      </div>
      
      <SettingsPanel />
    </main>
  )
}

