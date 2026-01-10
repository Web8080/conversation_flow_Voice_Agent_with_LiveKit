# Wireframe: Connection Flow States

## State 1: Initial/Disconnected

```

 [Voice Agent Logo] 

 Connect to Voice Agent 

 Room Name 
 [_____________________] 

 [Connect to Room] 

 Tip: Enter a room name 
 to start your session 

```

## State 2: Connecting

```

 [Animated Spinner] 

 Connecting to room... 

 [] Establishing connection 
 [] Joining room 
 [] Waiting for agent... 

 [Cancel] 

```

## State 3: Connected & Waiting

```

 Connected | Room: test-room 

 Agent is joining... 

 [Wave Animation] 

 [] Mic Ready 

```

## State 4: Active Conversation

```

 Connected | 2 Participants 

 [Agent] Hello! How can... 

 [You] Hi! 

 Listening... 

 [ ON] [ ON] [⏸] [] 

```

## State 5: Error/Disconnected

```

 [ Warning Icon] 

 Connection Lost 

 The connection to the room was 
 interrupted. 

 Possible reasons: 
 • Network issue 
 • Room closed 
 • Server error 

 [Reconnect] [Start New] 

```

## Microphone Permission Request

```

 [ Icon] 

 Microphone Access Required 

 We need access to your 
 microphone to enable voice 
 conversations. 

 [Allow Microphone Access] 

 [Not Now] 

 Your privacy is important. We 
 only use audio during active 
 conversations. 

```