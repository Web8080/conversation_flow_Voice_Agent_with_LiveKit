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
      // Generate Bearer token for API authentication
      // LiveKit Twirp API requires Bearer token with admin permissions
      const at = new AccessToken(apiKey, apiSecret, {
        identity: apiKey, // Use API key as identity for admin tokens
        name: 'Agent Dispatch Service',
      })
      
      // Grant admin permissions (required for agent dispatch)
      at.addGrant({
        roomAdmin: true, // Admin access needed for agent dispatch
        canPublish: true,
        canSubscribe: true,
        canPublishData: true,
      })
      
      const bearerToken = at.toJwt()
      
      // Use LiveKit Twirp API to dispatch agent
      // This is the same API that `lk dispatch create` uses
      const livekitApiUrl = livekitUrl.replace('wss://', 'https://')
      
      const response = await fetch(`${livekitApiUrl}/twirp/livekit.AgentService/CreateAgentDispatch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${bearerToken}`
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

