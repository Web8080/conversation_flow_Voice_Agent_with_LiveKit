#!/bin/bash

# Complete deployment via terminal only

cd /Users/user/Fortell_AI_Product/backend

echo "==================================================================="
echo "COMPLETE DEPLOYMENT VIA TERMINAL"
echo "==================================================================="

# Option 1: Create new agent with secrets
echo ""
echo "Creating new agent with secrets..."
echo "2" | lk agent create \
  --secrets-file .env.secrets \
  --project voiceagent008 \
  --silent

if [ $? -eq 0 ]; then
  echo "✅ Agent created successfully!"
  
  # Deploy the agent
  echo ""
  echo "Deploying agent..."
  echo "2" | lk agent deploy --project voiceagent008
  
  # Check status
  echo ""
  echo "Checking status..."
  echo "2" | lk agent status --project voiceagent008
else
  echo "❌ Agent creation failed. Trying to use existing agent..."
  
  # Option 2: If agent exists, update secrets and deploy
  echo ""
  echo "Updating secrets for existing agent..."
  echo "2" | lk agent update-secrets \
    --secrets-file .env.secrets \
    --project voiceagent008 \
    --overwrite
  
  echo ""
  echo "Deploying existing agent..."
  echo "2" | lk agent deploy \
    --secrets-file .env.secrets \
    --project voiceagent008
fi

echo ""
echo "==================================================================="
echo "DEPLOYMENT COMPLETE!"
echo "==================================================================="
echo ""
echo "View logs with:"
echo "  echo '2' | lk agent logs --project voiceagent008"
echo ""
echo "Check status with:"
echo "  echo '2' | lk agent status --project voiceagent008"
echo ""

