# search_js.ps1 - Search extension.js for REST patterns
$jsPath = "c:\Users\krrish-pawar\AppData\Local\Programs\Antigravity IDE\resources\app\extensions\antigravity\dist\extension.js"
$content = Get-Content -Path $jsPath -Raw

# Search for /models/ or /interactions or localhost or http
Write-Host "Searching for patterns..."
$matches = [regex]::Matches($content, '"/[a-zA-Z0-9_/:-]+"')
Write-Host "Found $($matches.Count) path strings."
$seen = @{}
foreach ($m in $matches) {
    $val = $m.Value
    if ($val -match "models" -or $val -match "interactions" -or $val -match "generative" -or $val -match "api") {
        if (-not $seen.ContainsKey($val)) {
            $seen[$val] = $true
            Write-Host "Path: $val" -ForegroundColor Green
        }
    }
}
