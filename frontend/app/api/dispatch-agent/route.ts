import { NextRequest, NextResponse } from 'next/server'
import jwt from 'jsonwebtoken'

export async function POST(request: NextRequest) {
  try {
    const { room_name } = await request.json()
    
    // #region debug log
    fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:6',message:'Dispatch API called',data:{room_name},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    
    if (!room_name) {
      return NextResponse.json({ error: 'Room name required' }, { status: 400 })
    }

    const apiKey = process.env.LIVEKIT_API_KEY
    const apiSecret = process.env.LIVEKIT_API_SECRET
    const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL

    // #region debug log
    fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:18',message:'Env vars check',data:{hasApiKey:!!apiKey,hasApiSecret:!!apiSecret,hasLivekitUrl:!!livekitUrl,livekitUrl},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion

    if (!apiKey || !apiSecret || !livekitUrl) {
      return NextResponse.json({ 
        error: 'LiveKit credentials not configured' 
      }, { status: 500 })
    }

    try {
      // Generate JWT token with correct format for LiveKit Cloud API
      // Based on LiveKit's token format: iss=API key, video grants with admin permissions
      const payload = {
        iss: apiKey,
        exp: Math.floor(Date.now() / 1000) + 3600, // Token expires in 1 hour
        video: {
          roomCreate: true,
          roomJoin: true,
          roomAdmin: true,
          room: room_name,
        }
      }
      
      const bearerToken = jwt.sign(payload, apiSecret, { algorithm: 'HS256' })
      
      // Use LiveKit Twirp API to dispatch agent
      // CLI dispatch uses agent_name (not agent_id)
      const livekitApiUrl = livekitUrl.replace('wss://', 'https://')
      const dispatchUrl = `${livekitApiUrl}/twirp/livekit.AgentService/CreateAgentDispatch`
      
      // Use agent_name (CLI agents are registered with agent_name)
      const agentName = 'appointment-scheduler'
      const dispatchBody = {
        room: room_name,
        agent_name: agentName, // Use agent_name (not agent_id)
      }
      
      // #region debug log
      fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:55',message:'Using agent_name for dispatch',data:{agentName,dispatchBody},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H'})}).catch(()=>{});
      // #endregion
      
      // #region debug log
      fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:52',message:'Dispatch body prepared',data:{dispatchBody,dispatchUrl},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      
      // #region debug log
      fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:50',message:'Before LiveKit API call',data:{dispatchUrl,dispatchBody,hasBearerToken:!!bearerToken},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      
      // #region debug log
      fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:70',message:'About to call LiveKit dispatch API',data:{dispatchUrl,dispatchBody,agentName},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion

      // Server-side logging (will appear in Vercel function logs)
      console.log('[DISPATCH] LiveKit API call:', {
        url: dispatchUrl,
        body: dispatchBody,
        agentName: agentName,
      })

      const response = await fetch(dispatchUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${bearerToken}`,
        },
        body: JSON.stringify(dispatchBody)
      })

      // Read response body once (can only read once)
      const responseText = await response.text()
      const contentType = response.headers.get('content-type') || ''
      
      // Server-side logging
      console.log('[DISPATCH] LiveKit API response:', {
        status: response.status,
        statusText: response.statusText,
        contentType,
        body: responseText,
      })

      // #region debug log
      fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:82',message:'LiveKit API response received',data:{status:response.status,statusText:response.statusText,ok:response.ok,body:responseText,contentType},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      
      if (!response.ok) {
        console.error('[DISPATCH] LiveKit API error:', {
          status: response.status,
          statusText: response.statusText,
          body: responseText,
        })
        // #region debug log
        fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:62',message:'Dispatch API error',data:{status:response.status,errorText:responseText},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        throw new Error(`Failed to dispatch agent: ${response.status} ${responseText}`)
      }

      // Handle response - LiveKit API might return "OK" as text or JSON
      let result: any = {}
      
      if (contentType.includes('application/json')) {
        try {
          result = JSON.parse(responseText)
        } catch (e) {
          console.error('[DISPATCH] Failed to parse JSON response:', responseText, e)
          result = { message: responseText }
        }
      } else {
        // Response might be "OK" or empty - dispatch succeeded
        console.log('[DISPATCH] LiveKit API response (text):', responseText)
        
        // If we get "OK" or empty, dispatch was successful
        if (responseText.trim() === 'OK' || responseText.trim() === '') {
          result = { success: true }
        } else {
          // Try to parse as JSON anyway
          try {
            result = JSON.parse(responseText)
          } catch {
            result = { message: responseText }
          }
        }
      }
      
      console.log('[DISPATCH] Parsed result:', result)

      // #region debug log
      fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:85',message:'Dispatch result parsed',data:{result,contentType,responseText},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      
      console.log('Agent dispatched successfully:', result)

      // Return detailed response including what LiveKit returned
      const responseData = { 
        success: true,
        message: 'Agent dispatched successfully',
        dispatch_id: result.id || result.dispatch_id || result.dispatchId,
        livekit_response: {
          status: response.status,
          body: responseText,
          contentType,
          parsed: result,
        },
        dispatch_request: {
          url: dispatchUrl,
          body: dispatchBody,
          agentName,
        }
      }
      
      console.log('[DISPATCH] Returning response to frontend:', responseData)

      // #region debug log
      fetch('http://127.0.0.1:7244/ingest/8572ea72-42e9-4de6-ae58-e541b30671a6',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'dispatch-agent/route.ts:120',message:'Dispatch successful, returning response',data:responseData,timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion

      return NextResponse.json(responseData)
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

