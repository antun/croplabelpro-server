#!/usr/bin/env bash

gcloud functions deploy analyze \
  --gen2 \
  --runtime=python312 \
  --project=genlabhackathon \
  --region=us-central1 \
  --source=. \
  --entry-point=analyze \
  --trigger-http \
  --allow-unauthenticated \
  --env-vars-file .env.yaml
