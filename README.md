# gcp-demo-model-armor

python -m venv .venv
source .venv/bin/activate

gcloud run deploy armor-cheers  --source . --platform managed  --region us-central1 --allow-unauthenticated