#!/bin/bash

# 🎬 Greenlit AI - Deployment Script for Google Cloud Run
# Run this script to deploy both frontend and backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎬 Greenlit AI - Production Deployment${NC}"
echo "======================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI not found. Please install gcloud first.${NC}"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_CLOUD_PROJECT not set. Please set it first:${NC}"
    echo "export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

echo -e "${GREEN}📋 Project: $GOOGLE_CLOUD_PROJECT${NC}"

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Deploy Backend to Cloud Run
echo -e "${BLUE}🚀 Deploying backend to Google Cloud Run...${NC}"
cd backend

# Build and deploy
gcloud run deploy greenlit-ai-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300s

# Get backend URL
BACKEND_URL=$(gcloud run services describe greenlit-ai-backend --region=us-central1 --format='value(status.url)')
echo -e "${GREEN}✅ Backend deployed: $BACKEND_URL${NC}"

cd ..

# Deploy Frontend to Cloud Run (alternative to Vercel)
echo -e "${BLUE}🚀 Deploying frontend to Google Cloud Run...${NC}"
cd frontend

# Create Dockerfile for frontend if it doesn't exist
if [ ! -f "Dockerfile" ]; then
    cat > Dockerfile << EOF
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
ENV NEXT_PUBLIC_API_URL=$BACKEND_URL
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT 3000
CMD ["node", "server.js"]
EOF
fi

# Build and deploy frontend
gcloud run deploy greenlit-ai-frontend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL" \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe greenlit-ai-frontend --region=us-central1 --format='value(status.url)')
echo -e "${GREEN}✅ Frontend deployed: $FRONTEND_URL${NC}"

cd ..

# Summary
echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "========================"
echo -e "${BLUE}🌐 Frontend URL:${NC} $FRONTEND_URL"
echo -e "${BLUE}🔧 Backend URL:${NC} $BACKEND_URL"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Update CORS settings in backend to include frontend URL"
echo "2. Set up custom domain (optional)"
echo "3. Configure monitoring and logging"
echo "4. Set up CI/CD pipeline"
echo ""
echo -e "${GREEN}🎬 Ready to greenlight your production research!${NC}"