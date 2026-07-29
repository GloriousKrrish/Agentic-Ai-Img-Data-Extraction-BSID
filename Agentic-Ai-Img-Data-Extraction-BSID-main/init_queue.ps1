# init_queue.ps1 - Initialize processing queue from Excel
param (
    [string]$FileName = "Invoice_data_capture.xlsx"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }

$filePath = Join-Path $scriptDir $FileName
$queueDir = Join-Path $scriptDir "queue"
$resultsDir = Join-Path $scriptDir "results"

if (-not (Test-Path $filePath)) {
    Write-Error "Target file not found at $filePath"
}

# Create directories
if (-not (Test-Path $queueDir)) {
    New-Item -ItemType Directory -Path $queueDir | Out-Null
}
if (-not (Test-Path $resultsDir)) {
    New-Item -ItemType Directory -Path $resultsDir | Out-Null
}

Write-Host "Opening Excel workbook to scan for unprocessed rows..." -ForegroundColor Yellow
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $wb = $excel.Workbooks.Open($filePath)
    $sheet = $wb.Sheets.Item("Sheet1")
    $rows = $sheet.UsedRange.Rows.Count
    
    Write-Host "Excel open. Scanning $rows rows..." -ForegroundColor Yellow
    
    $createdCount = 0
    for ($r = 2; $r -le $rows; $r++) {
        $url = $sheet.Cells.Item($r, 1).Text
        if ($url -like "http*") {
            $existingName = $sheet.Cells.Item($r, 2).Text.Trim()
            $existingTotal = $sheet.Cells.Item($r, 9).Text.Trim()
            
            # Check if it has not been processed yet
            if ($existingName -eq "" -and $existingTotal -eq "") {
                # Create a task file
                $taskFile = Join-Path $queueDir "${r}.task"
                $url | Out-File -FilePath $taskFile -Encoding UTF8
                $createdCount++
            }
        }
    }
    
    Write-Host "Queue initialized: Created $createdCount task files in queue folder." -ForegroundColor Green
    $wb.Close($false)
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
