#!/bin/bash
# Test deploy: prints a line a second, deploys nothing
set -euo pipefail

echo "Deploying $COMMIT_SHA to $ENVIRONMENT"
for i in $(seq 1 30); do
  echo "step $i/30"
  sleep 2
done
echo "Done"