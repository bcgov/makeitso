#!/bin/bash
set -euxo pipefail

# Fetch only the commit being deployed, into this deploy's own folder.
# The worker then reads engage.yaml from it and runs deploy.file itself
mkdir -p "$WORKDIR"
cd "$WORKDIR"
git init -q
git fetch --depth 1 "https://github.com/$STACK_ORG/$STACK_REPO.git" "$COMMIT_SHA"
git checkout -q FETCH_HEAD
