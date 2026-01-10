# Wireframe: Main Voice Agent Dashboard

## Layout Structure

```

 VOICE AGENT DASHBOARD 

 HEADER BAR 
 [Logo] Voice Agent [Status: Connected] [] 

 CONNECTION PANEL (Collapsible) 

 Room Name: [voice-agent-room ] [Connect] 

 Status: Connected | Participants: 2 (You + Agent) 

 Mic: ON Spk: ON ⏸ Pause 

 CONVERSATION AREA 

 [Agent Avatar] 
 Hello! I'm your appointment scheduling 
 assistant. What's your name? 
 10:30 AM 

 [Your Avatar] 
 My name is John Doe 
 10:31 AM 

 [Agent Avatar] 
 Nice to meet you, John! When would you like 
 to schedule your appointment? 
 10:31 AM 

 [Scroll to bottom] 

 CONVERSATION STATE INDICATOR 
 Current State: [Collecting Date] 

 Greet Name Date Time Confirm 

 QUICK ACTIONS 
 [ Restart] [ End Conversation] [ Help] 

```

## Key UI Elements

### 1. Header Bar
- **Logo/Branding**: Left side
- **Status Indicator**: Real-time connection status
- **Settings Icon**: Access to configuration

### 2. Connection Panel
- **Room Input**: Text field for LiveKit room name
- **Connect Button**: Primary CTA
- **Status Display**: Connection state, participant count
- **Audio Controls**: Microphone, Speaker, Pause toggles

### 3. Conversation Area
- **Message Bubbles**: Chat-like interface
 - Agent messages: Left-aligned, blue background
 - User messages: Right-aligned, gray background
- **Timestamps**: Each message has timestamp
- **Avatars**: Visual distinction between user and agent
- **Auto-scroll**: Automatically scrolls to latest message

### 4. State Indicator
- **Progress Bar**: Shows current conversation stage
- **Visual Feedback**: Completed states checked, current state highlighted
- **Helpful**: Users understand where they are in the flow

### 5. Quick Actions
- **Restart**: Start new conversation
- **End**: Gracefully end current conversation
- **Help**: Show help/support options

## Mobile Layout

On mobile (< 768px):
- Full-width layout
- Stacked controls
- Larger tap targets (min 44x44px)
- Simplified state indicator
- Bottom sheet for audio controls

## Accessibility Features

- **Keyboard Navigation**: Tab through all interactive elements
- **Screen Reader Support**: ARIA labels on all controls
- **Focus Indicators**: Clear focus states
- **Color Contrast**: WCAG AA compliant (4.5:1 ratio)
- **Text Scaling**: Supports up to 200% zoom