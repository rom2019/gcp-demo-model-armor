#!/bin/bash

# deploy.sh - gcloud run을 사용한 배포 스크립트

set -e

# Need to change
export GCP_PROJECT_ID="releng-project"
export GCP_LOCATION="us-central1"
export SERVICE_NAME="model-armor-demo"
export IMAGE_NAME="model-armor-demo"
export MODEL_ARMOR_TEMPLATE_ID="model-armor-demo"

echo "🚀 Starting deployment with gcloud run..."
echo "📋 Configuration:"
echo "  Project ID: $GCP_PROJECT_ID"
echo "  Location: $GCP_LOCATION"
echo "  Service Name: $SERVICE_NAME"
echo "  Model Armor Template: $MODEL_ARMOR_TEMPLATE_ID"

echo "🔧 Setting up GCP project..."
gcloud config set project $GCP_PROJECT_ID

echo "🔌 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable modelarmor.googleapis.com

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

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$GCP_LOCATION --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"

echo "🔍 Checking service status..."
gcloud run services describe $SERVICE_NAME --region=$GCP_LOCATION

echo ""
echo "🎉 Deployment successful!"
echo "📱 Access your application at: $SERVICE_URL"
