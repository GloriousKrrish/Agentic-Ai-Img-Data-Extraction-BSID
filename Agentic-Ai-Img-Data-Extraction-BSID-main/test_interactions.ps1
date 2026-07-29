# test_interactions.ps1 - Test the Interactions API endpoint
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }
$envPath = Join-Path $scriptDir ".env"
$envContent = Get-Content -Path $envPath
$apiKeyLine = $envContent | Where-Object { $_ -like "GEMINI_API_KEY*" }
$apiKey = ($apiKeyLine -split "=", 2)[1].Trim()

$uri = "https://generativelanguage.googleapis.com/v1beta/interactions?key=$apiKey"
$body = @{
    model = "gemini-3.5-flash"
    input = "Hello! Say test."
} | ConvertTo-Json -Depth 10

try {
    $res = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json" -TimeoutSec 15
    Write-Host "Success! Response: $($res | ConvertTo-Json)" -ForegroundColor Green
}
catch {
    $status = 0
    if ($null -ne $_.Exception.Response) {
        $status = [int]$_.Exception.Response.StatusCode
    }
    $msg = "Unknown error"
    try {
        $streamReader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errorBody = $streamReader.ReadToEnd()
        Write-Host "Error Body: $errorBody" -ForegroundColor DarkRed
    } catch {}
    Write-Host "Failed - Status: $status, Message: $_" -ForegroundColor Red
}
