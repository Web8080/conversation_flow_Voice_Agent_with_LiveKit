'use client'

interface SystemStatusProps {
  services: {
    stt: 'operational' | 'degraded' | 'down'
    llm: 'operational' | 'degraded' | 'down'
    tts: 'operational' | 'degraded' | 'down'
    livekit: 'operational' | 'degraded' | 'down'
  }
  latency?: {
    stt?: number
    llm?: number
    tts?: number
    total?: number
  }
}

export default function SystemStatus({ services, latency }: SystemStatusProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'down':
        return 'bg-red-500'
      default:
        return 'bg-gray-400'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'operational':
        return 'Operational'
      case 'degraded':
        return 'Degraded'
      case 'down':
        return 'Down'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
        System Status
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.entries(services).map(([service, status]) => (
          <div key={service} className="flex flex-col">
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2 h-2 rounded-full ${getStatusColor(status)}`} />
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">
                {service}
              </span>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-500">
              {getStatusLabel(status)}
            </span>
            {latency && latency[service as keyof typeof latency] && (
              <span className="text-xs text-gray-400 dark:text-gray-600 mt-1">
                {latency[service as keyof typeof latency]}ms
              </span>
            )}
          </div>
        ))}
      </div>
      {latency?.total && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-600 dark:text-gray-400">Total Latency</span>
            <span className={`text-sm font-semibold ${
              latency.total < 2000 ? 'text-green-600' : latency.total < 3000 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {latency.total}ms
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

