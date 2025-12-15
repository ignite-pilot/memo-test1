"""Database configuration and session management."""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.secrets import get_postgres_credentials

# Load environment variables - check PHASE first
PHASE = os.getenv("PHASE", "local")
config_file = f"config/config.{PHASE}.env"
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), f"../../{config_file}"))
# Fallback to local if phase config doesn't exist
if not os.path.exists(os.path.join(os.path.dirname(__file__), f"../../{config_file}")):
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../config/config.local.env"))

# Get database credentials from AWS Secrets Manager or environment variables
postgres_secret = get_postgres_credentials()

if postgres_secret:
    # AWS Secrets Manager is available - use it
    DB_HOST = postgres_secret.get("host")
    DB_PORT = postgres_secret.get("port") or "5432"
    DB_USER = postgres_secret.get("user")
    DB_PASSWORD = postgres_secret.get("password")
    DB_NAME = postgres_secret.get("dbname") or os.getenv("DB_NAME", "memo-test1")
else:
    # Fallback to environment variables (for local development, testing, or non-AWS environments)
    print("⚠️  AWS Secrets Manager not available, using environment variables")

    # Try to parse DATABASE_URL if provided
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Parse DATABASE_URL: postgresql://user:password@host:port/dbname
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if match:
            DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = match.groups()
        else:
            raise ValueError(
                "Invalid DATABASE_URL format. Expected: postgresql://user:password@host:port/dbname"
            )
    else:
        # Use individual environment variables
        DB_HOST = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "localhost"))
        DB_PORT = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432"))
        DB_USER = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres"))
        DB_PASSWORD = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", ""))
        DB_NAME = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "memo-test1"))

# Validate required database configuration
if not DB_HOST or not DB_USER or not DB_PASSWORD or not DB_NAME:
    missing = []
    if not DB_HOST:
        missing.append("DB_HOST")
    if not DB_USER:
        missing.append("DB_USER")
    if not DB_PASSWORD:
        missing.append("DB_PASSWORD")
    if not DB_NAME:
        missing.append("DB_NAME")
    raise ValueError(
        f"Database configuration is incomplete. Missing: {', '.join(missing)}. "
        f"Please ensure AWS Secrets Manager 'prod/ignite-pilot/postgresInfo2' "
        f"contains all required fields: DB_HOST, DB_USER, DB_PASSWORD."
    )

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Initialize database and create tables."""
    try:
        # Try to create database if it doesn't exist
        # Sanitize database name to prevent SQL injection
        safe_db_name = DB_NAME.replace("'", "").replace(";", "").replace("--", "")
        admin_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        
        with admin_engine.connect() as conn:
            # Use parameterized query for checking database existence
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": safe_db_name}
            )
            if not result.fetchone():
                # Database name must be identifier, not parameter
                # Validate it contains only safe characters
                if safe_db_name.replace("_", "").isalnum():
                    conn.execute(text(f'CREATE DATABASE "{safe_db_name}"'))
        admin_engine.dispose()
    except Exception as e:
        # Database might already exist or connection issue
        print(f"Database creation check: {e}")
    
    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Table creation: {e}")


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

