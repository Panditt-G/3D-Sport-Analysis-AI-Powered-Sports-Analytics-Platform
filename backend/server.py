"""Backend API Server for Sports AI Analytics Platform."""
import os
import sys

# Add project root to path so imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from ai_engine.registry import SportRegistry
import sports  # Initializes and registers all sports

from backend.services.config_service import config_service
from backend.services.video_service import VideoService
from backend.services.analysis_service import AnalysisService

# Initialize services
video_service = VideoService(
    upload_dir=config_service.upload_dir,
    allowed_extensions=config_service.allowed_extensions,
    max_size_mb=config_service.max_file_size_mb,
)
analysis_service = AnalysisService(output_dir=config_service.output_dir)

# Create FastAPI app
app = FastAPI(title="Sports AI Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API ROUTES ---

@app.get("/api")
def api_root():
    """API health check."""
    return {"message": "Sports AI Analytics Platform API running", "version": "1.0.0"}


@app.get("/api/sports")
def list_sports():
    """List all registered sports with details."""
    return {"sports": SportRegistry.get_all_sports_info()}


@app.get("/api/sports/{sport_name}")
def get_sport_detail(sport_name: str):
    """Get detailed info about a specific sport."""
    if not SportRegistry.is_registered(sport_name):
        raise HTTPException(status_code=404, detail=f"Sport '{sport_name}' not found")

    sport_info = SportRegistry.get_sport_info(sport_name)
    sport_config = config_service.get_sport_config(sport_name)

    return {
        "sport": sport_info,
        "config": sport_config,
    }


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for analysis."""
    # Validate file
    content = await file.read()
    is_valid, error_msg = video_service.validate_file(file.filename, len(content))
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Save file
    save_result = video_service.save_upload(content, file.filename)

    # Get video info
    video_info = video_service.get_video_info(save_result["saved_path"])

    return {
        "success": True,
        "filename": save_result["saved_filename"],
        "original_filename": save_result["original_filename"],
        "file_path": save_result["saved_path"],
        "file_size_mb": save_result["file_size_mb"],
        "video_info": video_info,
    }


@app.post("/api/analyze/{sport_name}")
async def analyze_video(sport_name: str, file: UploadFile = File(...)):
    """Upload and analyze a video for a specific sport."""
    if not SportRegistry.is_registered(sport_name):
        raise HTTPException(status_code=404, detail=f"Sport '{sport_name}' not registered")

    # Save uploaded file
    content = await file.read()
    is_valid, error_msg = video_service.validate_file(file.filename, len(content))
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    save_result = video_service.save_upload(content, file.filename)

    # Get sport config
    sport_config = config_service.get_sport_config(sport_name)

    # Run analysis
    result = analysis_service.analyze_video(
        video_path=save_result["saved_path"],
        sport_name=sport_name,
        config=sport_config,
    )

    return result


@app.get("/api/results/{session_id}")
def get_results(session_id: str):
    """Get analysis results by session ID."""
    result = analysis_service.get_result(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return result


@app.get("/api/sessions")
def list_sessions():
    """List all analysis sessions."""
    return {"sessions": analysis_service.list_sessions()}


# --- SERVE FRONTEND (React Build Support) ---

dist_dir = os.path.join(PROJECT_ROOT, "frontend", "dist")
assets_dir = os.path.join(dist_dir, "assets")

if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/{full_path:path}")
def serve_react_app(full_path: str):
    """Serve React frontend single-page application."""
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    dist_index = os.path.join(dist_dir, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    return {"message": "Sports AI Analytics Platform API running. Start React dev server via 'npm run dev' inside frontend/"}

