#!/bin/bash

set -euxo pipefail

if [ -z "$CIIP_NAMESPACE_PREFIX" ]; then
  echo "CIIP_NAMESPACE_PREFIX is not set"
  exit 1
fi

echo "Deploying makeitso to namespace $CIIP_NAMESPACE_PREFIX-tools"
helm repo add cas-postgres https://bcgov.github.io/cas-postgres/
helm dep up ./helm/makeitso

GIT_COMMIT=$(git rev-parse HEAD)

helm upgrade -n "$CIIP_NAMESPACE_PREFIX-tools" \
  --install --atomic  \
  makeitso ./helm/makeitso

