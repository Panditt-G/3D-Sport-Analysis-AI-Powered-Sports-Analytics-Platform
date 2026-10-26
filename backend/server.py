import os
import sys
import json

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
from backend.services.job_service import JobService

# Initialize services
video_service = VideoService(
    upload_dir=config_service.upload_dir,
    allowed_extensions=config_service.allowed_extensions,
    max_size_mb=config_service.max_file_size_mb,
)
analysis_service = AnalysisService(output_dir=config_service.output_dir)
job_service = JobService(output_dir=config_service.output_dir)

# Create FastAPI app
app = FastAPI(title="Multi-Sport AI Analytics & Correction Platform", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure output directory exists and mount static outputs for legacy video access
os.makedirs(config_service.output_dir, exist_ok=True)
app.mount("/api/outputs", StaticFiles(directory=config_service.output_dir), name="outputs")


# --- V1 REST API ROUTES ---

@app.get("/api/v1/health")
def api_v1_health():
    """Health check endpoint."""
    return {"status": "ok", "platform": "Multi-Sport AI Analytics", "version": "2.0.0"}


@app.get("/api/v1/sports")
def list_v1_sports():
    """List all supported sport packs."""
    packs_info = []
    for s_name, pack in job_service.sport_packs.items():
        packs_info.append(pack.get_info())
    # Include other registered sports
    for reg_sport in SportRegistry.available_sports():
        if reg_sport not in job_service.sport_packs:
            packs_info.append({
                "name": reg_sport,
                "display_name": reg_sport.replace("_", " ").title(),
                "version": "1.0.0",
                "supported_movements": ["general"],
                "default_pose_model": "mediapipe_blazepose",
            })
    return {"sports": packs_info}


@app.get("/api/v1/sports/{sport_name}/movements")
def get_v1_sport_movements(sport_name: str):
    """List supported movements and camera views for a sport."""
    if sport_name in job_service.sport_packs:
        pack = job_service.sport_packs[sport_name]
        return {
            "sport": sport_name,
            "manifest": pack.manifest,
            "movements": pack.manifest.get("supported_movements", {}),
            "camera_views": pack.manifest.get("supported_camera_views", []),
        }
    raise HTTPException(status_code=404, detail=f"Sport pack '{sport_name}' not found")


@app.get("/api/v1/references/{sport_name}/{movement_name}")
def get_v1_reference(sport_name: str, movement_name: str):
    """Retrieve coach-approved benchmark references for a movement."""
    if sport_name in job_service.sport_packs:
        pack = job_service.sport_packs[sport_name]
        ref = pack.references.get(movement_name)
        if ref:
            return ref
    raise HTTPException(status_code=404, detail=f"Reference for '{sport_name}/{movement_name}' not found")


@app.post("/api/v1/analyses")
async def create_v1_analysis(
    file: UploadFile = File(...),
    sport: str = "badminton",
    movement: str = "overhead_clear",
    pose_model: str = "mediapipe",
):
    """Upload video and create an asynchronous analysis job."""
    content = await file.read()
    is_valid, error_msg = video_service.validate_file(file.filename, len(content))
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    save_result = video_service.save_upload(content, file.filename)
    job = job_service.create_job(
        video_path=save_result["saved_path"],
        sport_name=sport,
        movement_name=movement,
        pose_model=pose_model,
    )

    return {
        "job_id": job["id"],
        "status": job["status"],
        "stage": job["stage"],
        "sport": sport,
        "movement": movement,
        "filename": save_result["saved_filename"],
        "message": "Analysis job accepted and processing in background.",
    }


@app.get("/api/v1/analyses/{job_id}")
def get_v1_analysis_status(job_id: str):
    """Get status and progress of an analysis job."""
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Analysis job '{job_id}' not found")

    return {
        "id": job["id"],
        "status": job["status"],
        "progress_pct": job["progress_pct"],
        "stage": job["stage"],
        "sport": job["sport"],
        "movement": job["movement"],
        "error": job["error"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
    }


@app.get("/api/v1/analyses/{job_id}/results")
def get_v1_analysis_results(job_id: str):
    """Get complete results (metrics, phases, 5-point corrections) for a job."""
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Analysis job '{job_id}' not found")
    if job["status"] != "completed":
        return {
            "status": job["status"],
            "progress_pct": job["progress_pct"],
            "stage": job["stage"],
            "results": None,
        }
    return {
        "status": job["status"],
        "results": job["results"],
    }


@app.get("/api/v1/analyses/{job_id}/video")
def get_v1_analysis_video(job_id: str):
    """Stream or download the rendered annotated MP4."""
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Analysis job '{job_id}' not found")
    video_path = job.get("artifacts", {}).get("annotated_video")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Annotated video not available yet")
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"{job_id}_annotated.mp4",
        headers={"Accept-Ranges": "bytes"},
    )


@app.get("/api/v1/analyses/{job_id}/pose")
def get_v1_analysis_pose(job_id: str):
    """Retrieve full frame-by-frame pose landmarks for frontend interactive overlay."""
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Analysis job '{job_id}' not found")
    pose_path = job.get("artifacts", {}).get("pose_json")
    if not pose_path or not os.path.exists(pose_path):
        raise HTTPException(status_code=404, detail="Pose landmarks not available yet")
    with open(pose_path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- LEGACY API ROUTES (For backwards compatibility) ---

@app.get("/api")
def api_root():
    """API health check."""
    return {"message": "Sports AI Analytics Platform API running", "version": "2.0.0"}


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
