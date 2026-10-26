# Golden Build Preservation Rule

Whenever developing in this repository:
1. **Reference State**: The rock-solid, verified working state of this application is marked with git tag `golden-build` and git branch `golden-build`.
2. **Ports**:
   - Frontend runs on port 8080 (`http://localhost:8080`)
   - Backend runs on port 8000 (`http://127.0.0.1:8000`)
3. **Safety / Rollback Protocol**:
   - If changes fail, tests break, or any regression occurs, the assistant must offer or execute safe restoration to `golden-build`.
   - Always safeguard the user's modifications (stash or create a timestamped backup branch) prior to any reset or checkout so work is never destroyed.
   - Script `.\restore_golden_build.ps1` is available for 1-click safe restoration.
