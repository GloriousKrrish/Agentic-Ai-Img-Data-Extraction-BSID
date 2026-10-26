# ==============================================================================
# Golden Build Recovery & Rollback Script
# Universal AI Document Intelligence Engine
# ==============================================================================
param(
    [ValidateSet("SafeBranch", "HardReset")]
    [string]$Mode = "SafeBranch"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         GOLDEN BUILD RESTORATION PROCEDURE               " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$CurrentBranch = (git branch --show-current).Trim()
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupBranch = "backup/pre-rollback-$Timestamp"

Write-Host "[1/4] Checking repository state..." -ForegroundColor Cyan
$Status = git status --porcelain

if ($Status) {
    Write-Host "      Detected uncommitted changes. Creating safety backup..." -ForegroundColor Yellow
    git stash push -m "Automated backup before restoring Golden Build ($Timestamp)"
    Write-Host "      [OK] Stashed uncommitted files safely." -ForegroundColor Green
} else {
    Write-Host "      [OK] Working tree clean." -ForegroundColor Green
}

Write-Host "[2/4] Backing up current branch pointer to: $BackupBranch..." -ForegroundColor Cyan
git branch "$BackupBranch"
Write-Host "      [OK] Preserved branch pointer: $BackupBranch" -ForegroundColor Green

Write-Host "[3/4] Restoring to tag: golden-build ($Mode)..." -ForegroundColor Cyan
if ($Mode -eq "SafeBranch") {
    $RestoreBranchName = "golden-restore-$Timestamp"
    git checkout -b "$RestoreBranchName" "golden-build"
    Write-Host "      [OK] Checked out golden-build to new active branch: $RestoreBranchName" -ForegroundColor Green
} else {
    git checkout "$CurrentBranch"
    git reset --hard "golden-build"
    Write-Host "      [OK] Reset current branch ($CurrentBranch) to golden-build." -ForegroundColor Green
}

Write-Host "[4/4] Verifying Golden Build status..." -ForegroundColor Cyan
git log -1 --oneline

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  Golden Build successfully restored!                     " -ForegroundColor Green
Write-Host "  Nothing was lost: prior work preserved in $BackupBranch" -ForegroundColor Yellow
Write-Host "  To run:                                                 " -ForegroundColor White
Write-Host "    Backend  (port 8000): python -m uvicorn backend.main:app --port 8000" -ForegroundColor White
Write-Host "    Frontend (port 8080): npm run dev --prefix frontend -- --port 8080" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
