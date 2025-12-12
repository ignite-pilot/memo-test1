#!/usr/bin/env python3
"""Script to create database using credentials from AWS Secrets Manager."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.secrets import get_postgres_credentials
from sqlalchemy import create_engine, text

def create_database():
    """Create database if it doesn't exist."""
    print("=" * 60)
    print("Creating Database")
    print("=" * 60)
    
    # Get credentials from AWS Secrets Manager
    use_aws_secrets = os.getenv("USE_AWS_SECRETS", "false").lower() == "true"
    if not use_aws_secrets:
        print("⚠️  USE_AWS_SECRETS is not set to true")
        print("   Set USE_AWS_SECRETS=true to use AWS Secrets Manager")
        return False
    
    credentials = get_postgres_credentials()
    if not credentials:
        print("❌ Failed to retrieve PostgreSQL credentials")
        return False
    
    host = credentials.get("host")
    port = credentials.get("port", "5432")
    user = credentials.get("user", "postgres")
    password = credentials.get("password")
    db_name = credentials.get("dbname") or os.getenv("DB_NAME", "memo_test1")
    
    if not host or not password or not db_name:
        print("❌ Missing required database credentials")
        return False
    
    print(f"📊 Database Configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   User: {user}")
    print(f"   Database: {db_name}")
    
    try:
        # Connect to postgres database to create target database
        admin_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        
        with admin_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if result.fetchone():
                print(f"✅ Database '{db_name}' already exists")
            else:
                # Create database
                print(f"📝 Creating database '{db_name}'...")
                # Sanitize database name
                safe_db_name = db_name.replace("'", "").replace(";", "").replace("--", "")
                if safe_db_name.replace("_", "").isalnum():
                    conn.execute(text(f'CREATE DATABASE "{safe_db_name}"'))
                    print(f"✅ Database '{db_name}' created successfully")
                else:
                    print(f"❌ Invalid database name: {db_name}")
                    return False
        
        admin_engine.dispose()
        
        # Test connection to the new database
        print(f"\n🔍 Testing connection to database '{db_name}'...")
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        test_engine = create_engine(db_url, pool_pre_ping=True)
        
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connection successful")
            print(f"   PostgreSQL version: {version[:50]}...")
        
        test_engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False


if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)

