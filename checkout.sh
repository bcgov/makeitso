#!/bin/bash
cd ./workspace

mkdir -p $COMMIT_SHA
cd $COMMIT_SHA

git clone --depth 1 https://github.com/$STACK_ORG/$STACK_REPO.git .
git fetch --depth 1 origin $COMMIT_SHA
git checkout $COMMIT_SHA
