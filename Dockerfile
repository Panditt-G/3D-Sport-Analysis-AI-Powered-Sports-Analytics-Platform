# ==========================================
# STAGE 1: Build the React Frontend
# ==========================================
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

# Install dependencies first (for faster caching)
COPY frontend/package*.json ./
RUN npm install

# Copy all frontend code and build it
COPY frontend/ ./
RUN npm run build


# ==========================================
# STAGE 2: Setup Python Backend & Combine
# ==========================================
FROM python:3.10-slim
WORKDIR /app

# Install system libraries required by OpenCV (cv2)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .

# We install the CPU version of PyTorch first so it doesn't download massive GPU files
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy your backend code and AI engine into the container
COPY ai_engine/ ./ai_engine/
COPY backend/ ./backend/
COPY configs/ ./configs/
COPY sports/ ./sports/
COPY data/ ./data/

# Copy the built React website from Stage 1 into the backend
# (Your server.py expects to find it at frontend/dist)
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port 8000 for the web
EXPOSE 8000

# Start the FastAPI server (which serves both the API and the React frontend)
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
