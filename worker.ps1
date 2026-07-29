# worker.ps1 - Parallel worker for invoice extraction
param (
    [int]$WorkerId = 1,
    [int]$DelaySeconds = 8,
    [string]$WorkspacePath = ""
)

$ErrorActionPreference = "Stop"

# Helper function to clean text fields
function Clean-Field ($val) {
    if ($null -eq $val -or $val -eq "null" -or $val -eq "NULL" -or $val.ToString().Trim() -eq "") {
        return ""
    }
    return $val.ToString().Trim()
}

# Helper function to clean mobile numbers
function Clean-Mobile ($val) {
    $cleaned = Clean-Field $val
    if ($cleaned -eq "") { return "" }
    
    # Remove all non-digit characters
    $mob = $cleaned -replace '[^\d]', ''
    
    # If 12 digits and starts with 91, strip it
    if ($mob.Length -eq 12 -and $mob.StartsWith("91")) {
        $mob = $mob.Substring(2)
    }
    # If 11 digits and starts with 0, strip it
    if ($mob.Length -eq 11 -and $mob.StartsWith("0")) {
        $mob = $mob.Substring(1)
    }
    
    # Verify it is exactly 10 digits starting with 6-9
    if ($mob -match '^[6-9]\d{9}$') {
        return $mob
    }
    return ""
}

# Helper function to clean cost fields
function Clean-Cost ($val) {
    $cleaned = Clean-Field $val
    if ($cleaned -eq "") { return "" }
    
    if ($cleaned -match '(\d+[\d,]*(\.\d+)?)') {
        $num = $Matches[1]
        $num = $num -replace ',', ''
        return $num
    }
    return ""
}

# Helper function to clean license plate vehicle number
function Clean-Vehicle ($val) {
    $cleaned = Clean-Field $val
    if ($cleaned -eq "") { return "" }
    return ($cleaned -replace '[^a-zA-Z0-9]', '').ToUpper()
}

# Load API Key
$scriptDir = $WorkspacePath
if ($null -eq $scriptDir -or $scriptDir -eq "") {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }
}
$envPath = Join-Path $scriptDir ".env"

if (-not (Test-Path $envPath)) {
    Write-Error "Could not find .env file at $envPath"
}

$envContent = Get-Content -Path $envPath
$apiKeyLine = $envContent | Where-Object { $_ -like "GEMINI_API_KEY*" }
if ($null -eq $apiKeyLine) {
    Write-Error "GEMINI_API_KEY not found in .env file."
}
$apiKey = ($apiKeyLine -split "=", 2)[1].Trim()

$queueDir = Join-Path $scriptDir "queue"
$resultsDir = Join-Path $scriptDir "results"

$schema = @{
    type = "object"
    properties = @{
        CustomerName = @{ type = "string"; description = "Customer Name. Return null if missing." }
        CustomerMobile = @{ type = "string"; description = "10-digit customer mobile number starting with 6-9. Strip any country codes like +91 or prefix 0. Return null if missing." }
        VehicleNumber = @{ type = "string"; description = "Alphanumeric vehicle license plate format. Return null if missing." }
        Size = @{ type = "string"; description = "Automotive tire size format, e.g., 205/55R16. Return null if missing." }
        Pattern = @{ type = "string"; description = "Tire model/tread design name string, e.g., STURDOL. Return null if missing." }
        DOT = @{ type = "string"; description = "Tire manufacturing code starting with 'DOT'. Return null if missing." }
        Cost = @{ type = "string"; description = "Individual unit price of a single tire. Clean value containing only numbers. Return null if missing." }
        TotalCost = @{ type = "string"; description = "Final invoice grand total price. Clean value containing only numbers. Ensure this is the grand total and NOT the individual tire unit cost. Return null if missing." }
        DealerName = @{ type = "string"; description = "The business banner name of the tire dealer at the top of the invoice. Return null if missing." }
    }
    required = @("CustomerName", "CustomerMobile", "VehicleNumber", "Size", "Pattern", "DOT", "Cost", "TotalCost", "DealerName")
}

$prompt = @"
You are a high-precision extraction system. Analyze the invoice image and extract the following fields.
Pay close attention to both printed and hand-written text (often in blue/black ink or pencil, which may be rotated).
Check the entire page for hand-written numbers, vehicle license plates, or names.

