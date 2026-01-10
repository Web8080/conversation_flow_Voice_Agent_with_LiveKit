#!/bin/bash

# Deploy agent via CLI with all secrets

echo "Deploying agent via CLI..."

# Step 1: Update secrets
echo "Step 1: Updating secrets..."
echo "2" | lk agent update-secrets --secrets-file .env.secrets --project voiceagent008 --overwrite

# Step 2: Deploy agent
echo "Step 2: Deploying agent..."
echo "2" | lk agent deploy --secrets-file .env.secrets --project voiceagent008

# Step 3: Check status
echo "Step 3: Checking status..."
echo "2" | lk agent status --project voiceagent008

echo "Deployment complete!"
