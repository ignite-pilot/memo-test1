"""AWS Secrets Manager integration for secure credential management."""
import os
import json
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any


def get_secret(secret_name: str, region_name: str = "ap-northeast-2") -> Optional[Dict[str, Any]]:
    """
    Retrieve secret from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in AWS Secrets Manager
        region_name: AWS region name (default: ap-northeast-2)
    
    Returns:
        Dictionary containing secret values, or None if retrieval fails
    """
    # Only use AWS Secrets Manager if running in AWS environment
    # Check for AWS credentials or if explicitly enabled
    use_aws_secrets = os.getenv("USE_AWS_SECRETS", "false").lower() == "true"
    
    # In local development, fall back to environment variables
    if not use_aws_secrets:
        return None
    
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        
        # Parse the secret string (could be JSON or plain text)
        secret_string = get_secret_value_response['SecretString']
        try:
            return json.loads(secret_string)
        except json.JSONDecodeError:
            # If not JSON, return as plain text
            return {"value": secret_string}
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error'].get('Message', '')
        if error_code == 'ResourceNotFoundException':
            print(f"❌ Secret '{secret_name}' not found in AWS Secrets Manager")
            print(f"   Please verify the secret name exists in region {region_name}")
        elif error_code == 'InvalidRequestException':
            print(f"❌ Invalid request for secret '{secret_name}': {error_message}")
        elif error_code == 'InvalidParameterException':
            print(f"❌ Invalid parameter for secret '{secret_name}': {error_message}")
        elif error_code == 'DecryptionFailureException':
            print(f"❌ Decryption failure for secret '{secret_name}': {error_message}")
        elif error_code == 'AccessDeniedException':
            print(f"❌ Access denied for secret '{secret_name}'")
            print(f"   Current IAM role/user may not have permission to access this secret")
        elif error_code == 'InternalServiceErrorException':
            print(f"❌ Internal service error for secret '{secret_name}': {error_message}")
        else:
            print(f"❌ Error retrieving secret '{secret_name}': {error_code} - {error_message}")
        return None
    except Exception as e:
        print(f"Unexpected error retrieving secret {secret_name}: {e}")
        return None


def get_github_token() -> Optional[str]:
    """
    Get GitHub Personal Access Token from AWS Secrets Manager.
    
    Returns:
        GitHub token string, or None if not found
    """
    secret = get_secret("prod/ignite-pilot/github")
    if secret:
        # Try various possible key names (prioritize GITHUB-PAT format)
        return (secret.get("GITHUB-PAT") or secret.get("GITHUB_PAT") or 
                secret.get("token") or secret.get("github_token") or 
                secret.get("GITHUB_TOKEN") or secret.get("githubToken") or
                secret.get("value"))
    return None


def get_postgres_credentials() -> Optional[Dict[str, str]]:
    """
    Get PostgreSQL credentials from AWS Secrets Manager.
    
    Returns:
        Dictionary with keys: host, port, user, password, dbname
    """
    secret = get_secret("prod/ignite-pilot/postgresInfo")
    if secret:
        # Debug: print available keys (only in debug mode)
        if os.getenv("DEBUG_SECRETS", "false").lower() == "true":
            print(f"🔍 Available keys in secret: {list(secret.keys())}")
        
        # Try various possible key names (prioritize DB_* format)
        # DB_NAME might not be in secret, so fallback to environment variable or project name
        db_name = (secret.get("DB_NAME") or secret.get("DBNAME") or secret.get("dbname") or 
                  secret.get("database") or secret.get("DATABASE") or secret.get("DbName") or 
                  secret.get("Database") or secret.get("dbName") or secret.get("db_name") or
                  os.getenv("DB_NAME", "memo_test1"))
        
        return {
            "host": (secret.get("DB_HOST") or secret.get("host") or secret.get("HOST") or 
                    secret.get("hostname") or secret.get("Host") or secret.get("HOSTNAME") or 
                    secret.get("endpoint") or secret.get("Endpoint") or secret.get("address") or 
                    secret.get("Address")),
            "port": (secret.get("DB_PORT") or secret.get("port") or secret.get("PORT") or 
                    secret.get("Port") or "5432"),
            "user": (secret.get("DB_USER") or secret.get("user") or secret.get("USER") or 
                    secret.get("username") or secret.get("USERNAME") or secret.get("User") or 
                    secret.get("Username") or secret.get("dbUser") or secret.get("db_user")),
            "password": (secret.get("DB_PASSWORD") or secret.get("password") or 
                        secret.get("PASSWORD") or secret.get("Password") or
                        secret.get("dbPassword") or secret.get("db_password")),
            "dbname": db_name
        }
    return None

