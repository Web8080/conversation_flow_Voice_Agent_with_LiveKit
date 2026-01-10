'use client'

import { useState } from 'react'

export default function InfoPanel() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        aria-label="Show system information"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        System Info
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 z-50">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 dark:text-white">System Architecture</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-3 text-sm">
              <div>
                <div className="font-medium text-gray-700 dark:text-gray-300 mb-1">Architecture</div>
                <div className="text-gray-600 dark:text-gray-400 text-xs">
                  Frontend → LiveKit → Python Agent → STT/LLM/TTS Pipeline
                </div>
              </div>
              
              <div>
                <div className="font-medium text-gray-700 dark:text-gray-300 mb-1">State Machine</div>
                <div className="text-gray-600 dark:text-gray-400 text-xs">
                  Greeting → Collect Info → Confirmation → Terminal
                </div>
              </div>
              
              <div>
                <div className="font-medium text-gray-700 dark:text-gray-300 mb-1">Design Approach</div>
                <div className="text-gray-600 dark:text-gray-400 text-xs">
                  Structured, deterministic flow with LLM-assisted understanding
                </div>
              </div>
              
              <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                <a
                  href="https://github.com/your-repo"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                >
                  View Documentation →
                </a>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

