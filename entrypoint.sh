#!/bin/sh

# shellcheck disable=SC2153
app_type=$APP_TYPE
echo "$app_type is running..."

if [ "$app_type" = "app" ]; then
  # shellcheck disable=SC2086
  uvicorn main:app --host 0.0.0.0 --port $PORT

elif [ "$app_type" = "worker" ]; then
  # shellcheck disable=SC2086
  celery -A tasks.tasks worker --loglevel=INFO --concurrency=$CONCURRENCY

fi