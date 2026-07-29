# write_row.ps1 - Writes extracted data to a single Excel row
param (
    [int]$RowNum,
    [string]$CustomerName = "",
    [string]$CustomerMobile = "",
    [string]$VehicleNumber = "",
    [string]$Size = "",
    [string]$Pattern = "",
    [string]$DOT = "",
    [string]$Cost = "",
    [string]$TotalCost = "",
    [string]$DealerName = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }

$filePath = Join-Path $scriptDir "Invoice_data_capture.xlsx"

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $wb = $excel.Workbooks.Open($filePath)
    $sheet = $wb.Sheets.Item("Sheet1")

    # Ensure Dealer name header exists
    $headerCol10 = $sheet.Cells.Item(1, 10).Text
    if ($headerCol10 -eq "") {
        $sheet.Cells.Item(1, 10).Value2 = "Dealer name"
    }

    # Write data
    $sheet.Cells.Item($RowNum, 2).Value2 = $CustomerName
    $sheet.Cells.Item($RowNum, 3).Value2 = $CustomerMobile
    $sheet.Cells.Item($RowNum, 4).Value2 = $VehicleNumber
    $sheet.Cells.Item($RowNum, 5).Value2 = $Size
    $sheet.Cells.Item($RowNum, 6).Value2 = $Pattern
    $sheet.Cells.Item($RowNum, 7).Value2 = $DOT
    $sheet.Cells.Item($RowNum, 8).Value2 = $Cost
    $sheet.Cells.Item($RowNum, 9).Value2 = $TotalCost
    $sheet.Cells.Item($RowNum, 10).Value2 = $DealerName

    $wb.Save()
    Write-Host ""
    Write-Host "+------------+----------------------+------------+------------+"
    Write-Host "| Row Number | Customer Name        | Mobile     | Total Cost |"
    Write-Host "+------------+----------------------+------------+------------+"
    $rStr = $RowNum.ToString().PadRight(10).Substring(0, 10)
    $nStr = $CustomerName.PadRight(20).Substring(0, 20)
    $mStr = $CustomerMobile.PadRight(10).Substring(0, 10)
    $tStr = $TotalCost.PadRight(10).Substring(0, 10)
    Write-Host "| $rStr | $nStr | $mStr | $tStr |"
    Write-Host "+------------+----------------------+------------+------------+"
    Write-Host ""
    Write-Host "Row $RowNum saved to Excel successfully."

    $wb.Close($true)
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
