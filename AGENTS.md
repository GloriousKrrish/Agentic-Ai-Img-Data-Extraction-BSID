# AGENTS GUIDELINES & GOLDEN BUILD GUARANTEE

## 1. Golden Build Reference Point
- **Git Tag**: `golden-build`
- **Git Branch**: `golden-build`
- **Default Running Ports**:
  - Backend: `http://127.0.0.1:8000` (FastAPI / Uvicorn)
  - Frontend: `http://localhost:8080` (Vite + React)
- **Repository Remote**: `https://github.com/GloriousKrrish/Agentic-Ai-Img-Data-Extraction-BSID.git`

## 2. Mandatory Preservation & Rollback Behavior
If during ongoing or future development, any feature additions, refactorings, dependency updates, or unexpected errors break or destabilize the project:
1. **Never discard or destroy user work recklessly**:
   - Always preserve dirty state by creating a backup branch or stashing uncommitted files (`git stash` or `git branch backup/...`).
2. **Bring back the Golden Build**:
   - The user or agent can execute `powershell .\restore_golden_build.ps1` or run `git checkout golden-build`.
3. **Preserve Compatibility**:
   - Ensure `frontend/.env.development` and `frontend/vite.config.ts` maintain proxy mapping to the backend on port 8000 and frontend on port 8080 unless explicitly requested otherwise.
