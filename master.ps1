# master.ps1 - Supervisor script to write results to Excel and log progress
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

Write-Host "Supervisor: Opening Excel workbook..." -ForegroundColor Yellow
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open($filePath)
$sheet = $wb.Sheets.Item("Sheet1")

# Make sure dealer name header is initialized
$headerCol10 = $sheet.Cells.Item(1, 10).Text
if ($headerCol10 -eq "") {
    $sheet.Cells.Item(1, 10).Value2 = "Dealer name"
    $wb.Save()
}

Write-Host "Supervisor active. Listening for worker results..." -ForegroundColor Yellow

$processedCount = 0

try {
    while ($true) {
        # Check if we have files in queue (tasks or locks)
        $tasksCount = 0
        $locksCount = 0
        
        if (Test-Path $queueDir) {
            $tasksCount = (Get-ChildItem -Path $queueDir -Filter "*.task").Count
            $locksCount = (Get-ChildItem -Path $queueDir -Filter "*.lock_*").Count
        }
        
        # Check if we have results to process
        $results = @()
        if (Test-Path $resultsDir) {
            $results = Get-ChildItem -Path $resultsDir -Filter "*.json"
        }
        
        # If no tasks, locks, or results remain, we are finished!
        if ($tasksCount -eq 0 -and $locksCount -eq 0 -and $results.Count -eq 0) {
            Write-Host "Supervisor: No more tasks or results. All processing complete." -ForegroundColor Green
            break
        }
        
        # Process any pending results
        foreach ($rFile in $results) {
            try {
                $content = Get-Content -Path $rFile.FullName -Raw
                $res = ConvertFrom-Json -InputObject $content
                
                $r = [int]$res.RowIndex
                
                # Write to Excel
                $sheet.Cells.Item($r, 2).Value2 = $res.CustomerName
                $sheet.Cells.Item($r, 3).Value2 = $res.CustomerMobile
                $sheet.Cells.Item($r, 4).Value2 = $res.VehicleNumber
                $sheet.Cells.Item($r, 5).Value2 = $res.Size
                $sheet.Cells.Item($r, 6).Value2 = $res.Pattern
                $sheet.Cells.Item($r, 7).Value2 = $res.DOT
                $sheet.Cells.Item($r, 8).Value2 = $res.Cost
                $sheet.Cells.Item($r, 9).Value2 = $res.TotalCost
                $sheet.Cells.Item($r, 10).Value2 = $res.DealerName
                
                # Save immediately
                $wb.Save()
                
                # Print output log table
                Write-Host ""
                Write-Host "+------------+----------------------+------------+------------+" -ForegroundColor Gray
                Write-Host "| Row Number | Customer Name        | Mobile     | Total Cost |" -ForegroundColor Gray
                Write-Host "+------------+----------------------+------------+------------+" -ForegroundColor Gray
                $rStr = $r.ToString().PadRight(10).Substring(0, 10)
                $nStr = $res.CustomerName.PadRight(20).Substring(0, 20)
                $mStr = $res.CustomerMobile.PadRight(10).Substring(0, 10)
                $tStr = $res.TotalCost.PadRight(10).Substring(0, 10)
                Write-Host "| $rStr | $nStr | $mStr | $tStr |" -ForegroundColor White
                Write-Host "+------------+----------------------+------------+------------+" -ForegroundColor Gray
                Write-Host "Supervisor: Saved Row $r to Excel. (Pending tasks: $tasksCount, Active locks: $locksCount)" -ForegroundColor Green
                Write-Host ""
                
                $processedCount++
                
                # Delete the JSON file after processing
                Remove-Item -Path $rFile.FullName -Force -ErrorAction SilentlyContinue
            }
            catch {
                Write-Host "Supervisor Error processing result file $($rFile.Name): $_" -ForegroundColor Red
            }
        }
        
        # Sleep for a short interval before polling again
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "Supervisor: Releasing Excel COM resources..." -ForegroundColor Gray
    if ($null -ne $wb) {
        $wb.Close($true)
    }
    if ($null -ne $excel) {
        $excel.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    Write-Host "Supervisor: Resources released. Processed $processedCount rows in this run." -ForegroundColor Green
}
