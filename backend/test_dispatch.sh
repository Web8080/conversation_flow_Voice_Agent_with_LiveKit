#!/bin/bash
# Test agent dispatch via curl

source .env 2>/dev/null || true

API_KEY="${LIVEKIT_API_KEY}"
API_SECRET="${LIVEKIT_API_SECRET}"
LIVEKIT_URL="${LIVEKIT_URL:-wss://voiceagent007-fnileh5c.livekit.cloud}"
AGENT_ID="${1:-CA_ZzqAYfvCTYjs}"
ROOM_NAME="${2:-test-room-cli}"

if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ]; then
    echo "ERROR: Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET"
    exit 1
fi

echo "Testing dispatch for agent: $AGENT_ID"
echo "Room: $ROOM_NAME"
echo ""

# Generate JWT token using Python
JWT_TOKEN=$(python3 << PYEOF
import jwt
import time

payload = {
    "iss": "$API_KEY",
    "exp": int(time.time()) + 3600,
    "video": {
        "roomCreate": True,
        "roomJoin": True,
        "roomAdmin": True,
        "room": "$ROOM_NAME"
    }
}

token = jwt.encode(payload, "$API_SECRET", algorithm='HS256')
print(token)
PYEOF
)

if [ -z "$JWT_TOKEN" ]; then
    echo "ERROR: Failed to generate JWT token"
    exit 1
fi

# Convert wss:// to https://
API_URL=$(echo "$LIVEKIT_URL" | sed 's/wss:\/\//https:\/\//')
DISPATCH_URL="${API_URL}/twirp/livekit.AgentService/CreateAgentDispatch"

echo "Dispatching agent..."
echo "URL: $DISPATCH_URL"
echo ""

# Call dispatch API
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "{\"room\": \"$ROOM_NAME\", \"agent_id\": \"$AGENT_ID\"}" \
    "$DISPATCH_URL")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Response Status: $HTTP_STATUS"
echo "Response Body: $BODY"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Dispatch successful!"
    echo ""
    echo "Now watch agent logs with:"
    echo "  lk agent logs --project voiceagent007"
    echo ""
    echo "You should see 'received job request' in the logs"
else
    echo "❌ Dispatch failed with status $HTTP_STATUS"
fi
