# run_parallel.ps1 - Orchestrates the parallel execution of workers and supervisor
param (
    [string]$FileName = "Invoice_data_capture.xlsx",
    [int]$NumWorkers = 3,
    [int]$DelaySeconds = 8
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }

$queueDir = Join-Path $scriptDir "queue"
$resultsDir = Join-Path $scriptDir "results"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Starting Parallel Queue Processing" -ForegroundColor Cyan
Write-Host "   FileName:     $FileName" -ForegroundColor Cyan
Write-Host "   NumWorkers:   $NumWorkers" -ForegroundColor Cyan
Write-Host "   DelaySeconds: $DelaySeconds" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Clean up old directories
Write-Host "Cleaning up old temporary queue and results directories..." -ForegroundColor Yellow
if (Test-Path $queueDir) {
    Remove-Item -Path $queueDir -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path $resultsDir) {
    Remove-Item -Path $resultsDir -Recurse -Force -ErrorAction SilentlyContinue
}

# 2. Build the task queue
& "$scriptDir\init_queue.ps1" -FileName $FileName

# Check if queue has tasks
$tasksCount = (Get-ChildItem -Path $queueDir -Filter "*.task").Count
if ($tasksCount -eq 0) {
    Write-Host "All rows are already processed. Nothing to do!" -ForegroundColor Green
    return
}

# 3. Spawn background workers
Write-Host "Spawning $NumWorkers workers in the background..." -ForegroundColor Yellow
$processes = @()
for ($w = 1; $w -le $NumWorkers; $w++) {
    $stdoutLog = Join-Path $scriptDir "worker_${w}.log"
    $stderrLog = Join-Path $scriptDir "worker_${w}_err.log"
    
    # Remove existing worker log files if any
    Remove-Item -Path $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue
    
    $p = Start-Process powershell.exe -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptDir\worker.ps1`" -WorkerId $w -DelaySeconds $DelaySeconds -WorkspacePath `"$scriptDir`"" -PassThru -NoNewWindow -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
    $processes += $p
}

# 4. Start foreground supervisor (master)
Write-Host "Starting foreground supervisor to watch queue and update Excel..." -ForegroundColor Yellow
try {
    & "$scriptDir\master.ps1" -FileName $FileName
}
catch {
    Write-Host "Supervisor encountered an error: $_" -ForegroundColor Red
}

# 5. Clean up jobs
Write-Host "Waiting for background workers to exit..." -ForegroundColor Yellow
$processes | Wait-Process -Timeout 10 -ErrorAction SilentlyContinue
$processes | Stop-Process -Force -ErrorAction SilentlyContinue

# Verify
$finalTasksCount = (Get-ChildItem -Path $queueDir -Filter "*.task").Count
$finalLocksCount = (Get-ChildItem -Path $queueDir -Filter "*.lock_*").Count
if ($finalTasksCount -eq 0 -and $finalLocksCount -eq 0) {
    Write-Host "Parallel processing run completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Some tasks are still left or locked. Run again to process them." -ForegroundColor Yellow
}
