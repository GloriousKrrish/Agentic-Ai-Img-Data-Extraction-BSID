param (
    [string]$FileName = "Invoice_data_capture-3.xlsx",
    [int]$SaveInterval = 5,
    [int]$DelaySeconds = 12
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
    
    # If 12 digits and starts with 91 (country code for India), strip it
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
    return "" # Invalid mobile number, return empty
}

# Helper function to clean cost fields
function Clean-Cost ($val) {
    $cleaned = Clean-Field $val
    if ($cleaned -eq "") { return "" }
    
    # Extract the first sequence that looks like a decimal or integer number
    if ($cleaned -match '(\d+[\d,]*(\.\d+)?)') {
        $num = $Matches[1]
        # Remove commas
        $num = $num -replace ',', ''
        return $num
    }
    return ""
}

# Helper function to clean license plate vehicle number
function Clean-Vehicle ($val) {
    $cleaned = Clean-Field $val
    if ($cleaned -eq "") { return "" }
    # Remove spaces and punctuation to leave only alphanumeric characters
    return ($cleaned -replace '[^a-zA-Z0-9]', '').ToUpper()
}

# 1. Load API Key
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($null -eq $scriptDir -or $scriptDir -eq "") { $scriptDir = Get-Location }
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

# 2. Check File Path
$filePath = Join-Path $scriptDir $FileName
if (-not (Test-Path $filePath)) {
    Write-Error "Target file not found at $filePath"
}

Write-Host "Starting extraction for: $FileName" -ForegroundColor Cyan

# 3. Setup Gemini API Payload
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

# Initialize Excel COM
$excel = $null
$wb = $null
$processedCount = 0

