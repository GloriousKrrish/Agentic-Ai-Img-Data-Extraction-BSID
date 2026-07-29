param (
    [string]$FileName = "Invoice_data_capture-3.xlsx"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }
$filePath = Join-Path $scriptDir $FileName

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open($filePath)
$sheet = $wb.Sheets.Item("Sheet1")
$rows = $sheet.UsedRange.Rows.Count
$cols = $sheet.UsedRange.Columns.Count
Write-Host "Rows: $rows, Cols: $cols"
Write-Host "--- Row 1 (Headers) ---"
for ($c = 1; $c -le $cols; $c++) {
    Write-Host "  Col $($c): $($sheet.Cells.Item(1, $c).Text)"
}
Write-Host ""
Write-Host "--- Rows 2-6 (Data Sample) ---"
for ($r = 2; $r -le [Math]::Min(6, $rows); $r++) {
    Write-Host "Row $($r):"
    for ($c = 1; $c -le $cols; $c++) {
        $val = $sheet.Cells.Item($r, $c).Text
        if ($val -ne "") { Write-Host "  Col $($c): $val" }
    }
}

Write-Host ""
Write-Host "--- Checking first 20 data rows for URL presence ---"
$urlCount = 0
$filledCount = 0
$emptyCount = 0
for ($r = 2; $r -le [Math]::Min(21, $rows); $r++) {
    $col1 = $sheet.Cells.Item($r, 1).Text
    $col2 = $sheet.Cells.Item($r, 2).Text
    $col9 = $sheet.Cells.Item($r, 9).Text
    $hasUrl = $col1 -like "http*"
    $isFilled = ($col2 -ne "" -or $col9 -ne "")
    $col1preview = $col1.Substring(0, [Math]::Min(50, $col1.Length))
    Write-Host "Row $($r) | Col1: '$col1preview' | HasURL: $hasUrl | Name: '$col2' | Total: '$col9'"
    if ($hasUrl) { $urlCount++ }
    if ($isFilled) { $filledCount++ }
    else { $emptyCount++ }
}
Write-Host ""
Write-Host "In first 20 rows: URLs=$urlCount, Filled=$filledCount, Empty=$emptyCount"

$wb.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
[GC]::Collect()
