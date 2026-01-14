'use client'

import { useState, useEffect, useRef } from 'react'
import { Room, RoomEvent, RemoteParticipant, RemoteTrack, Track } from 'livekit-client'
import StateProgressIndicator from './StateProgressIndicator'
import SystemStatus from './SystemStatus'
import InfoPanel from './InfoPanel'
import ConversationContext from './ConversationContext'

interface Message {
  role: 'user' | 'agent'
  text: string
  timestamp: Date
  state?: string
  metadata?: Record<string, any>
}

export default function VoiceAgentUI() {
  const [room, setRoom] = useState<Room | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [roomName, setRoomName] = useState('voice-agent-room')
  const [messages, setMessages] = useState<Message[]>([])
  const [micEnabled, setMicEnabled] = useState(true)
  const [speakerEnabled, setSpeakerEnabled] = useState(true)
  const [currentState, setCurrentState] = useState<string | null>(null)
  const [collectedSlots, setCollectedSlots] = useState<Record<string, any>>({})
  const [systemStatus, setSystemStatus] = useState({
    stt: 'operational' as const,
    llm: 'operational' as const,
    tts: 'operational' as const,
    livekit: 'operational' as const,
  })
  const [latency, setLatency] = useState<{ stt?: number; llm?: number; tts?: number; total?: number }>({})
  const audioRef = useRef<HTMLAudioElement>(null)

  const connectToRoom = async () => {
    if (isConnecting || isConnected) return

    setIsConnecting(true)
    try {
      const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || 'wss://your-project.livekit.cloud'
      
      const token = await fetch('/api/livekit-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_name: roomName }),
      }).then(res => res.json()).then(data => data.token)

      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
      })

      newRoom.on(RoomEvent.TrackSubscribed, (track: RemoteTrack, publication: any, participant: RemoteParticipant) => {
        // Log all track subscriptions for debugging
        console.log('Track subscribed:', {
          kind: track.kind,
          participantIdentity: participant.identity,
          participantName: participant.name,
          trackName: publication.trackName,
        })
        
        // Check if this is an audio track from the agent
        // Agent joins with identity like "agent-{job_id}" (e.g., "agent-AJ_Fus3FPcfa7e8")
        const isAgent = 
          participant.identity === 'agent' ||
          participant.identity === 'appointment-scheduler' ||
          participant.identity?.startsWith('agent-') || // Match "agent-{job_id}" pattern
          participant.name?.toLowerCase().includes('agent') ||
          participant.name?.toLowerCase().includes('appointment') ||
          participant.metadata?.toLowerCase().includes('agent')
        
        if (track.kind === Track.Kind.Audio && isAgent) {
          track.attach(audioRef.current!)
          addMessage('agent', `Agent audio connected (${participant.identity})`, 'greeting')
          setCurrentState('greeting')
        }
      })

      newRoom.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
        track.detach()
      })

      newRoom.on(RoomEvent.Disconnected, () => {
        setIsConnected(false)
        setCurrentState(null)
        addMessage('agent', 'Disconnected from room')
      })

      newRoom.on(RoomEvent.ParticipantConnected, (participant: RemoteParticipant) => {
        // Log all participants for debugging
        const participantData = {
          identity: participant.identity,
          name: participant.name,
          metadata: participant.metadata,
          trackCount: participant.trackPublications.size,
          audioTracks: Array.from(participant.trackPublications.values()).filter(p => p.kind === 'audio').length,
        }
        console.log('Participant connected:', participantData)
        
        // #region debug log
        fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:89',message:'ParticipantConnected event',data:participantData,timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
        // #endregion
        
        // Check if this is the agent (by identity, name, or metadata)
        // Agent joins with identity like "agent-{job_id}" (e.g., "agent-AJ_Fus3FPcfa7e8")
        const isAgent = 
          participant.identity === 'agent' ||
          participant.identity === 'appointment-scheduler' ||
          participant.identity?.startsWith('agent-') || // Match "agent-{job_id}" pattern
          participant.name?.toLowerCase().includes('agent') ||
          participant.name?.toLowerCase().includes('appointment') ||
          participant.metadata?.toLowerCase().includes('agent')
        
        // #region debug log
        fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:105',message:'Agent detection check',data:{isAgent,identity:participant.identity,name:participant.name,metadata:participant.metadata},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
        // #endregion
        
        if (isAgent) {
          addMessage('agent', `Agent joined the room (${participant.identity})`, 'greeting')
          setCurrentState('greeting')
        } else {
          // If participant joins after user connects, it might be the agent (anonymous identity)
          // Check if participant has audio tracks (agent will publish audio)
          const hasAudioTracks = Array.from(participant.trackPublications.values()).some(
            pub => pub.kind === 'audio'
          )
          // #region debug log
          fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:115',message:'Checking audio tracks for anonymous participant',data:{hasAudioTracks,identity:participant.identity},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
          // #endregion
          if (hasAudioTracks) {
            addMessage('agent', `Agent joined the room (${participant.identity})`, 'greeting')
            setCurrentState('greeting')
          } else {
            addMessage('agent', `User ${participant.identity} joined`)
          }
        }
      })
      
      // Listen for data messages (state updates from agent)
      newRoom.on(RoomEvent.DataReceived, (payload: Uint8Array, participant?: RemoteParticipant) => {
        try {
          const data = JSON.parse(new TextDecoder().decode(payload))
          if (data.type === 'state_update') {
            setCurrentState(data.state)
          }
          if (data.type === 'message') {
            addMessage('agent', data.text, data.state)
          }
          if (data.type === 'system_status') {
            setSystemStatus(data.status)
          }
          if (data.type === 'latency') {
            setLatency(data.latency)
          }
          if (data.type === 'slot_update') {
            setCollectedSlots(prev => ({ ...prev, ...data.slots }))
          }
        } catch (e) {
          console.error('Failed to parse data message', e)
        }
      })

      await newRoom.connect(livekitUrl, token)
      
      // Enable microphone after connection
      if (micEnabled) {
        await newRoom.localParticipant.setMicrophoneEnabled(true)
      }

      // Track initial participants before dispatch
      const initialParticipantIds = new Set(
        Array.from(newRoom.remoteParticipants.keys())
      )
      console.log('Initial participants:', Array.from(initialParticipantIds))
      
      // Track if agent has been detected
      let agentDetected = false

      setRoom(newRoom)
      setIsConnected(true)
      addMessage('agent', 'Connected to room successfully. Agent will join automatically...')
      
      // Note: Agent auto-joins when agent_name is removed from WorkerOptions
      // No need to dispatch manually - agent will join automatically when user connects
      
      // Keep dispatch code commented out as fallback if auto-join doesn't work
      /*
      // Dispatch agent after connecting
      try {
        // #region debug log
        fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:168',message:'Calling dispatch API',data:{room_name:roomName,initialParticipantCount:initialParticipantIds.size},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        
        const dispatchResponse = await fetch('/api/dispatch-agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ room_name: roomName }),
        })
        
        // #region debug log
        fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:175',message:'Dispatch API response received',data:{status:dispatchResponse.status,ok:dispatchResponse.ok},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        
        const dispatchResult = await dispatchResponse.json()
        
        // Log detailed LiveKit API response for debugging
        console.log('[FRONTEND] Dispatch API response:', dispatchResult)
        if (dispatchResult.livekit_response) {
          console.log('[FRONTEND] LiveKit API details:', {
            status: dispatchResult.livekit_response.status,
            body: dispatchResult.livekit_response.body,
            contentType: dispatchResult.livekit_response.contentType,
            parsed: dispatchResult.livekit_response.parsed,
          })
          console.log('[FRONTEND] Dispatch request sent:', dispatchResult.dispatch_request)
        }
        
        // #region debug log
        fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:180',message:'Dispatch result parsed',data:dispatchResult,timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        
        if (dispatchResult.success) {
          addMessage('agent', 'Agent dispatch requested. Waiting for agent to join...')
          
          // #region debug log
          fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:203',message:'Dispatch successful, starting agent polling',data:{roomName,initialParticipantCount:initialParticipantIds.size,dispatchResult},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          
          // Monitor for new participants after dispatch (agent should be the only one)
          let checkCount = 0
          const checkForAgent = setInterval(() => {
            checkCount++
            const currentParticipants = Array.from(newRoom.remoteParticipants.keys())
            const participantDetails = currentParticipants.map(id => {
              const p = newRoom.remoteParticipants.get(id)
              return p ? {id, identity: p.identity, name: p.name, metadata: p.metadata} : null
            }).filter(Boolean)
            const newParticipants = currentParticipants.filter(
              id => !initialParticipantIds.has(id)
            )
            
            // #region debug log
            fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:214',message:'Polling for agent',data:{checkCount,currentParticipantCount:currentParticipants.length,newParticipantCount:newParticipants.length,newParticipants,participantDetails,agentDetected},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
            // #endregion
            
            if (newParticipants.length > 0 && !agentDetected) {
              console.log('New participants detected after dispatch:', newParticipants)
              newParticipants.forEach(participantId => {
                const participant = newRoom.remoteParticipants.get(participantId)
                if (participant && !agentDetected) {
                  // #region debug log
                  fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:225',message:'New participant detected in polling',data:{participantId,identity:participant.identity,name:participant.name,metadata:participant.metadata},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
                  // #endregion
                  
                  // Check if this is the agent (agent joins with identity like "agent-{job_id}")
                  const isAgent = 
                    participant.identity === 'agent' ||
                    participant.identity === 'appointment-scheduler' ||
                    participant.identity?.startsWith('agent-') || // Match "agent-{job_id}" pattern
                    participant.name?.toLowerCase().includes('agent') ||
                    participant.name?.toLowerCase().includes('appointment') ||
                    participant.metadata?.toLowerCase().includes('agent')
                  
                  // #region debug log
                  fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:235',message:'Agent detection check in polling',data:{isAgent,identity:participant.identity,name:participant.name},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
                  // #endregion
                  
                  // Any new participant after dispatch is likely the agent, or if identity starts with "agent-"
                  if (isAgent || newParticipants.length === 1) {
                    agentDetected = true
                    clearInterval(checkForAgent)
                    addMessage('agent', `Agent joined the room (${participant.identity})`, 'greeting')
                    setCurrentState('greeting')
                  }
                }
              })
            }
          }, 1000) // Check every second
          
          // Stop checking after 30 seconds
          setTimeout(() => {
            clearInterval(checkForAgent)
            if (!agentDetected) {
              // #region debug log
              fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:214',message:'Agent detection timeout',data:{checkCount,agentDetected,currentParticipants:Array.from(newRoom.remoteParticipants.keys())},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
              // #endregion
              addMessage('agent', 'Still waiting for agent to join. Check browser console for details.')
            }
          }, 30000)
        } else {
          // #region debug log
          fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:220',message:'Dispatch failed',data:dispatchResult,timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
          // #endregion
          addMessage('agent', `Agent dispatch failed: ${dispatchResult.error || 'Unknown error'}`)
        }
      } catch (error) {
        // #region debug log
        fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'VoiceAgentUI.tsx:225',message:'Dispatch exception',data:{error:error instanceof Error ? error.message : String(error)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        console.error('Failed to dispatch agent:', error)
        addMessage('agent', 'Failed to dispatch agent. Agent may need to be configured in dashboard.')
      }
      */
      
      // Agent should auto-join now (no dispatch needed)
      // Monitor for agent joining automatically
      let agentDetectedAuto = false
      const checkForAgentAuto = setInterval(() => {
        const currentParticipants = Array.from(newRoom.remoteParticipants.keys())
        const newParticipants = currentParticipants.filter(
          id => !initialParticipantIds.has(id)
        )
        
        if (newParticipants.length > 0 && !agentDetectedAuto) {
          newParticipants.forEach(participantId => {
            const participant = newRoom.remoteParticipants.get(participantId)
            if (participant) {
              // Agent joins with identity like "agent-{job_id}" or just "agent"
              const isAgent = 
                participant.identity === 'agent' ||
                participant.identity?.startsWith('agent-') ||
                participant.name?.toLowerCase().includes('agent')
              
              if (isAgent || newParticipants.length === 1) {
                agentDetectedAuto = true
                clearInterval(checkForAgentAuto)
                addMessage('agent', `Agent joined the room automatically (${participant.identity})`, 'greeting')
                setCurrentState('greeting')
              }
            }
          })
        }
      }, 1000)
      
      // Stop checking after 30 seconds
      setTimeout(() => {
        clearInterval(checkForAgentAuto)
        if (!agentDetectedAuto) {
          addMessage('agent', 'Still waiting for agent to join. Check agent logs.')
        }
      }, 30000)
    } catch (error) {
      console.error('Failed to connect:', error)
      addMessage('agent', `Connection failed: ${error}`)
    } finally {
      setIsConnecting(false)
    }
  }

  const disconnectFromRoom = async () => {
    if (room) {
      room.disconnect()
      setRoom(null)
      setIsConnected(false)
      setMessages([])
      setCurrentState(null)
    }
  }

  const toggleMicrophone = async () => {
    if (!room) return
    
    if (micEnabled) {
      await room.localParticipant.setMicrophoneEnabled(false)
      setMicEnabled(false)
    } else {
      await room.localParticipant.setMicrophoneEnabled(true)
      setMicEnabled(true)
    }
  }

  const addMessage = (role: 'user' | 'agent', text: string, state?: string, metadata?: Record<string, any>) => {
    setMessages(prev => [...prev, { role, text, timestamp: new Date(), state, metadata }])
    if (state) {
      setCurrentState(state)
    }
  }
  
  const handleRestart = () => {
    if (room) {
      room.disconnect()
    }
    setMessages([])
    setCurrentState(null)
    setCollectedSlots({})
    setIsConnected(false)
    setRoom(null)
  }
  
  const handleEndConversation = () => {
    if (room) {
      room.disconnect()
    }
    setCurrentState('terminal')
    addMessage('agent', 'Conversation ended. Thank you!', 'terminal')
  }

  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect()
      }
    }
  }, [room])

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Voice Agent</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Appointment Scheduling Assistant
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <InfoPanel />
          </div>
        </div>
      </div>

      {/* System Status */}
      {isConnected && (
        <SystemStatus services={systemStatus} latency={latency} />
      )}

      {/* Main Content Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
        {/* Connection Panel */}
        <div className="mb-6 pb-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-col md:flex-row gap-4 items-end mb-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                LiveKit Room Name
              </label>
              <input
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                disabled={isConnected}
                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
                placeholder="voice-agent-room"
              />
            </div>
            <button
              onClick={isConnected ? disconnectFromRoom : connectToRoom}
              disabled={isConnecting}
              className={`px-6 py-2.5 rounded-lg font-medium transition-colors whitespace-nowrap ${
                isConnected
                  ? 'bg-red-500 hover:bg-red-600 text-white'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isConnecting ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Connecting...
                </span>
              ) : isConnected ? (
                'Disconnect'
              ) : (
                'Connect to Room'
              )}
            </button>
          </div>

          {/* Connection Info */}
          {isConnected && (
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center gap-2">
                <span className="font-medium">Participants:</span>
                <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                  {room?.remoteParticipants.size || 0} + You
                </span>
              </div>
              {roomName && (
                <div className="flex items-center gap-2">
                  <span className="font-medium">Room:</span>
                  <code className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">{roomName}</code>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Conversation Context - Shows collected slots */}
        {isConnected && (currentState || Object.keys(collectedSlots).length > 0) && (
          <div className="mb-6">
            <ConversationContext slots={collectedSlots} currentState={currentState} />
          </div>
        )}

        {/* State Progress Indicator */}
        {isConnected && (
          <div className="mb-6">
            <StateProgressIndicator currentState={currentState} />
          </div>
        )}

        {/* Conversation Area */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Conversation</h2>
            {isConnected && currentState && (
              <span className="text-xs px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full font-medium">
                {currentState.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            )}
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4 h-96 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <svg className="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p className="text-gray-500 dark:text-gray-400 font-medium">No messages yet</p>
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                  Connect to start the conversation
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[75%] rounded-lg p-3 ${
                        msg.role === 'user'
                          ? 'bg-blue-500 text-white rounded-br-none'
                          : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-bl-none'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <div className={`font-semibold text-xs ${
                          msg.role === 'user' ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'
                        }`}>
                          {msg.role === 'user' ? 'You' : 'Agent'}
                        </div>
                        {msg.state && (
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            msg.role === 'user' 
                              ? 'bg-blue-400 text-blue-50' 
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                          }`}>
                            {msg.state.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                      <div className={`text-sm ${msg.role === 'user' ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
                        {msg.text}
                      </div>
                      <div className={`text-xs mt-2 ${
                        msg.role === 'user' ? 'text-blue-100' : 'text-gray-400 dark:text-gray-500'
                      }`}>
                        {msg.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Audio Controls & Quick Actions */}
        <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          {isConnected && (
            <div className="flex gap-3 flex-1">
              <button
                onClick={toggleMicrophone}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  micEnabled 
                    ? 'bg-green-500 hover:bg-green-600 text-white' 
                    : 'bg-gray-300 dark:bg-gray-700 hover:bg-gray-400 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                {micEnabled ? 'Mic On' : 'Mic Off'}
              </button>
              <button
                onClick={() => setSpeakerEnabled(!speakerEnabled)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  speakerEnabled 
                    ? 'bg-green-500 hover:bg-green-600 text-white' 
                    : 'bg-gray-300 dark:bg-gray-700 hover:bg-gray-400 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
                {speakerEnabled ? 'Speaker On' : 'Speaker Off'}
              </button>
            </div>
          )}
          
          {isConnected && (
            <div className="flex gap-3">
              <button
                onClick={handleRestart}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Restart
              </button>
              <button
                onClick={handleEndConversation}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium bg-red-500 hover:bg-red-600 text-white transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                End
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Hidden audio element for agent audio */}
      <audio ref={audioRef} autoPlay style={{ display: 'none' }} />
    </div>
  )
}

