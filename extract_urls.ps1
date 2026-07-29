# Extract all unprocessed URLs from Invoice_data_capture.xlsx
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }

$filePath = Join-Path $scriptDir "Invoice_data_capture.xlsx"
$urlFile = Join-Path $scriptDir "urls.txt"

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $wb = $excel.Workbooks.Open($filePath)
    $sheet = $wb.Sheets.Item("Sheet1")
    $rows = $sheet.UsedRange.Rows.Count
    $cols = $sheet.UsedRange.Columns.Count

    Write-Host "Total rows: $rows, Cols: $cols"

    # Dump all unprocessed URLs
    $lines = @()
    $unprocessed = 0
    for ($r = 2; $r -le $rows; $r++) {
        $url = $sheet.Cells.Item($r, 1).Text
        $name = $sheet.Cells.Item($r, 2).Text
        $total = $sheet.Cells.Item($r, 9).Text
        if ($url -like "http*" -and $name -eq "" -and $total -eq "") {
            $lines += "$r|$url"
            $unprocessed++
        }
    }
    $lines | Out-File -FilePath $urlFile -Encoding UTF8
    Write-Host "Total unprocessed rows with URLs: $unprocessed"
    Write-Host "URL list saved to urls.txt"

    # Show first 5 URLs
    Write-Host ""
    Write-Host "First 5 URLs:"
    $lines | Select-Object -First 5 | ForEach-Object { Write-Host $_ }

    $wb.Close($false)
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [GC]::Collect()
}
