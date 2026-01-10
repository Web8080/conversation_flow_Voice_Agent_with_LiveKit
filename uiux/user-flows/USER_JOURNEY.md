# User Journey Map - Voice Agent

## Primary User Journey: Schedule Appointment

### Stage 1: Discovery & Entry
**User Goal**: Start a conversation to schedule appointment

```
[Landing Page]
 ↓
User clicks "Start Conversation"
 ↓
[Connection Screen]
 ↓
User enters room name (or uses default)
 ↓
Clicks "Connect"
```

**Pain Points**:
- Unclear what room name means (should have help text)
- No indication of what happens next

**Design Solutions**:
- Clear explanation of room name
- Progress indicator during connection
- Help tooltips

### Stage 2: Connection & Setup
**User Goal**: Successfully connect and enable microphone

```
[Connecting State]
 ↓
Browser asks for microphone permission
 ↓
User allows/denies
 ↓
[Connected State]
 ↓
Agent joins room
```

**Pain Points**:
- Microphone permission popup can be intrusive
- No feedback if permission denied
- Unclear if connection successful

**Design Solutions**:
- Clear permission request with explanation
- Graceful handling of denied permissions
- Visual confirmation of connection status
- Instructions for enabling permissions manually

### Stage 3: Initial Interaction
**User Goal**: Understand what to do and start conversation

```
[Agent Greeting]
 ↓
User listens to agent introduction
 ↓
Agent asks for name
 ↓
User speaks name
 ↓
[Visual Feedback: "Listening..."]
 ↓
Agent confirms name and asks for date
```

**Pain Points**:
- Users might not know when to speak
- No visual confirmation of speech being captured
- Unclear if agent understood correctly

**Design Solutions**:
- Visual "listening" indicator
- Real-time transcription display (optional)
- Clear prompts from agent
- Visual confirmation of understood input

### Stage 4: Information Collection
**User Goal**: Provide required information (date, time)

```
[Date Collection]
 ↓
User provides date
 ↓
Agent confirms date, asks for time
 ↓
User provides time
 ↓
Agent confirms time
```

**Pain Points**:
- Users might provide incomplete information
- Natural language variations ("tomorrow", "next week")
- No way to see what was understood

**Design Solutions**:
- State progress indicator shows current step
- Agent repeats back what was understood
- Error messages if information unclear
- Option to correct information

### Stage 5: Confirmation
**User Goal**: Verify appointment details are correct

```
[Confirmation State]
 ↓
Agent summarizes: "John, appointment on Jan 15 at 2PM?"
 ↓
User confirms yes/no
 ↓
If yes: [Completion]
If no: [Return to date collection]
```

**Pain Points**:
- Users might not remember what they said
- Confirmation might be missed
- No way to see full summary visually

**Design Solutions**:
- Visual summary card with all details
- Clear yes/no prompts
- Easy way to go back and change details
- Confirmation screen with all information

### Stage 6: Completion
**User Goal**: Receive confirmation and end conversation

```
[Terminal State]
 ↓
Agent confirms appointment
 ↓
Provides summary
 ↓
Says goodbye
 ↓
[End Conversation Button]
```

**Pain Points**:
- Users might want to save/export appointment details
- No record of conversation
- Unclear when conversation is over

**Design Solutions**:
- Final summary screen with all details
- Option to export/save (email, calendar)
- Clear "Conversation Complete" state
- Option to start new conversation

## Error Scenarios

### Scenario 1: Connection Failed
```
[Connection Attempt]
 ↓
Error: Connection failed
 ↓
[Error Screen with reason]
 ↓
Options:
 - [Retry]
 - [Check Settings]
 - [Contact Support]
```

### Scenario 2: Microphone Not Working
```
[Connection Successful]
 ↓
No audio detected
 ↓
[Warning Banner]
 ↓
"Microphone not detected. Please check your settings."
 ↓
[Test Microphone] button
```

### Scenario 3: Agent Doesn't Understand
```
[User provides input]
 ↓
Agent: "I didn't catch that. Could you repeat?"
 ↓
Visual indicator: "Unclear input, please try again"
 ↓
[Retry Count: 1/3]
 ↓
After 3 attempts: Offer to connect to human agent
```

## Accessibility Journey

### Screen Reader User
1. All UI elements have ARIA labels
2. Conversation transcript is fully accessible
3. Keyboard navigation through all controls
4. Status announcements for state changes

### Keyboard-Only User
1. Tab through all interactive elements
2. Enter/Space to activate buttons
3. Escape to close modals
4. Arrow keys for navigation where applicable

### Low Vision User
1. High contrast mode option
2. Text scaling up to 200%
3. Large touch targets (min 44x44px)
4. Clear visual indicators for all states