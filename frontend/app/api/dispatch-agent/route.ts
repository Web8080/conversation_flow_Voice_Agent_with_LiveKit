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
      // For LiveKit Cloud Twirp API, generate a server admin token
      // The token needs admin permissions and room access for dispatch
      const at = new AccessToken(apiKey, apiSecret, {
        identity: 'dispatch-service',
        name: 'Agent Dispatch Service',
      })
      
      // Grant admin permissions with room access for agent dispatch
      // Include the room in the grant since we're dispatching to a specific room
      at.addGrant({
        room: room_name, // Include room for dispatch
        roomAdmin: true, // Admin access needed for agent dispatch
        canPublish: true,
        canSubscribe: true,
        canPublishData: true,
        canUpdateOwnMetadata: true,
      })
      
      // Set token expiration (5 minutes for API calls)
      at.ttl = '5m'
      
      // Generate Bearer token (synchronous, no await)
      const bearerToken = at.toJwt()
      
      // Use LiveKit Twirp API to dispatch agent
      // The endpoint URL should match the LiveKit Cloud instance
      const livekitApiUrl = livekitUrl.replace('wss://', 'https://')
      
      const response = await fetch(`${livekitApiUrl}/twirp/livekit.AgentService/CreateAgentDispatch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${bearerToken}`,
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

