"""Backend API Server for Sports AI Analytics Platform."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_engine.registry import SportRegistry
import sports  # Initializes and registers all sports

app = FastAPI(title="Sports AI Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Sports AI Analytics Platform API running"}

@app.get("/sports")
def list_sports():
    """List all registered sports dynamically."""
    return {"available_sports": SportRegistry.available_sports()}
