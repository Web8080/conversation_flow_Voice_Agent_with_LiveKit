'use client'

interface StateProgressIndicatorProps {
  currentState: string | null
  states?: Array<{ id: string; label: string; completed: boolean }>
}

export default function StateProgressIndicator({ 
  currentState, 
  states 
}: StateProgressIndicatorProps) {
  const defaultStates = [
    { id: 'greeting', label: 'Greeting', completed: false },
    { id: 'collect_date', label: 'Date', completed: false },
    { id: 'collect_time', label: 'Time', completed: false },
    { id: 'confirmation', label: 'Confirm', completed: false },
    { id: 'terminal', label: 'Complete', completed: false },
  ]

  const displayStates = states || defaultStates
  
  // Mark states as completed based on current state
  const stateOrder = ['greeting', 'collect_date', 'collect_time', 'confirmation', 'terminal']
  const currentIndex = currentState ? stateOrder.indexOf(currentState) : -1
  
  const statesWithStatus = displayStates.map((state, index) => {
    const stateIndex = stateOrder.indexOf(state.id)
    return {
      ...state,
      completed: stateIndex >= 0 && currentIndex >= 0 && stateIndex < currentIndex,
      current: state.id === currentState,
    }
  })

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Conversation Progress
        </h3>
        {currentState && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Current: {currentState.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </span>
        )}
      </div>
      <div className="flex items-center justify-between relative">
        {/* Connection line */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200 dark:bg-gray-700 -z-10" />
        
        {statesWithStatus.map((state, index) => (
          <div key={state.id} className="flex flex-col items-center flex-1 relative">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm border-2 transition-all ${
                state.completed
                  ? 'bg-green-500 border-green-500 text-white'
                  : state.current
                  ? 'bg-blue-500 border-blue-500 text-white ring-4 ring-blue-200 dark:ring-blue-800'
                  : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-400 dark:text-gray-500'
              }`}
            >
              {state.completed ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span
              className={`text-xs mt-2 font-medium text-center ${
                state.current
                  ? 'text-blue-600 dark:text-blue-400'
                  : state.completed
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              {state.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

