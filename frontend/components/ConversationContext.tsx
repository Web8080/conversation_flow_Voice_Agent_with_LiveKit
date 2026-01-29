'use client'

interface ConversationContextProps {
  slots: Record<string, any>
  currentState: string | null
}

export default function ConversationContext({ slots, currentState }: ConversationContextProps) {
  const slotLabels: Record<string, string> = {
    name: 'Name',
    date: 'Appointment Date',
    time: 'Appointment Time',
    type: 'Appointment Type',
    contact: 'Contact Information',
  }

  const hasSlots = Object.keys(slots).length > 0

  if (!hasSlots && !currentState) return null

  return (
    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 p-4 mb-4">
      <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-3">
        Collected Information
      </h3>
      {hasSlots ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(slots).map(([key, value]) => (
            <div key={key} className="flex items-start gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full mt-1.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-blue-800 dark:text-blue-200">
                  {slotLabels[key] || key}
                </div>
                <div className="text-sm text-blue-900 dark:text-blue-100 font-semibold truncate">
                  {String(value)}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-sm text-blue-700 dark:text-blue-300">
          <p>No information collected yet. The agent will guide you through collecting:</p>
          <ul className="list-disc list-inside mt-2 space-y-1 text-xs">
            <li>Your name</li>
            <li>Preferred appointment date</li>
            <li>Preferred appointment time</li>
          </ul>
        </div>
      )}
    </div>
  )
}


