# 3D-Sport-Analysis — AI-Powered Sports Analytics Platform

> **v2.0 — Multi-Sport Biomechanics, Pose Estimation & Technique Correction Engine**

An end-to-end **Computer Vision & Sports Biomechanics Platform** built with **Python, MediaPipe, YOLOv8, OpenCV, FastAPI, React 18, and Tailwind CSS v3**. Upload athlete footage, extract full-body skeleton landmarks, segment stroke phases, compare against coach-approved references, and receive actionable 5-point technique correction cards — all in one pipeline.

---

## ✨ What's New in v2.0

| Feature | v1.0 | v2.0 |
|---|---|---|
| Pose Backend | MediaPipe Tasks API only | **MediaPipe BlazePose + YOLOv8n-pose** (user selectable) |
| Analysis Flow | Synchronous — blocks on upload | **Async job queue** with real-time progress polling |
| Correction Engine | None | **5-pillar biomechanics rule evaluator** vs coach references |
| Video Output | Raw OpenCV `mp4v` | **H.264 + faststart** transcoded via FFmpeg (browser-native) |
| Frontend Player | Simple `<video>` tag | **Interactive synchronized player** with phase scrubber & speed control |
| Sport Pack Architecture | `sports/` plugins only | `sports/` (legacy) + **`sport_packs/`** (full analysis packs with rules & references) |
| API Versioning | `/api/*` legacy only | **`/api/v1/*`** suite + backwards-compatible `/api/*` legacy |

---

## 🏗 Repository Structure

```
.
├── ai_engine/                        # Core AI engine
│   ├── base/                         # Abstract Base Classes (BaseSportPipeline, BaseSportAnalytics)
│   ├── common/                       # Shared utilities: VideoCapture, preprocessing, visualization
│   ├── correction/
│   │   └── rule_evaluator.py         # 5-pillar biomechanics correction engine
│   ├── pose_analysis/                # Legacy: landmarks, joint angles, motion phases, EMA smoother
│   ├── rendering/
│   │   └── video_renderer.py         # Ghost reference overlay + HUD annotation renderer
│   ├── validation/                   # Sport module compliance validator
│   ├── vision/
│   │   ├── pose/
│   │   │   ├── base_pose.py          # Unified PoseFrame / Keypoint abstraction
│   │   │   ├── mediapipe_adapter.py  # MediaPipe BlazePose → standard PoseFrame adapter
│   │   │   ├── mediapipe_pose.py     # MediaPipe Tasks API wrapper (Python 3.13 compatible)
│   │   │   ├── yolo_pose.py          # YOLOv8-pose → standard PoseFrame adapter
│   │   │   └── pose_benchmark.py     # Pose benchmarking utilities
│   │   ├── detection/                # YOLO object detection test scripts
│   │   └── tracking/                 # ByteTrack multi-object tracking
│   └── registry.py                   # Dynamic SportRegistry for auto-discovery
│
├── backend/
│   ├── models/
│   │   ├── detector.py               # BadmintonDetector (shuttlecock & racket)
│   │   └── schemas.py                # Pydantic response schemas
│   ├── services/
│   │   ├── analysis_service.py       # Legacy synchronous analysis orchestrator
│   │   ├── config_service.py         # App configuration loader
│   │   ├── job_service.py            # Async job queue coordinator (v2 pipeline)
│   │   └── video_service.py          # Video upload, validation, metadata
│   └── server.py                     # FastAPI app — /api/v1/* + /api/* legacy routes
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                   # Main layout, state, analysis flow
│   │   ├── index.css                 # Tailwind directives + dark scrollbar
│   │   ├── components/
│   │   │   ├── Header.jsx            # Sticky navbar
│   │   │   ├── SportSelector.jsx     # Sport card picker + movement + pose model selector
│   │   │   ├── VideoUploader.jsx     # Drag-and-drop ingest with progress bar
│   │   │   ├── InteractivePlayer.jsx # Synced video player: phases, speed control, ghost toggle
│   │   │   ├── ResultsDashboard.jsx  # Biomechanics metrics + correction cards display
│   │   │   ├── CorrectionCard.jsx    # 5-pillar technique feedback card component
│   │   │   └── PastSessions.jsx      # Session history browser
│   │   └── services/
│   │       └── api.js                # API client: v1 job polling + legacy fallback
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js                # Dev proxy → localhost:8000
│
├── sports/                           # Legacy plug-and-play sport implementations
│   ├── badminton/                    # Equipment detection pipeline (badminton_detector_v1.pt)
│   └── running/                      # Running gait analysis pipeline
│
├── sport_packs/                      # v2 Sport Pack architecture (full biomechanics packs)
│   └── badminton/
│       ├── pack.yaml                 # Pack manifest & supported movements
│       ├── plugin.py                 # BadmintonSportPack: analyze_sequence(), references
│       ├── movements/
│       │   └── overhead_clear.py     # Phase detector + kinematics for overhead clear stroke
│       ├── references/
│       │   └── overhead_clear_ref.json  # Coach-approved benchmark angles & ghost poses
│       └── rules/
│           └── overhead_clear_rules.yaml  # Technique evaluation rules (5 pillars)
│
├── model/
│   └── badminton_detector_v1.pt      # Custom-trained YOLOv8 badminton equipment detector (21.5 MB)
│
├── configs/                          # YAML app & sport configuration files
├── data/                             # Local uploads and per-job output artifacts
│   ├── raw/                          # Uploaded raw videos
│   └── outputs/
│       └── job_{id}/                 # Per-job artifacts: annotated.mp4, pose.json, metrics.json, analysis.json
│
├── tests/
│   ├── test_api_v1.py                # V1 REST API endpoint tests
│   ├── test_badminton_pipeline.py    # Sport pack, rule evaluator, video renderer tests
│   ├── test_full_workflow.py         # End-to-end integration test (upload → analyze → results → video)
│   └── test_ai/
│       └── test_running_metrics_unit.py
│
├── notebooks/                        # Learning notebooks (Python, NumPy, OpenCV, PyTorch, YOLO, Tracking, Pose)
├── pose_landmarker_full.task         # MediaPipe BlazePose 3D model (9 MB)
├── yolov8n-pose.pt                   # YOLOv8n pose estimation weights (6.5 MB)
├── yolov8n.pt                        # YOLOv8n object detection weights (6.2 MB)
├── requirements.txt
└── Dockerfile
```

