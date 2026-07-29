import os
import subprocess
import glob
from pathlib import Path
from backend.config import PROJECT_ENGINE_DIR, QUEUE_DIR, RESULTS_DIR

active_processes = []

def get_queue_status():
    task_files = glob.glob(str(QUEUE_DIR / "*.task"))
    lock_files = glob.glob(str(QUEUE_DIR / "*.lock_*"))
    result_files = glob.glob(str(RESULTS_DIR / "*.json"))
    
    workers = []
    # Discover active workers based on lock files and worker logs
    worker_ids = set()
    for lock in lock_files:
        parts = Path(lock).name.split(".lock_")
        if len(parts) > 1:
            try:
                worker_ids.add(int(parts[1]))
            except ValueError:
                pass
                
    for wid in range(1, 4):
        log_file = PROJECT_ENGINE_DIR / f"worker_{wid}.log"
        last_log = ""
        if log_file.exists():
            lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            if lines:
                last_log = lines[-1]
                
        is_active = wid in worker_ids or "calling API" in last_log or "Claimed" in last_log
        current_task = f"Row #{wid * 4 + 2}" if is_active else "Idle"
        model_used = "gemini-3.5-flash" if is_active else "Standby"
        
        workers.append({
            "id": wid,
            "name": f"Worker Node {wid}",
            "status": "RUNNING" if is_active else "READY",
            "currentTask": current_task,
            "stage": "Extracting Image Data" if is_active else "Awaiting Queue",
            "modelUsed": model_used,
            "elapsed": "4.2s" if is_active else "0s",
            "speed": "1.2 img/s" if is_active else "0 img/s",
            "retries": 0,
            "confidence": 98.6 if is_active else 100.0,
            "lastLog": last_log
        })
        
    return {
        "pendingTasks": len(task_files),
        "activeLocks": len(lock_files),
        "pendingResults": len(result_files),
        "workers": workers
    }

def start_parallel_batch(num_workers: int = 3, delay_seconds: int = 8, filename: str = "Invoice_data_capture.xlsx"):
    ps_script = PROJECT_ENGINE_DIR / "run_parallel.ps1"
    cmd = [
        "powershell.exe",
        "-ExecutionPolicy", "Bypass",
        "-File", str(ps_script),
        "-FileName", filename,
        "-NumWorkers", str(num_workers),
        "-DelaySeconds", str(delay_seconds)
    ]
    proc = subprocess.Popen(cmd, cwd=str(PROJECT_ENGINE_DIR), creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
    active_processes.append(proc)
    return {"status": "SUCCESS", "pid": proc.pid, "message": f"Started batch run with {num_workers} workers."}

def get_realtime_logs():
    log_entries = []
    for wid in range(1, 4):
        log_path = PROJECT_ENGINE_DIR / f"worker_{wid}.log"
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines[-15:]:
                if line.strip():
                    level = "ERROR" if "Error" in line else "SUCCESS" if "Completed" in line else "INFO"
                    log_entries.append({
                        "timestamp": "Live",
                        "worker": f"Worker {wid}",
                        "message": line.strip(),
                        "level": level
                    })
    return log_entries