try {
    Write-Host "Opening Excel workbook..." -ForegroundColor Yellow
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $wb = $excel.Workbooks.Open($filePath)
    $sheet = $wb.Sheets.Item("Sheet1")
    
    # Initialize Dealer Name header at Col 10 if missing
    $headerCol10 = $sheet.Cells.Item(1, 10).Text
    if ($headerCol10 -eq "") {
        Write-Host "Initializing Column 10 header as 'Dealer name'..." -ForegroundColor Gray
        $sheet.Cells.Item(1, 10).Value2 = "Dealer name"
    }

    $rows = $sheet.UsedRange.Rows.Count
    Write-Host "Workbook open. Total spreadsheet rows: $rows" -ForegroundColor Yellow

    # Collect rows that contain URLs and are not yet processed
    $rowsToProcess = @()
    for ($r = 2; $r -le $rows; $r++) {
        $url = $sheet.Cells.Item($r, 1).Text
        if ($url -like "http*") {
            $existingName = $sheet.Cells.Item($r, 2).Text.Trim()
            $existingTotal = $sheet.Cells.Item($r, 9).Text.Trim()
            if ($existingName -eq "" -and $existingTotal -eq "") {
                $rowsToProcess += @{ RowIndex = $r; Url = $url }
            }
        }
    }

    Write-Host "Found $($rowsToProcess.Count) unprocessed rows with image URLs to process." -ForegroundColor Green

    for ($i = 0; $i -lt $rowsToProcess.Count; $i++) {
        $item = $rowsToProcess[$i]
        $r = $item.RowIndex
        $url = $item.Url
        
        Write-Host ""
        Write-Host "--- Processing Row $r ($($i + 1) of $($rowsToProcess.Count)) ---" -ForegroundColor Blue
        Write-Host "URL: $url" -ForegroundColor Gray
        
        # Download image
        $tempFile = Join-Path $env:TEMP "invoice_row_${r}.jpg"
        $downloadSuccess = $false
        
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $tempFile -UserAgent "Mozilla/5.0" -ErrorAction Stop
            $downloadSuccess = $true
        }
        catch {
            Write-Host "Error downloading image: $_" -ForegroundColor Red
        }

        if (-not $downloadSuccess) {
            Write-Host "Skipping Row $r due to download failure." -ForegroundColor Red
            continue
        }

        # Encode to Base64
        $base64Image = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($tempFile))
        Remove-Item $tempFile -Force | Out-Null

        # Call Gemini API with Retries
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

        $models = @(
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-1.5-flash"
        )
        $currentModelIndex = 0

        while ($retries -gt 0 -and -not $success) {
            $modelName = $models[$currentModelIndex]
            $uri = "https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=$apiKey"
            try {
                $response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json" -TimeoutSec 45
                $extractedText = $response.candidates[0].content.parts[0].text
                $success = $true
            }
            catch {
                $status = 0
                if ($null -ne $_.Exception.Response) {
                    $status = [int]$_.Exception.Response.StatusCode
                }
                Write-Host "API Call Error ($modelName): $_ (Status: $status)" -ForegroundColor Red
                
                if ($status -eq 429 -or $_.Message -like "*Too Many Requests*") {
                    $currentModelIndex++
                    if ($currentModelIndex -ge $models.Count) {
                        Write-Host "All models rate-limited/exhausted. Sleeping 30s before retry..." -ForegroundColor Yellow
                        $currentModelIndex = 0
                        Start-Sleep -Seconds 30
                        $retries--
                    } else {
                        Write-Host "Model $modelName limit reached. Falling back to $($models[$currentModelIndex])..." -ForegroundColor Yellow
                    }
                }
                else {
                    Write-Host "Sleeping 10 seconds before retry..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 10
                    $retries--
                }
            }
        }

        if (-not $success) {
            Write-Host "Failed to extract data for Row $r after multiple retries. Skipping." -ForegroundColor Red
            continue
        }

        # Parse extracted JSON
        try {
            $extractedObj = ConvertFrom-Json -InputObject $extractedText
            
            # Clean fields
            $customerName   = Clean-Field   $extractedObj.CustomerName
            $customerMobile = Clean-Mobile  $extractedObj.CustomerMobile
            $vehicleNumber  = Clean-Vehicle $extractedObj.VehicleNumber
            $size           = Clean-Field   $extractedObj.Size
            $pattern        = Clean-Field   $extractedObj.Pattern
            $dot            = Clean-Field   $extractedObj.DOT
            $cost           = Clean-Cost    $extractedObj.Cost
            $totalCost      = Clean-Cost    $extractedObj.TotalCost
            $dealerName     = Clean-Field   $extractedObj.DealerName
            
            # Enforce DOT starts with DOT prefix
            if ($dot -ne "" -and $dot -notlike "DOT*") {
                $dot = "DOT $dot"
            }

            # Write to Excel (ACTION B)
            $sheet.Cells.Item($r, 2).Value2 = $customerName
            $sheet.Cells.Item($r, 3).Value2 = $customerMobile
            $sheet.Cells.Item($r, 4).Value2 = $vehicleNumber
            $sheet.Cells.Item($r, 5).Value2 = $size
            $sheet.Cells.Item($r, 6).Value2 = $pattern
            $sheet.Cells.Item($r, 7).Value2 = $dot
            $sheet.Cells.Item($r, 8).Value2 = $cost
            $sheet.Cells.Item($r, 9).Value2 = $totalCost
            $sheet.Cells.Item($r, 10).Value2 = $dealerName

            # Immediate save/flush to disk (ACTION B)
            $wb.Save()

            # Format and Print clean plain-text log table in terminal (ACTION A)
            Write-Host ""
            Write-Host "+------------+----------------------+------------+------------+" -ForegroundColor Gray
            Write-Host "| Row Number | Customer Name        | Mobile     | Total Cost |" -ForegroundColor Gray
            Write-Host "+------------+----------------------+------------+------------+" -ForegroundColor Gray
            $rStr = $r.ToString().PadRight(10).Substring(0, 10)
            $nStr = $customerName.PadRight(20).Substring(0, 20)
            $mStr = $customerMobile.PadRight(10).Substring(0, 10)
            $tStr = $totalCost.PadRight(10).Substring(0, 10)
            Write-Host "| $rStr | $nStr | $mStr | $tStr |" -ForegroundColor White
            Write-Host "+------------+----------------------+------------+------------+" -ForegroundColor Gray
            Write-Host ""

            $processedCount++
        }
        catch {
            Write-Host "Error parsing Gemini JSON response for Row ${r}: $_" -ForegroundColor Red
            Write-Host "Raw Response: $extractedText" -ForegroundColor DarkRed
        }

        # Apply Rate Limit Defense Pacing
        if ($i -lt ($rowsToProcess.Count - 1)) {
            Write-Host "Sleeping $DelaySeconds seconds (Rate Limit Defense pacing)..." -ForegroundColor DarkGray
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    # Final Master Save
    Write-Host ""
    Write-Host "Finalizing and saving Excel workbook..." -ForegroundColor Yellow
    $wb.Save()
    Write-Host "Excel saved successfully." -ForegroundColor Green

    # 4. Programmatic Verification Pass
    Write-Host ""
    Write-Host "--- Performing Programmatic Verification ---" -ForegroundColor Cyan
    $skippedRows = @()
    $filledRowsCount = 0
    
    foreach ($item in $rowsToProcess) {
        $r = $item.RowIndex
        $url = $item.Url
        
        # Check if fields are written (we can check Customer Name, Dealer Name or Total Cost)
        $cName = $sheet.Cells.Item($r, 2).Text
        $cTotal = $sheet.Cells.Item($r, 9).Text
        
        if ($cName -eq "" -and $cTotal -eq "") {
            $skippedRows += $r
        } else {
            $filledRowsCount++
        }
    }
    
    Write-Host "Verification Pass Complete:" -ForegroundColor Green
    Write-Host "  Total URLs expected: $($rowsToProcess.Count)" -ForegroundColor Green
    Write-Host "  Successfully filled rows: $filledRowsCount" -ForegroundColor Green
    if ($skippedRows.Count -gt 0) {
        Write-Host "  Skipped/Failed rows: $($skippedRows -join ', ')" -ForegroundColor Red
    } else {
        Write-Host "  No rows were skipped or shifted!" -ForegroundColor Green
    }
}
finally {
    # Release Excel COM Objects safely
    Write-Host "Releasing Excel COM resources..." -ForegroundColor Gray
    if ($null -ne $wb) {
        $wb.Close($true)
    }
    if ($null -ne $excel) {
        $excel.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    Write-Host "Resources released." -ForegroundColor Gray
}
