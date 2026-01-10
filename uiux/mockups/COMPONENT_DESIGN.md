# Component Design Specifications

## 1. Message Bubble Component

### Agent Message
```css
.agent-message {
 background: #EFF6FF; /* Light blue */
 border-left: 4px solid #2563EB; /* Blue accent */
 border-radius: 12px 12px 12px 4px;
 padding: 12px 16px;
 margin: 8px 0;
 max-width: 75%;
 text-align: left;

 .avatar {
 width: 32px;
 height: 32px;
 background: #2563EB;
 border-radius: 50%;
 display: inline-block;
 margin-right: 8px;
 }

 .timestamp {
 font-size: 12px;
 color: #6B7280;
 margin-top: 4px;
 }
}
```

### User Message
```css
.user-message {
 background: #F3F4F6; /* Light gray */
 border-right: 4px solid #6B7280; /* Gray accent */
 border-radius: 12px 12px 4px 12px;
 padding: 12px 16px;
 margin: 8px 0 8px auto;
 max-width: 75%;
 text-align: right;

 .avatar {
 width: 32px;
 height: 32px;
 background: #6B7280;
 border-radius: 50%;
 display: inline-block;
 margin-left: 8px;
 }

 .timestamp {
 font-size: 12px;
 color: #6B7280;
 margin-top: 4px;
 }
}
```

## 2. Connection Status Indicator

```css
.status-indicator {
 display: inline-flex;
 align-items: center;
 gap: 8px;
 padding: 4px 12px;
 border-radius: 16px;
 font-size: 14px;
 font-weight: 500;

 .dot {
 width: 8px;
 height: 8px;
 border-radius: 50%;
 animation: pulse 2s infinite;
 }

 &.connected .dot {
 background: #10B981; /* Green */
 }

 &.disconnected .dot {
 background: #EF4444; /* Red */
 }

 &.connecting .dot {
 background: #F59E0B; /* Amber */
 animation: pulse 1s infinite;
 }
}

@keyframes pulse {
 0%, 100% { opacity: 1; }
 50% { opacity: 0.5; }
}
```

## 3. Audio Control Button

```css
.audio-control {
 display: inline-flex;
 align-items: center;
 gap: 8px;
 padding: 10px 16px;
 border: 2px solid #E5E7EB;
 border-radius: 8px;
 background: white;
 cursor: pointer;
 transition: all 0.2s;
 font-size: 14px;
 font-weight: 500;

 &:hover {
 border-color: #2563EB;
 background: #F9FAFB;
 }

 &.active {
 background: #10B981;
 border-color: #10B981;
 color: white;
 }

 &.disabled {
 background: #F3F4F6;
 border-color: #E5E7EB;
 color: #9CA3AF;
 cursor: not-allowed;
 }

 .icon {
 font-size: 18px;
 }
}
```

## 4. State Progress Indicator

```css
.state-progress {
 display: flex;
 justify-content: space-between;
 padding: 16px;
 background: #F9FAFB;
 border-radius: 8px;
 margin: 16px 0;

 .state-step {
 flex: 1;
 text-align: center;
 position: relative;

 .step-icon {
 width: 40px;
 height: 40px;
 border-radius: 50%;
 display: flex;
 align-items: center;
 justify-content: center;
 margin: 0 auto 8px;
 font-size: 18px;
 font-weight: bold;

 &.completed {
 background: #10B981;
 color: white;
 }

 &.current {
 background: #2563EB;
 color: white;
 animation: pulse 2s infinite;
 }

 &.pending {
 background: #E5E7EB;
 color: #9CA3AF;
 border: 2px solid #D1D5DB;
 }
 }

 .step-label {
 font-size: 12px;
 color: #6B7280;
 font-weight: 500;

 &.current {
 color: #2563EB;
 font-weight: 600;
 }
 }

 &:not(:last-child)::after {
 content: '';
 position: absolute;
 top: 20px;
 right: -50%;
 width: 100%;
 height: 2px;
 background: #E5E7EB;
 z-index: -1;
 }
 }
}
```

## 5. Loading States

### Spinner
```css
.spinner {
 width: 40px;
 height: 40px;
 border: 4px solid #E5E7EB;
 border-top-color: #2563EB;
 border-radius: 50%;
 animation: spin 1s linear infinite;
}

@keyframes spin {
 to { transform: rotate(360deg); }
}
```

### Typing Indicator
```css
.typing-indicator {
 display: flex;
 gap: 4px;
 padding: 12px 16px;

 .dot {
 width: 8px;
 height: 8px;
 background: #9CA3AF;
 border-radius: 50%;
 animation: typing 1.4s infinite;

 &:nth-child(2) { animation-delay: 0.2s; }
 &:nth-child(3) { animation-delay: 0.4s; }
 }
}

@keyframes typing {
 0%, 60%, 100% { transform: translateY(0); }
 30% { transform: translateY(-10px); }
}
```

## 6. Error Toast

```css
.error-toast {
 position: fixed;
 bottom: 24px;
 right: 24px;
 max-width: 400px;
 padding: 16px;
 background: white;
 border-left: 4px solid #EF4444;
 border-radius: 8px;
 box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
 display: flex;
 align-items: start;
 gap: 12px;
 animation: slideIn 0.3s ease-out;

 .icon {
 color: #EF4444;
 font-size: 24px;
 flex-shrink: 0;
 }

 .content {
 flex: 1;

 .title {
 font-weight: 600;
 color: #111827;
 margin-bottom: 4px;
 }

 .message {
 font-size: 14px;
 color: #6B7280;
 }
 }

 .close {
 cursor: pointer;
 color: #9CA3AF;
 font-size: 20px;

 &:hover {
 color: #6B7280;
 }
 }
}

@keyframes slideIn {
 from {
 transform: translateX(100%);
 opacity: 0;
 }
 to {
 transform: translateX(0);
 opacity: 1;
 }
}
```

## Responsive Breakpoints

```css
/* Mobile First */
@media (max-width: 640px) {
 .message-bubble {
 max-width: 85%;
 padding: 10px 14px;
 font-size: 14px;
 }

 .state-progress {
 flex-direction: column;
 gap: 16px;
 }

 .audio-controls {
 flex-direction: column;
 width: 100%;
 }
}

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) {
 .message-bubble {
 max-width: 70%;
 }
}

/* Desktop */
@media (min-width: 1025px) {
 .message-bubble {
 max-width: 60%;
 }
}
```