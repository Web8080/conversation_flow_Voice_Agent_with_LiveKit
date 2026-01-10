#!/bin/bash

# Deployment Script
# Handles automated deployment with rollback capability

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

echo "🚀 Deploying to $ENVIRONMENT environment..."
echo "Version: $VERSION"

# Pre-deployment checks
echo "📋 Running pre-deployment checks..."
./scripts/deployment/pre-deploy-checks.sh

# Backup current version
echo "💾 Backing up current version..."
./scripts/deployment/backup.sh "$ENVIRONMENT"

# Deploy backend
echo "🔧 Deploying backend..."
cd backend
docker build -t voice-agent-backend:$VERSION .
docker tag voice-agent-backend:$VERSION your-registry/voice-agent-backend:$VERSION
docker push your-registry/voice-agent-backend:$VERSION

# Deploy frontend
echo "🎨 Deploying frontend..."
cd ../frontend
npm run build
# Deploy to Vercel or similar

# Health checks
echo "🏥 Running health checks..."
sleep 10
./scripts/deployment/health-check.sh "$ENVIRONMENT"

# Verify deployment
if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    ./scripts/deployment/notify.sh "$ENVIRONMENT" "success" "$VERSION"
else
    echo "❌ Deployment failed! Rolling back..."
    ./scripts/deployment/rollback.sh "$ENVIRONMENT"
    exit 1
fi

