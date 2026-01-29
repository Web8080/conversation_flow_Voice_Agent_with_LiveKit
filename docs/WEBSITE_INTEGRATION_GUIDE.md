# Website Integration Guide

## Overview

This voice agent can be integrated into any website using several methods. The frontend is built with Next.js/React and can be embedded as a widget, iframe, or standalone component.

## Integration Methods

### Method 1: Embed as React Component (Recommended)

**For React/Next.js websites:**

1. **Copy the VoiceAgentUI component:**
   ```bash
   # Copy the component and dependencies
   cp -r frontend/components/VoiceAgentUI.tsx your-project/components/
   cp -r frontend/components/StateProgressIndicator.tsx your-project/components/
   cp -r frontend/components/SystemStatus.tsx your-project/components/
   cp -r frontend/components/ConversationContext.tsx your-project/components/
   cp -r frontend/components/InfoPanel.tsx your-project/components/
   ```

2. **Install dependencies:**
   ```bash
   npm install livekit-client livekit-server-sdk jsonwebtoken
   ```

3. **Set up API route for LiveKit tokens:**
   ```typescript
   // your-project/app/api/livekit-token/route.ts
   import { NextRequest, NextResponse } from 'next/server'
   import { AccessToken } from 'livekit-server-sdk'
   
   export async function POST(req: NextRequest) {
     const { room_name } = await req.json()
     
     const apiKey = process.env.LIVEKIT_API_KEY!
     const apiSecret = process.env.LIVEKIT_API_SECRET!
     const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL!
     
     const at = new AccessToken(apiKey, apiSecret, {
       identity: `user-${Date.now()}`,
     })
     
     at.addGrant({
       roomJoin: true,
       room: room_name,
       canPublish: true,
       canSubscribe: true,
     })
     
     const token = await at.toJwt()
     
     return NextResponse.json({ token })
   }
   ```

4. **Use in your page:**
   ```tsx
   import VoiceAgentUI from '@/components/VoiceAgentUI'
   
   export default function YourPage() {
     return (
       <div>
         <h1>Your Website</h1>
         <VoiceAgentUI />
       </div>
     )
   }
   ```

### Method 2: Embed as iframe

**For any website (WordPress, HTML, etc.):**

1. **Deploy the frontend to a public URL** (e.g., Vercel, Netlify)

2. **Embed in your website:**
   ```html
   <iframe 
     src="https://your-voice-agent.vercel.app" 
     width="100%" 
     height="600px"
     frameborder="0"
     allow="microphone"
   ></iframe>
   ```

3. **For better mobile experience, use responsive iframe:**
   ```html
   <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
     <iframe 
       src="https://your-voice-agent.vercel.app" 
       style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
       frameborder="0"
       allow="microphone"
     ></iframe>
   </div>
   ```

### Method 3: Standalone Widget (Custom Build)

**Create a minimal widget version:**

1. **Create a widget-specific component:**
   ```tsx
   // widget/VoiceAgentWidget.tsx
   'use client'
   
   import { useState } from 'react'
   import VoiceAgentUI from '../components/VoiceAgentUI'
   
   export default function VoiceAgentWidget() {
     const [isOpen, setIsOpen] = useState(false)
     
     return (
       <>
         {/* Floating button */}
         <button
           onClick={() => setIsOpen(!isOpen)}
           className="fixed bottom-4 right-4 bg-blue-500 text-white rounded-full p-4 shadow-lg"
         >
           🎤 Voice Assistant
         </button>
         
         {/* Widget panel */}
         {isOpen && (
           <div className="fixed bottom-20 right-4 w-96 h-96 bg-white rounded-lg shadow-xl">
             <VoiceAgentUI />
           </div>
         )}
       </>
     )
   }
   ```

2. **Build and deploy as standalone widget**

### Method 4: API Integration (Headless)

**For custom frontends:**

1. **Use LiveKit SDK directly:**
   ```typescript
   import { Room, RoomEvent } from 'livekit-client'
   
   // Get token from your backend
   const token = await fetch('/api/livekit-token', {
     method: 'POST',
     body: JSON.stringify({ room_name: 'voice-agent-room' })
   }).then(r => r.json()).then(d => d.token)
   
   // Connect to room
   const room = new Room()
   await room.connect('wss://your-project.livekit.cloud', token)
   
   // Handle audio
   room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
     if (track.kind === Track.Kind.Audio) {
       track.attach(audioElement)
     }
   })
   ```

## Configuration for External Websites

### Environment Variables

Set these in your deployment platform (Vercel, Netlify, etc.):

```
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

### Customization Options

**1. Custom Styling:**
   - Modify `VoiceAgentUI.tsx` Tailwind classes
   - Add custom CSS for branding
   - Adjust colors, fonts, spacing

**2. Custom Room Names:**
   - Generate unique room names per user/session
   - Use user ID or session ID in room name
   - Implement room cleanup after session

**3. White-label Options:**
   - Replace logo/branding
   - Customize greeting messages
   - Adjust conversation flow for your use case

## Security Considerations

1. **Token Generation**: Always generate LiveKit tokens server-side
2. **Rate Limiting**: Implement rate limiting on token generation endpoint
3. **Room Access**: Use room names with user/session identifiers
4. **CORS**: Configure CORS if embedding cross-domain

## Features to Add for Production

### Recommended Enhancements

1. **User Authentication**
   - Integrate with your auth system
   - Pass user context to agent
   - Personalize conversations

2. **Analytics Integration**
   - Track conversation metrics
   - Monitor success rates
   - A/B test different flows

3. **Multi-language Support**
   - Detect user language
   - Configure STT/LLM/TTS for multiple languages
   - Localize UI

4. **Custom Business Logic**
   - Integrate with your CRM
   - Connect to your booking system
   - Sync with your database

5. **Webhook Integration**
   - Send appointment confirmations via webhook
   - Notify external systems
   - Trigger follow-up actions

6. **Recording & Playback**
   - Record conversations for quality assurance
   - Allow users to replay conversations
   - Compliance and training

7. **Admin Dashboard**
   - View all appointments
   - Monitor agent performance
   - Manage calendar integrations

## Example: WordPress Integration

```php
<!-- Add to your WordPress theme -->
<div id="voice-agent-container"></div>

<script>
  // Load the voice agent widget
  const iframe = document.createElement('iframe');
  iframe.src = 'https://your-voice-agent.vercel.app';
  iframe.width = '100%';
  iframe.height = '600px';
  iframe.frameBorder = '0';
  iframe.allow = 'microphone';
  document.getElementById('voice-agent-container').appendChild(iframe);
</script>
```

## Example: Shopify Integration

1. Create a Shopify app
2. Embed the voice agent in product pages
3. Use Shopify API to create orders/bookings
4. Sync appointments with Shopify calendar

## Support

For integration help, refer to:
- `docs/STAGE2_IMPLEMENTATION_GUIDE.md` - Implementation details
- `frontend/README.md` - Frontend setup
- LiveKit documentation: https://docs.livekit.io/


