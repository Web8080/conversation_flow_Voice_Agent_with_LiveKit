# UI Preview Guide

## Viewing the UI

The frontend is now running! You can view it at:

**http://localhost:3000**

## UI Components You'll See

### Main Dashboard

The UI includes:

1. **Header**
 - Title: "Voice Agent"
 - Clean, centered layout

2. **Connection Panel**
 - Room name input field (default: "voice-agent-room")
 - Connect/Disconnect button
 - Connection status indicator (green dot = connected, gray = disconnected)
 - Participant count display

3. **Audio Controls** (when connected)
 - Microphone toggle button ( Mic On/Off)
 - Speaker toggle button ( Speaker On/Off)
 - Green = enabled, Gray = disabled

4. **Conversation Area**
 - Message bubbles display
 - Agent messages: Left-aligned, gray background
 - User messages: Right-aligned, blue background
 - Timestamps for each message
 - Empty state: "No messages yet. Connect to start the conversation."

5. **State Progress Indicator** (to be added in Stage 2)
 - Visual progress through conversation states
 - Shows: Greeting → Name → Date → Time → Confirmation

## Design Features

- **Modern UI**: Clean, professional design
- **Responsive**: Works on desktop and mobile
- **Dark Mode**: Supports dark mode (follows system preference)
- **Tailwind CSS**: Utility-first styling
- **Accessible**: Proper labels and semantic HTML

## Current Status

### What Works Now:
 UI renders correctly
 Room connection UI
 Connection status display
 Message display area
 Audio controls UI
 Responsive design

### What Needs Backend:
 Token generation (requires LiveKit credentials)
 Actual room connection (requires backend running)
 Voice interaction (requires agent running)

## Testing the UI Without Backend

You can still see the UI layout:

1. Open http://localhost:3000 in your browser
2. The UI will render with:
 - Room name input
 - Connect button
 - Empty conversation area
 - Status showing "Disconnected"

3. Clicking "Connect" will attempt to:
 - Generate a LiveKit token via `/api/livekit-token`
 - Connect to LiveKit room
 - This will fail without proper credentials, but you'll see error handling

## UI Screenshots / Wireframes

For detailed wireframes and mockups, see:
- `uiux/wireframes/MAIN_DASHBOARD.md` - Main UI layout
- `uiux/wireframes/CONNECTION_FLOW.md` - Connection states
- `uiux/mockups/COMPONENT_DESIGN.md` - Component specifications

## Next Steps to See Full Functionality

1. **Configure LiveKit**:
 - Get LiveKit Cloud credentials
 - Add to `frontend/.env.local`:
 ```
 NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
 ```
 - Add to backend or API route:
 ```
 LIVEKIT_API_KEY=your-key
 LIVEKIT_API_SECRET=your-secret
 ```

2. **Start Backend**:
 ```bash
 cd backend
 python main.py dev
 ```

3. **Test Full Flow**:
 - Connect to room
 - Agent joins
 - Start conversation
 - See state machine in action

## UI Improvements Made

Based on the wireframes and design specs:
- Clean, professional design
- Clear visual hierarchy
- Proper spacing and layout
- Color-coded status indicators
- Accessible form controls
- Responsive message bubbles
- Error handling UI
- Loading states

## Browser Compatibility

Tested and works on:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

**UI not loading?**
- Check if dev server is running: `npm run dev` in frontend directory
- Check browser console for errors
- Verify port 3000 is available

**Styles not working?**
- Tailwind CSS should compile automatically
- Check if `postcss.config.js` exists
- Try rebuilding: `npm run build`

**Connection errors?**
- Normal without LiveKit credentials
- Check browser console for specific error
- Verify API route exists: `/api/livekit-token`

## Visual Design Details

**Colors**:
- Primary Blue: `#2563EB` (buttons, links)
- Success Green: `#10B981` (status indicators, enabled states)
- Error Red: `#EF4444` (errors, disconnect)
- Background: `#F9FAFB` (light), `#111827` (dark)

**Typography**:
- Font: Inter, system-ui, sans-serif
- Headings: Bold, 24-32px
- Body: Regular, 16px

**Spacing**:
- Consistent 4px base unit
- Common: 8px, 16px, 24px, 32px

Enjoy exploring the UI!