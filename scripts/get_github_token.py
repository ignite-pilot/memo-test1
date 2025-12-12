#!/usr/bin/env python3
"""Script to get GitHub token from AWS Secrets Manager for deployment."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.secrets import get_github_token

if __name__ == "__main__":
    # Always try AWS Secrets Manager first
    use_aws_secrets = os.getenv("USE_AWS_SECRETS", "false").lower() == "true"
    if not use_aws_secrets:
        # Check if running in AWS environment
        aws_env_indicators = [
            os.getenv("AWS_EXECUTION_ENV"),
            os.getenv("ECS_CONTAINER_METADATA_URI"),
            os.getenv("LAMBDA_TASK_ROOT"),
        ]
        if any(aws_env_indicators):
            use_aws_secrets = True
        else:
            # For local development, allow environment variable fallback
            token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ACCESS_TOKEN")
            if token:
                print(token)
                sys.exit(0)
    
    if use_aws_secrets:
        os.environ["USE_AWS_SECRETS"] = "true"
    
    token = get_github_token()
    if token:
        print(token)
        sys.exit(0)
    else:
        print("GitHub token not found in AWS Secrets Manager", file=sys.stderr)
        sys.exit(1)

