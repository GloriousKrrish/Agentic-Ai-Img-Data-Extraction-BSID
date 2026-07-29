# batch_download.ps1 - Downloads a range of invoice images
param (
    [int]$StartRow = 2,
    [int]$EndRow = 11
)

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }

$urlFile = Join-Path $scriptDir "urls.txt"
$outDir = Join-Path $scriptDir "images"

if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

$allLines = Get-Content -Path $urlFile
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$downloaded = 0
$skipped = 0
$failed = 0

foreach ($line in $allLines) {
    if ($line -eq "" -or $null -eq $line) { continue }
    $parts = $line -split "\|", 2
    $rowNum = [int]$parts[0]
    $url = $parts[1]

    if ($rowNum -lt $StartRow -or $rowNum -gt $EndRow) { continue }

    $outFile = Join-Path $outDir "invoice_row_$rowNum.jpg"

    if (Test-Path $outFile) {
        $skipped++
        continue
    }

    try {
        Invoke-WebRequest -Uri $url -OutFile $outFile -UserAgent "Mozilla/5.0" -ErrorAction Stop
        $fileSize = (Get-Item $outFile).Length
        Write-Host "Row $rowNum downloaded ($fileSize bytes)"
        $downloaded++
    }
    catch {
        Write-Host "Row $rowNum FAILED: $_"
        $failed++
    }
}

Write-Host ""
Write-Host "Batch download complete: Downloaded=$downloaded, Skipped=$skipped, Failed=$failed"