---

## ⚡ Quickstart

### Prerequisites
- **Python**: 3.10 – 3.13 (Tested on 3.13.15)
- **Node.js**: 18+ with npm

---

### 1. Clone the Repository

```bash
git clone https://github.com/Panditt-G/3D-Sport-Analysis-AI-Powered-Sports-Analytics-Platform.git
cd 3D-Sport-Analysis-AI-Powered-Sports-Analytics-Platform
```

---

### 2. Backend Setup (FastAPI)

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

> **CPU-only PyTorch** (lighter install, no CUDA required):
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> ```

---

### 3. Frontend Setup (React + Tailwind CSS v3)

```bash
cd frontend
npm install
```

---

### 4. Run the Platform

**Option A — Full-stack (single port, production-like):**
```bash
# From project root
uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
```
Open → **[http://localhost:8000](http://localhost:8000)**

---

**Option B — Development mode (hot reload for both backend and frontend):**

Terminal 1 — Backend:
```bash
uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 — Frontend:
```bash
cd frontend
npm run dev
```
Open → **[http://localhost:5173](http://localhost:5173)**

---

## 🤖 AI Models Included

All model files are committed to the repository — no separate downloads needed.

| File | Size | Purpose |
|---|---|---|
| `yolov8n-pose.pt` | 6.5 MB | YOLOv8 athlete pose estimation (COCO-17 keypoints, used in v2 job pipeline) |
| `pose_landmarker_full.task` | 9.0 MB | MediaPipe BlazePose 3D model (33 landmarks, Python 3.13 compatible) |
| `yolov8n.pt` | 6.2 MB | YOLOv8 general object detection (player tracking) |
| `model/badminton_detector_v1.pt` | 21.5 MB | Custom-trained badminton equipment detector (shuttlecock, racket, player) |

---

## 🧠 How the v2 Pipeline Works

```
Upload Video (MP4 / AVI / MOV)
        │
        ▼
POST /api/v1/analyses
(sport, movement, pose_model)
        │
        ▼
JobService — background thread
        │
        ├─ 1. EXTRACTING_POSE    → YOLOv8-pose or MediaPipe BlazePose
        │                           → PoseFrame[] (normalized keypoints per frame)
        │
        ├─ 2. SEGMENTING_PHASES  → BadmintonSportPack.analyze_sequence()
        │                           → phases: {preparation, backswing, contact, follow_through}
        │                           → metrics: {elbow_angle, trunk_lean, wrist_snap_velocity, ...}
        │
        ├─ 3. EVALUATING_RULES   → RuleEvaluator vs overhead_clear_rules.yaml
        │                           → corrections[]: 5-pillar technique feedback cards
        │
        ├─ 4. RENDERING_VIDEO    → VideoRenderer
        │                           → ghost reference skeleton overlay
        │                           → joint angle arcs & HUD telemetry
        │                           → FFmpeg transcode to H.264 MP4 (browser-native)
        │
        └─ 5. COMPLETED          → artifacts saved to data/outputs/{job_id}/
                                    annotated.mp4 | pose.json | metrics.json | analysis.json
```

Poll progress via `GET /api/v1/analyses/{job_id}` — returns `progress_pct` (0–100) and current `stage`.

---

## 📡 API Reference

### V1 Endpoints (Recommended)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check — returns platform version |
| `GET` | `/api/v1/sports` | List all registered sports and sport packs |
| `GET` | `/api/v1/sports/{sport}/movements` | List supported movements and camera views |
| `GET` | `/api/v1/references/{sport}/{movement}` | Coach benchmark angles & ghost reference poses |
| `POST` | `/api/v1/analyses` | Upload video → create async analysis job |
| `GET` | `/api/v1/analyses/{job_id}` | Poll job status (progress %, current stage) |
| `GET` | `/api/v1/analyses/{job_id}/results` | Full results: phases, metrics, corrections |
| `GET` | `/api/v1/analyses/{job_id}/video` | Stream browser-playable annotated MP4 |
| `GET` | `/api/v1/analyses/{job_id}/pose` | Frame-by-frame landmark JSON for frontend overlay |

### Legacy Endpoints (Backwards Compatible)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api` | API root — health check |
| `GET` | `/api/sports` | List registered sports |
| `GET` | `/api/sports/{name}` | Sport detail and config |
| `POST` | `/api/upload` | Upload video (validation only) |
| `POST` | `/api/analyze/{sport}` | Synchronous analysis (legacy) |
| `GET` | `/api/results/{session_id}` | Retrieve past session results |
| `GET` | `/api/sessions` | List all past sessions |

---

## 🔌 Extending — Add a New Sport in 3 Steps

The platform uses automatic plugin discovery. Adding any new sport (e.g. `tennis`) takes only 3 steps:

### Step 1 — Register in `sports/` (Legacy Pipeline)
```python
# sports/tennis/pipeline.py
@SportRegistry.register_pipeline("tennis")
class TennisPipeline(BaseSportPipeline):
    def process_frame(self, frame, frame_idx):
        ...

# sports/tennis/analytics.py
@SportRegistry.register_analytics("tennis")
class TennisAnalytics(BaseSportAnalytics):
    def update(self, detection_data, pose_data, frame_idx):
        ...
```

### Step 2 — Add a Sport Pack (v2 Biomechanics)
```
sport_packs/tennis/
├── pack.yaml                      # Manifest: supported_movements, camera_views
├── plugin.py                      # TennisSportPack(BaseSportPack)
├── movements/forehand_drive.py    # Phase detector + kinematics
├── references/forehand_drive_ref.json  # Coach benchmark angles
└── rules/forehand_drive_rules.yaml     # Evaluation rules
```

### Step 3 — Add config
```yaml
# configs/tennis.yaml
sport: tennis
pose_model: mediapipe
```

Your new sport will be automatically discovered by the registry and appear in both the React frontend and the API.

---

## ✅ Running Tests

```bash
# Run full test suite (14 tests)
python -m pytest tests -v

# Run specific suites
python -m pytest tests/test_api_v1.py -v           # REST API tests
python -m pytest tests/test_badminton_pipeline.py -v  # Sport pack tests
python -m pytest tests/test_full_workflow.py -v    # End-to-end integration
```

---

## 🐳 Docker Deployment

```bash
docker build -t sports-ai .
docker run -p 7860:7860 sports-ai
```

Open → **[http://localhost:7860](http://localhost:7860)**

---

## 📦 Tech Stack

| Layer | Technologies |
|---|---|
| **AI & Computer Vision** | MediaPipe BlazePose, YOLOv8 (Ultralytics), OpenCV, NumPy |
| **Deep Learning** | PyTorch, TorchVision |
| **Backend** | FastAPI 0.109+, Uvicorn, Pydantic v2, Python-Multipart |
| **Video Processing** | OpenCV, imageio-ffmpeg (H.264 transcoding) |
| **Frontend** | React 18, Vite, Tailwind CSS v3 |
| **Testing** | Pytest, HTTPX, FastAPI TestClient |
| **Reporting** | ReportLab |
| **Data** | YAML (PyYAML), SciPy, Pandas, Matplotlib |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

Designed for AI, Computer Vision & Sports Analytics academic and research projects.
