#!/usr/bin/env bash

gcloud functions deploy prompt \
  --gen2 \
  --runtime=python312 \
  --project=genlabhackathon \
  --region=us-central1 \
  --source=. \
  --entry-point=prompt \
  --trigger-http \
  --allow-unauthenticated
