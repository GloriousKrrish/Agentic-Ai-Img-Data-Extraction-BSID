# =====================================================================
# MULTI-STAGE DOCKERFILE FOR GLOBAL PRODUCTION DEPLOYMENT
# =====================================================================

# --- Stage 1: Build React Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Backend + Static UI ---
FROM python:3.11-slim AS production

# Install system dependencies for OpenCV & image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn

# Copy backend source code
COPY backend/ ./backend/
COPY run_pipeline.py ./
COPY testing.xlsx ./

# Copy built frontend production dist bundle from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose production port
EXPOSE 8000

# Environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Start Gunicorn / Uvicorn server for production
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "backend.main:app", "--bind", "0.0.0.0:8000"]