Fields to extract:
1. CustomerName: The customer's name (e.g. SURESH, Panduranga reddy). Strip any vehicle numbers if written inside this field (e.g., if Name says 'Panduranga reddy ap05EY5775', return 'Panduranga reddy').
2. CustomerMobile: A 10-digit mobile number starting with 6-9 (e.g. 9493950218, 9951218688). If the printed phone field is empty, check for hand-written phone numbers on the invoice. Strip any country code like +91 or leading 0. If multiple numbers are written, always prefer and extract the one that is exactly 10 digits and starts with 6-9.
3. VehicleNumber: Look for a vehicle license plate format (e.g. KA03ME4662, AP05EY5775). It is often written next to the customer name, address, or hand-written on the page. Do NOT confuse it with the tire DOT serial number (e.g. W9madlf4625).
4. Size: The tire size format (e.g. 205/65R16, 155/70R13). Strip out any model pattern names (like B390, STURDO) from the size.
5. Pattern: The tire model/tread design pattern name (e.g. B390, STURDDTL, Sturdo, Sturdo TL, Ecopia, Dueler). Do NOT write 'BRIDGESTONE' as the pattern. Bridgestone is the brand.
6. DOT: The tire serial/manufacturing code, usually under product details (e.g. W9madlf4625). Extract the code as is.
7. Cost: The individual unit price of one tire before tax. This is the taxable value divided by the quantity. If the quantity is 2 and the total taxable value is 6779.66, then the unit cost is 3389.83.
8. TotalCost: The final grand total net amount of the invoice, after tax (e.g., 8000.00 for Suresh, 1800.00 for Panduranga). This is the largest final net figure at the bottom right.
9. DealerName: The business banner name of the tire dealer at the top of the invoice (e.g., M/s. SINDU TYRES, Chenna Someswara Tyres).

Important:
- If a field is missing, return null. Do not guess or hallucinate.
- Clean all values of currency symbols ($ or ₹), commas, or extra spacing.
"@

$models = @(
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-1.5-flash"
)
$currentModelIndex = 0

Write-Host "Worker ${WorkerId} started. Workspace: ${scriptDir}" -ForegroundColor Green

# Add a slight startup delay based on WorkerId to space out requests
Start-Sleep -Seconds ($WorkerId * 2)

