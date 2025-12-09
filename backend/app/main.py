"""Main FastAPI application."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import health, memos
from app.database import init_db

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../config/config.local.env"))

# Get frontend domain from config
FRONTEND_DOMAIN = os.getenv("FRONTEND_DOMAIN", "http://localhost:8500")

app = FastAPI(
    title="Memo API",
    description="Simple memo taking application API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_DOMAIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(memos.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()

