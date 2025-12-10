"""Main FastAPI application."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from app.routers import health, memos
from app.database import init_db

# Load environment variables - check PHASE first
PHASE = os.getenv("PHASE", "local")
config_file = f"config/config.{PHASE}.env"
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), f"../../{config_file}"))
# Fallback to local if phase config doesn't exist
if not os.path.exists(os.path.join(os.path.dirname(__file__), f"../../{config_file}")):
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../config/config.local.env"))

# Get frontend domain from config
FRONTEND_DOMAIN = os.getenv("FRONTEND_DOMAIN", "http://localhost:8500")

app = FastAPI(
    title="Memo API",
    description="Simple memo taking application API",
    version="1.0.0"
)

# CORS configuration - allow all origins when serving from same server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Same origin, so allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router)
app.include_router(memos.router)

# Serve static files from frontend build directory
static_dir = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
if os.path.exists(static_dir):
    # Mount static files (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    # Serve index.html for root path
    @app.get("/")
    async def serve_root():
        """Serve React app for root path."""
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"detail": "Frontend not built"}
    
    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React app for all non-API routes."""
        # Don't serve index.html for API routes
        if full_path.startswith("api/"):
            return {"detail": "Not found"}
        
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"detail": "Frontend not built"}


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()

