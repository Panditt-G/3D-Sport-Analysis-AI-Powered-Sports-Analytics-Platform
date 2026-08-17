"""Pydantic models for API request/response validation."""
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime


class SportInfo(BaseModel):
    """Sport information response."""
    name: str
    display_name: str
    description: str
    icon: str
    metrics: List[str]
    has_pipeline: bool
    has_analytics: bool


class UploadResponse(BaseModel):
    """Response after video upload."""
    success: bool
    filename: str
    file_path: str
    file_size_mb: float
    video_info: Dict[str, Any]


class AnalysisRequest(BaseModel):
    """Request to start analysis."""
    video_path: str
    sport: str
    config_overrides: Optional[Dict[str, Any]] = None


class AnalysisResult(BaseModel):
    """Analysis result response."""
    session_id: str
    sport: str
    status: str
    video_info: Dict[str, Any]
    frame_results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: str
