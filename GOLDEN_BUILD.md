# Universal AI Document Intelligence Engine — Golden Build

**Tag**: `golden-build`  
**Branch**: `golden-build` & `main`  
**Target Repository**: `https://github.com/GloriousKrrish/Agentic-Ai-Img-Data-Extraction-BSID.git`  
**Architecture**: FastAPI Backend + Vite React Frontend + SQLite Persistent Job Manager + Gemini Flash AI OCR/Extractor  

---

## 1. Verified Architecture & Default Ports

| Component | Default Port | Internal / Public URL | Role |
| :--- | :--- | :--- | :--- |
| **Backend Engine** | `8000` | `http://127.0.0.1:8000` | FastAPI, Uvicorn, SQLite Job Store, Document Parser, Vision AI |
| **Frontend UI** | `8080` | `http://localhost:8080` | Vite + React 19, TailwindCSS, WebSocket Live Job Tracker |
| **Vite Dev Proxy** | `/api` & `/ws` | Proxies to `http://127.0.0.1:8000` | Seamless local dev without CORS issues |

---

## 2. Safe Recovery / Rollback Protocol

If any future code changes cause bugs, regressions, or system failure, you can safely restore this Golden Build without losing work.

### Method A: Safe Automated Restoration Script (Recommended)
Run the included recovery script:
```powershell
.\restore_golden_build.ps1
```
This script will:
1. Automatically stash/backup any modified or uncommitted work to a timestamped backup branch (`backup/wip-<timestamp>`).
2. Restore the repository to the pristine `golden-build` state.
3. Keep all your recent changes preserved in git history so nothing is destroyed.

---

### Method B: Manual Safe Rollback via Git

#### 1. Preserve current work first
```bash
# Save uncommitted changes
git stash push -m "WIP before rollback to golden build"

# Or save current branch to a backup
git branch backup-before-rollback
```

#### 2. Checkout the Golden Build
```bash
# Option 1: Work on a new branch based directly on the Golden Build
git checkout -b restore-golden golden-build

# Option 2: Hard-reset current branch to Golden Build (destructive to untracked commits)
git reset --hard golden-build
```

---

## 3. How to Start the Golden Build

### 1. Start the Backend (Port 8000)
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- Health Check: `http://127.0.0.1:8000/api/status`

### 2. Start the Frontend (Port 8080)
```powershell
npm run dev --prefix frontend -- --port 8080 --host 0.0.0.0
```
- Access UI: `http://localhost:8080`

---

## 4. Key Artifacts & Guarantees
- **Backend**: Verified Python 3.14+ compatibility with FastAPI and Pydantic v2.
- **Frontend**: Vite 8, React 19, Framer Motion, dynamic proxy configured for port 8000.
- **AI Agentic Loop**: Multimodal OCR + dynamic schema extraction + canonical column alignment.
- **Database**: Backend-owned SQLite queue (`jobs.sqlite3`) with persistent job states.
