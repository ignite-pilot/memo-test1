#!/usr/bin/env python3
"""Test script to verify AWS Secrets Manager connectivity."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.secrets import get_github_token, get_postgres_credentials
import requests
from sqlalchemy import create_engine, text

def test_github_token():
    """Test GitHub token retrieval and API access."""
    print("=" * 60)
    print("Testing GitHub Token from AWS Secrets Manager")
    print("=" * 60)
    
    token = get_github_token()
    if not token:
        print("❌ Failed to retrieve GitHub token from AWS Secrets Manager")
        print("   Trying environment variable...")
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ACCESS_TOKEN")
        if not token:
            print("❌ GitHub token not found in environment variables either")
            return False
    
    print(f"✅ GitHub token retrieved (length: {len(token)})")
    
    # Test GitHub API access
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ GitHub API access successful")
            print(f"   Authenticated as: {user_data.get('login', 'Unknown')}")
            return True
        else:
            print(f"❌ GitHub API access failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error accessing GitHub API: {e}")
        return False


def test_postgres_credentials():
    """Test PostgreSQL credentials retrieval and database connection."""
    print("\n" + "=" * 60)
    print("Testing PostgreSQL Credentials from AWS Secrets Manager")
    print("=" * 60)
    
    credentials = get_postgres_credentials()
    if not credentials:
        print("❌ Failed to retrieve PostgreSQL credentials from AWS Secrets Manager")
        print("   Trying environment variables...")
        credentials = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT", "5432"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD"),
            "dbname": os.getenv("DB_NAME")
        }
        if not credentials.get("host") or not credentials.get("password") or not credentials.get("dbname"):
            print("❌ PostgreSQL credentials not found in environment variables either")
            return False
    
    print(f"✅ PostgreSQL credentials retrieved")
    print(f"   Host: {credentials.get('host')}")
    print(f"   Port: {credentials.get('port')}")
    print(f"   User: {credentials.get('user')}")
    print(f"   Database: {credentials.get('dbname')}")
    
    # Test database connection
    try:
        db_url = f"postgresql://{credentials['user']}:{credentials['password']}@{credentials['host']}:{credentials['port']}/{credentials['dbname']}"
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Database connection successful")
            print(f"   PostgreSQL version: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_aws_credentials():
    """Check if AWS credentials are configured."""
    print("\n" + "=" * 60)
    print("Checking AWS Credentials")
    print("=" * 60)
    
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    aws_region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")
    
    if aws_access_key:
        print(f"✅ AWS_ACCESS_KEY_ID is set (length: {len(aws_access_key)})")
    else:
        print("❌ AWS_ACCESS_KEY_ID is not set")
    
    if aws_secret_key:
        print(f"✅ AWS_SECRET_ACCESS_KEY is set (length: {len(aws_secret_key)})")
    else:
        print("❌ AWS_SECRET_ACCESS_KEY is not set")
    
    if aws_session_token:
        print(f"✅ AWS_SESSION_TOKEN is set (for temporary credentials)")
    else:
        print("ℹ️  AWS_SESSION_TOKEN is not set (not using temporary credentials)")
    
    print(f"ℹ️  AWS Region: {aws_region}")
    
    # Try to get caller identity
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials are valid")
        print(f"   Account: {identity.get('Account', 'Unknown')}")
        print(f"   User/Role: {identity.get('Arn', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ AWS credentials validation failed: {e}")
        print("\n💡 To configure AWS credentials:")
        print("   1. Set environment variables:")
        print("      export AWS_ACCESS_KEY_ID=your_access_key")
        print("      export AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("      export AWS_DEFAULT_REGION=ap-northeast-2")
        print("   2. Or use AWS CLI: aws configure")
        print("   3. Or use IAM role (if running on EC2/ECS/Lambda)")
        return False


def main():
    """Run all tests."""
    print("\n🔍 Testing AWS Secrets Manager Integration\n")
    
    # Check if AWS secrets should be used
    use_aws_secrets = os.getenv("USE_AWS_SECRETS", "false").lower() == "true"
    if use_aws_secrets:
        print("ℹ️  USE_AWS_SECRETS=true - Using AWS Secrets Manager")
        aws_ok = check_aws_credentials()
        if not aws_ok:
            print("\n⚠️  AWS credentials not configured. Tests will fail.")
            print("   Set USE_AWS_SECRETS=false to test with environment variables instead.\n")
    else:
        print("ℹ️  USE_AWS_SECRETS=false - Using environment variables")
        print("   Set USE_AWS_SECRETS=true to test AWS Secrets Manager\n")
    
    github_ok = test_github_token()
    postgres_ok = test_postgres_credentials()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"GitHub Token: {'✅ PASS' if github_ok else '❌ FAIL'}")
    print(f"PostgreSQL:   {'✅ PASS' if postgres_ok else '❌ FAIL'}")
    
    if github_ok and postgres_ok:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

