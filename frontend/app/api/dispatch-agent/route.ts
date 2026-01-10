import { NextRequest, NextResponse } from 'next/server'
import { AccessToken } from 'livekit-server-sdk'

export async function POST(request: NextRequest) {
  try {
    const { room_name } = await request.json()
    
    if (!room_name) {
      return NextResponse.json({ error: 'Room name required' }, { status: 400 })
    }

    const apiKey = process.env.LIVEKIT_API_KEY
    const apiSecret = process.env.LIVEKIT_API_SECRET
    const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL

    if (!apiKey || !apiSecret || !livekitUrl) {
      return NextResponse.json({ 
        error: 'LiveKit credentials not configured' 
      }, { status: 500 })
    }

    try {
      // For LiveKit Cloud Twirp API, use Basic authentication
      // The API expects Basic auth (API key:secret base64 encoded) for server-side calls
      // This is different from client-side Bearer tokens
      const livekitApiUrl = livekitUrl.replace('wss://', 'https://')
      const basicAuth = Buffer.from(`${apiKey}:${apiSecret}`).toString('base64')
      
      // Use LiveKit Twirp API to dispatch agent
      // This is the same API that `lk dispatch create` uses
      const response = await fetch(`${livekitApiUrl}/twirp/livekit.AgentService/CreateAgentDispatch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${basicAuth}`,
        },
        body: JSON.stringify({
          room: room_name,
          agent_name: 'appointment-scheduler',
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Dispatch API error:', response.status, errorText)
        throw new Error(`Failed to dispatch agent: ${response.status} ${errorText}`)
      }

      const result = await response.json()
      console.log('Agent dispatched successfully:', result)

      return NextResponse.json({ 
        success: true,
        message: 'Agent dispatched successfully',
        dispatch_id: result.dispatch_id
      })
    } catch (error: any) {
      console.error('Agent dispatch error:', error)
      return NextResponse.json({ 
        error: `Failed to dispatch agent: ${error.message}` 
      }, { status: 500 })
    }
  } catch (error: any) {
    console.error('Dispatch API error:', error)
    return NextResponse.json({ 
      error: `Failed to dispatch agent: ${error.message}` 
    }, { status: 500 })
  }
}

