# download_image.ps1 - Downloads a single invoice image by row number
param (
    [int]$RowNum = 2
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }

$urlFile = Join-Path $scriptDir "urls.txt"
$outDir = Join-Path $scriptDir "images"

if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

# Find the URL for the requested row
$urlLine = Get-Content -Path $urlFile | Where-Object { $_.StartsWith("$RowNum|") } | Select-Object -First 1

if ($null -eq $urlLine) {
    Write-Error "Row $RowNum not found in urls.txt"
}

$parts = $urlLine -split "\|", 2
$url = $parts[1]

$outFile = Join-Path $outDir "invoice_row_$RowNum.jpg"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $url -OutFile $outFile -UserAgent "Mozilla/5.0" -ErrorAction Stop

$fileSize = (Get-Item $outFile).Length
Write-Host "Row $RowNum downloaded: $outFile ($fileSize bytes)"
