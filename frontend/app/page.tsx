'use client'

import VoiceAgentUI from '../components/VoiceAgentUI'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <VoiceAgentUI />
        
        {/* Footer with Technical Details */}
        <div className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>Voice Agent - LiveKit Integration | Stage 1 & Stage 2 Implementation</p>
          <p className="mt-1 text-xs">
            Demonstrating structured approach: State Machine, Error Handling, Clear Architecture
          </p>
        </div>
      </div>
    </main>
  )
}

