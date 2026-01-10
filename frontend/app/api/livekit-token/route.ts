import { NextRequest, NextResponse } from 'next/server'
import { AccessToken } from 'livekit-server-sdk'

// Rate limiting (simple in-memory, use Redis in production)
const rateLimitMap = new Map<string, number[]>()
const RATE_LIMIT_WINDOW = 60000 // 1 minute
const RATE_LIMIT_MAX = 60 // 60 requests per minute

function checkRateLimit(ip: string): boolean {
  const now = Date.now()
  const requests = rateLimitMap.get(ip) || []
  
  // Clean old requests
  const validRequests = requests.filter(time => now - time < RATE_LIMIT_WINDOW)
  
  if (validRequests.length >= RATE_LIMIT_MAX) {
    return false
  }
  
  validRequests.push(now)
  rateLimitMap.set(ip, validRequests)
  return true
}

function validateRoomName(roomName: string): boolean {
  // Validate room name format
  if (!roomName || roomName.length === 0 || roomName.length > 100) {
    return false
  }
  
  // Alphanumeric, dash, underscore only
  if (!/^[a-zA-Z0-9_-]+$/.test(roomName)) {
    return false
  }
  
  // Block reserved names
  const reserved = ['admin', 'system', 'test', 'api', 'internal']
  if (reserved.includes(roomName.toLowerCase())) {
    return false
  }
  
  return true
}

export async function POST(request: NextRequest) {
  try {
    // Rate limiting
    const ip = request.headers.get('x-forwarded-for') || 
               request.headers.get('x-real-ip') || 
               'unknown'
    
    if (!checkRateLimit(ip)) {
      return NextResponse.json(
        { error: 'Rate limit exceeded. Please try again later.' }, 
        { status: 429 }
      )
    }

    const { room_name, user_id, user_name } = await request.json()
    
    if (!room_name) {
      return NextResponse.json({ error: 'Room name required' }, { status: 400 })
    }

    // Validate room name
    if (!validateRoomName(room_name)) {
      return NextResponse.json(
        { error: 'Invalid room name. Use only alphanumeric characters, dashes, and underscores.' }, 
        { status: 400 }
      )
    }

    const apiKey = process.env.LIVEKIT_API_KEY
    const apiSecret = process.env.LIVEKIT_API_SECRET

    if (!apiKey || !apiSecret) {
      console.error('Missing LiveKit credentials. Set LIVEKIT_API_KEY and LIVEKIT_API_SECRET in .env.local')
      return NextResponse.json({ 
        error: 'LiveKit credentials not configured. Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET in .env.local' 
      }, { status: 500 })
    }

    // Generate user identity
    const identity = user_id || `anonymous-${Date.now()}`
    const name = user_name || identity

    const at = new AccessToken(apiKey, apiSecret, {
      identity,
      name,
    })

    at.addGrant({
      room: room_name,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
      canUpdateOwnMetadata: true,
      roomAdmin: false, // Regular users are not admins
    })

    // Set token expiration (1 hour)
    const token = await at.toJwt()

    return NextResponse.json({ 
      token,
      room_name,
      user_id: identity,
      expires_in: 3600, // 1 hour in seconds
    })
  } catch (error: any) {
    console.error('Token generation error:', error)
    return NextResponse.json({ 
      error: `Failed to generate token: ${error.message}` 
    }, { status: 500 })
  }
}

