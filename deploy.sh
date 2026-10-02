#!/bin/bash

set -euxo pipefail

if [ -z "${NAMESPACE_PREFIX:-}" ]; then
  echo "NAMESPACE_PREFIX is not set"
  exit 1
fi

echo "Deploying makeitso to namespace $NAMESPACE_PREFIX-tools"
helm repo add cas-postgres https://bcgov.github.io/cas-postgres/
helm dep up ./helm/makeitso

GIT_COMMIT=$(git rev-parse HEAD)

helm upgrade -n "$NAMESPACE_PREFIX-tools" \
  --install --rollback-on-failure  \
  --timeout 10m \
  --set app.imageTag="pr-35" \
  makeitso ./helm/makeitso

