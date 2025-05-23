#!/bin/bash

# deploy.sh - gcloud run을 사용한 배포 스크립트

set -e

# 환경 변수 설정 (필요에 따라 수정)
export GCP_PROJECT_ID="releng-project"
export GCP_LOCATION="us-central1"
export SERVICE_NAME="model-armor-demo"
export IMAGE_NAME="model-armor-demo"
export MODEL_ARMOR_TEMPLATE_ID="test"

echo "🚀 Starting deployment with gcloud run..."
echo "📋 Configuration:"
echo "  Project ID: $GCP_PROJECT_ID"
echo "  Location: $GCP_LOCATION"
echo "  Service Name: $SERVICE_NAME"
echo "  Model Armor Template: $MODEL_ARMOR_TEMPLATE_ID"

# 1. 프로젝트 설정 확인
echo "🔧 Setting up GCP project..."
gcloud config set project $GCP_PROJECT_ID

# 2. 필요한 API 활성화
echo "🔌 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable modelarmor.googleapis.com

# 3. 소스 코드로 직접 배포 (Cloud Build 사용)
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $GCP_LOCATION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 100 \
  --timeout 300 \
  --set-env-vars "GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_LOCATION=$GCP_LOCATION,MODEL_ARMOR_TEMPLATE_ID=$MODEL_ARMOR_TEMPLATE_ID" \
  --execution-environment gen2

echo "✅ Deployment completed!"

# 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$GCP_LOCATION --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"

# 서비스 상태 확인
echo "🔍 Checking service status..."
gcloud run services describe $SERVICE_NAME --region=$GCP_LOCATION

echo ""
echo "🎉 Deployment successful!"
echo "📱 Access your application at: $SERVICE_URL"
