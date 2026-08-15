# ðŸ† Sports AI Analytics Platform

Modular, plug-and-play Computer Vision & Biomechanics Analytics Platform designed for multi-sport analysis.

---

## âš¡ Adding a New Sport in 3 Steps:

1. **Copy the template**:
   ```bash
   cp -r sports/_template sports/tennis
   ```
2. **Implement your pipeline & analytics**:
   - Inherit `BaseSportPipeline` and decorate with `@SportRegistry.register_pipeline("tennis")`
   - Inherit `BaseSportAnalytics` and decorate with `@SportRegistry.register_analytics("tennis")`
3. **Add configuration** in `configs/tennis.yaml` (or in `sports/tennis/config.yaml`).

The sport is **automatically discovered and registered** across the backend API, AI pipelines, and dashboard.

---

## ðŸ“ Architecture Overview

- **`ai_engine/`**: Core AI modules (Base interfaces, Registry, Validation, Vision, Models, Pose Analysis, Common utils).
- **`sports/`**: Plug-and-play sport implementations (`_template`, `running`, `basketball`, `football`, `volleyball`, `cricket`).
- **`backend/`**: FastAPI REST API & WebSocket streaming services.
- **`frontend/`**: Interactive dashboard, live video visualizer, telemetry charts.
- **`data/`**: Pipeline for raw videos, processed frames, datasets, and outputs.
- **`notebooks/`**: Guided experiments from Python/OpenCV to YOLO and Pose Estimation.
- **`configs/`**: Global system & per-sport YAML configuration files.
- **`tests/`**: Unit & integration test suites.
