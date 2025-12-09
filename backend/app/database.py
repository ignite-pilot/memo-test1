"""Database configuration and session management."""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../config/config.local.env"))

# Database URL from environment or default
DB_HOST = os.getenv("DB_HOST", "aidev-pgvector-dev.crkgaskg6o61.ap-northeast-2.rds.amazonaws.com")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "vmcMrs75!KZHk2johkRR:]wL")
DB_NAME = os.getenv("DB_NAME", "memo_test1")

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

