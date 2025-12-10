#!/usr/bin/env python3
"""Script to get GitHub token from AWS Secrets Manager for deployment."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.secrets import get_github_token

if __name__ == "__main__":
    token = get_github_token()
    if token:
        print(token)
        sys.exit(0)
    else:
        # Fallback to environment variable
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ACCESS_TOKEN")
        if token:
            print(token)
            sys.exit(0)
        else:
            print("GitHub token not found in AWS Secrets Manager or environment variables", file=sys.stderr)
            sys.exit(1)

