#!/bin/bash
# Git push script using AWS Secrets Manager for GitHub token

set -e

export USE_AWS_SECRETS=true
GITHUB_TOKEN=$(python3 scripts/get_github_token.py)

if [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ Failed to get GitHub token from AWS Secrets Manager"
  exit 1
fi

# Update remote URL with token from AWS Secrets Manager
git remote set-url origin "https://${GITHUB_TOKEN}@github.com/ignite-pilot/memo-test1.git"

# Push to remote
echo "📤 Pushing to GitHub..."
git push "$@"
