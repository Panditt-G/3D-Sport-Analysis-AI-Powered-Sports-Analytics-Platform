# 3D-Sport-Analysis-AI-Powered-Sports-Analytics-Platform
AI-powered sports analytics platform for athlete movement, pose, tracking, and sport-specific performance analysis.

# 🏆 Sports AI Analytics Platform

A modular, plug-and-play **Computer Vision & Biomechanics Analytics Platform** designed for multi-sport video analysis using **Python, MediaPipe, OpenCV, FastAPI, React 18, and Tailwind CSS v3**.

---

## ✨ Features

- 🎯 **Multi-Sport Support**: Pre-built pipelines for **Cricket, Running, Basketball, Football, and Volleyball**.
- 🧩 **Plug-and-Play Architecture**: Add any new sport in just **3 simple steps** using standard decorators and base classes.
- 📐 **Biomechanics & Pose Analysis**:
  - Full 33-point MediaPipe BlazePose landmark extraction.
  - Joint angle calculation (knees, hips, ankles, elbows).
  - Temporal state-machine gait phase detection (Foot Contact, Stance, Toe-Off, Swing).
  - Exponential Moving Average (EMA) landmark jitter smoothing.
- ⚡ **FastAPI REST Backend**: Fast, lightweight API endpoints for video upload, analysis execution, and session history.
- 🎨 **React + Tailwind CSS v3 Frontend**: Modern, responsive dashboard with drag-and-drop video upload, real-time metrics, video metadata, and frame-by-frame telemetry inspection.

---

## 📁 Repository Structure

```
.
├── ai_engine/                 # Core AI engine & biomechanics modules
│   ├── base/                  # Abstract Base Classes (BaseSportPipeline, BaseSportAnalytics)
│   ├── common/                # Shared utilities (video capture, preprocessing, visualization, config loader)
│   ├── pose_analysis/         # Landmarks, joint angles, motion phase detector, EMA smoother
│   ├── validation/            # Sport module compliance validator
│   └── registry.py            # Dynamic SportRegistry for auto-discovery
├── backend/                   # FastAPI REST API backend
│   ├── models/                # Pydantic schemas
│   ├── services/              # Config, Video, and Analysis orchestration services
│   └── server.py              # Main FastAPI application
├── frontend/                  # React 18 + Vite + Tailwind CSS v3 dashboard
│   ├── src/
│   │   ├── components/        # React components (Header, SportSelector, VideoUploader, ResultsDashboard, PastSessions)
│   │   ├── services/          # API fetch client
│   │   ├── App.jsx            # Main React layout
│   │   └── index.css          # Tailwind CSS directives
│   ├── index.html             # Vite root HTML
│   ├── package.json           # Frontend dependencies
│   ├── tailwind.config.js     # Tailwind CSS v3 configuration
│   └── vite.config.js         # Vite dev server & API proxy
├── sports/                    # Plug-and-play sport implementations
│   ├── _template/             # Template directory for creating new sports
│   ├── cricket/               # Cricket bowling & batting pipeline
│   ├── running/               # Running gait analysis pipeline
│   ├── basketball/            # Basketball shot & tracking pipeline
│   ├── football/              # Football player tracking pipeline
│   └── volleyball/            # Volleyball spike & jump height pipeline
├── configs/                   # YAML configurations for global app & per-sport parameters
└── data/                      # Local video raw uploads and JSON output results
```

---

## ⚡ Quickstart & Setup Guide

### Prerequisites
- **Python**: 3.10+ (Tested on Python 3.14)
- **Node.js**: 18+ & **npm**

---

### 1. Backend Setup (FastAPI)

1. **Create and activate a Python Virtual Environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Backend Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(For CPU-only PyTorch optimization)*:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```

3. **Start FastAPI Backend Server**:
   ```bash
   python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be live at `http://127.0.0.1:8000/api`.

---

### 2. Frontend Setup (React + Tailwind CSS v3)

1. **Navigate to `frontend/` directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start Vite React Development Server**:
   ```bash
   npm run dev
   ```
   Open **`http://localhost:5173`** in your browser!

---

## 🚀 Adding a New Sport in 3 Steps

The platform uses automatic plugin discovery. Adding a new sport (e.g. `tennis`) takes only 3 steps:

1. **Copy the template**:
   ```bash
   cp -r sports/_template sports/tennis
   ```

2. **Implement your pipeline & analytics**:
   - Inherit `BaseSportPipeline` in `sports/tennis/pipeline.py` and decorate:
     ```python
     @SportRegistry.register_pipeline("tennis")
     class TennisPipeline(BaseSportPipeline):
         ...
     ```
   - Inherit `BaseSportAnalytics` in `sports/tennis/analytics.py` and decorate:
     ```python
     @SportRegistry.register_analytics("tennis")
     class TennisAnalytics(BaseSportAnalytics):
         ...
     ```

3. **Add configuration file** in `configs/tennis.yaml`.

*Your new sport will be automatically discovered and shown in the React frontend and FastAPI backend API!*

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sports` | List all registered sports with metadata |
| `GET` | `/api/sports/{name}` | Get detailed configuration & metadata for a sport |
| `POST` | `/api/upload` | Upload video file for validation |
| `POST` | `/api/analyze/{sport}` | Execute full AI pipeline on uploaded video |
| `GET` | `/api/results/{id}` | Retrieve results by session ID |
| `GET` | `/api/sessions` | List all past analysis sessions |

---

## 📜 License

MIT License. Designed for AI & Sports Analytics projects.