while ($true) {
    if (-not (Test-Path $queueDir)) { break }
    
    # Get all .task files
    $tasks = Get-ChildItem -Path $queueDir -Filter "*.task"
    if ($tasks.Count -eq 0) {
        Write-Host "Worker ${WorkerId} - No more tasks in queue. Exiting." -ForegroundColor Yellow
        break
    }
    
    # Try to claim a task
    $claimed = $false
    $r = $null
    $url = $null
    $lockFile = $null
    
    foreach ($t in $tasks) {
        $r = [int]$t.BaseName
        $lockFile = Join-Path $queueDir "${r}.lock_${WorkerId}"
        
        try {
            Rename-Item -Path $t.FullName -NewName "${r}.lock_${WorkerId}" -ErrorAction Stop
            $url = Get-Content -Path $lockFile -Raw
            $url = $url.Trim()
            $claimed = $true
            break
        }
        catch {
            # Failed to lock (another worker took it)
            continue
        }
    }
    
    if (-not $claimed) {
        # Tried to claim but couldn't lock any tasks. Sleep a bit and check again.
        Start-Sleep -Seconds 2
        continue
    }
    
    Write-Host "Worker ${WorkerId} - Claimed Row $r. Downloading..." -ForegroundColor Cyan
    
    # Download image
    $tempFile = Join-Path $env:TEMP "worker_${WorkerId}_row_${r}.jpg"
    $downloadSuccess = $false
    
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $tempFile -UserAgent "Mozilla/5.0" -ErrorAction Stop
        $downloadSuccess = $true
    }
    catch {
        Write-Host "Worker ${WorkerId} - Error downloading Row $r URL - $_" -ForegroundColor Red
    }
    
    if (-not $downloadSuccess) {
        Write-Host "Worker ${WorkerId} - Skipping Row $r due to download failure." -ForegroundColor Red
        # Remove lock file so another worker/pass can retry it
        Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue
        continue
    }
    
    # Encode to Base64
    $base64Image = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($tempFile))
    Remove-Item $tempFile -Force | Out-Null
    
    # Call Gemini API
    $retries = 3
    $success = $false
    $extractedText = ""
    
    $mimeType = "image/jpeg"
    if ($url -like "*.pdf*" -or $url -like "*application/pdf*") {
        $mimeType = "application/pdf"
    }
    
    $body = @{
        contents = @(
            @{
                parts = @(
                    @{ text = $prompt },
                    @{
                        inlineData = @{
                            mimeType = $mimeType
                            data = $base64Image
                        }
                    }
                )
            }
        )
        generationConfig = @{
            responseMimeType = "application/json"
            responseSchema = $schema
        }
    } | ConvertTo-Json -Depth 10
    
    while ($retries -gt 0 -and -not $success) {
        $modelName = $models[$currentModelIndex]
        $uri = "https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=$apiKey"
        try {
            Write-Host "Worker ${WorkerId} (Row $r) calling API with model $modelName..." -ForegroundColor Gray
            $response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json" -TimeoutSec 45
            $extractedText = $response.candidates[0].content.parts[0].text
            $success = $true
        }
        catch {
            $status = 0
            if ($null -ne $_.Exception.Response) {
                $status = [int]$_.Exception.Response.StatusCode
            }
            
            # Read error response body if possible to see if it's indeed a quota error
            $isQuotaError = $false
            try {
                $streamReader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $errorBody = $streamReader.ReadToEnd()
                if ($errorBody -match "Quota exceeded" -or $errorBody -match "exceeded your current quota" -or $errorBody -match "quotaLimit") {
                    $isQuotaError = $true
                }
            } catch {}
            
            Write-Host "Worker ${WorkerId} (Row $r) Model $modelName Error - $_ (Status: $status, IsQuota: $isQuotaError)" -ForegroundColor Red
            
            if ($status -eq 429 -and $isQuotaError) {
                # Quota exhausted! Try the next model after short delay
                $currentModelIndex++
                if ($currentModelIndex -ge $models.Count) {
                    Write-Host "Worker ${WorkerId} - All fallback models are exhausted. Sleeping 60s before retrying..." -ForegroundColor Yellow
                    $currentModelIndex = 0
                    Start-Sleep -Seconds 60
                } else {
                    Write-Host "Worker ${WorkerId} - Quota exhausted for $modelName. Falling back to $($models[$currentModelIndex])..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 5
                    continue
                }
            }
            elseif ($status -eq 429) {
                # Rate limit hit (e.g. RPM limit). Sleep 30s and retry.
                Write-Host "Worker ${WorkerId} - Rate limit hit on $modelName. Sleeping 30s..." -ForegroundColor Yellow
                Start-Sleep -Seconds 30
                $retries--
            }
            else {
                # Other error (e.g. timeout or 503). Sleep 10s and retry.
                Write-Host "Worker ${WorkerId} - Error on $modelName. Sleeping 10s..." -ForegroundColor Yellow
                Start-Sleep -Seconds 10
                $retries--
            }
        }
    }
    
    if (-not $success) {
        Write-Host "Worker ${WorkerId} - Row $r extraction failed after multiple attempts." -ForegroundColor Red
        # Remove lock file so it can be retried
        Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue
        continue
    }
    
    # Process extracted result
    try {
        $extractedObj = ConvertFrom-Json -InputObject $extractedText
        
        $customerName   = Clean-Field   $extractedObj.CustomerName
        $customerMobile = Clean-Mobile  $extractedObj.CustomerMobile
        $vehicleNumber  = Clean-Vehicle $extractedObj.VehicleNumber
        $size           = Clean-Field   $extractedObj.Size
        $pattern        = Clean-Field   $extractedObj.Pattern
        $dot            = Clean-Field   $extractedObj.DOT
        $cost           = Clean-Cost    $extractedObj.Cost
        $totalCost      = Clean-Cost    $extractedObj.TotalCost
        $dealerName     = Clean-Field   $extractedObj.DealerName
        
        if ($customerName -eq "" -and $customerMobile -eq "" -and $vehicleNumber -eq "" -and $size -eq "" -and $pattern -eq "" -and $dot -eq "" -and $cost -eq "" -and $totalCost -eq "" -and $dealerName -eq "") {
            $customerName = "N/A"
        }
        
        if ($dot -ne "" -and $dot -notlike "DOT*") {
            $dot = "DOT $dot"
        }
        
        $result = @{
            RowIndex       = $r
            CustomerName   = $customerName
            CustomerMobile = $customerMobile
            VehicleNumber  = $vehicleNumber
            Size           = $size
            Pattern        = $pattern
            DOT            = $dot
            Cost           = $cost
            TotalCost      = $totalCost
            DealerName     = $dealerName
        }
        
        # Save result JSON
        $resultFile = Join-Path $resultsDir "${r}.json"
        $result | ConvertTo-Json | Out-File -FilePath $resultFile -Encoding UTF8
        
        # Remove lock file to signal completion
        Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue
        Write-Host "Worker ${WorkerId} - Completed Row $r." -ForegroundColor Green
    }
    catch {
        Write-Host "Worker ${WorkerId} - Error saving results for Row $r - $_" -ForegroundColor Red
        Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue
    }
    
    # Pace worker
    Start-Sleep -Seconds $DelaySeconds
}
