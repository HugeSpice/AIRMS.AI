# Manual Test Commands for Risk Detection Flow
# Use these commands to test the complete risk detection and mitigation process

$BackendUrl = "http://localhost:8000"

Write-Host "🔍 Manual Risk Detection Test Commands" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Step 1: Create a test user account
Write-Host "`n📝 Step 1: Create a test user account" -ForegroundColor Yellow
$timestamp = [DateTimeOffset]::Now.ToUnixTimeSeconds()
$testEmail = "testuser$timestamp@example.com"
$testPassword = "TestPass123!"

$registrationData = @{
    email = $testEmail
    password = $testPassword
    full_name = "Test User"
} | ConvertTo-Json

Write-Host "Creating account with email: $testEmail" -ForegroundColor Cyan
try {
    $regResponse = Invoke-RestMethod -Uri "$BackendUrl/api/v1/auth/register" -Method POST -Body $registrationData -ContentType "application/json"
    Write-Host "✅ Account created successfully!" -ForegroundColor Green
    Write-Host "User ID: $($regResponse.id)" -ForegroundColor White
} catch {
    Write-Host "❌ Registration failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Login to get authentication token
Write-Host "`n🔐 Step 2: Login to get authentication token" -ForegroundColor Yellow
$loginData = @{
    email = $testEmail
    password = $testPassword
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$BackendUrl/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json"
    $authToken = $loginResponse.access_token
    Write-Host "✅ Login successful!" -ForegroundColor Green
    Write-Host "Token: $($authToken.Substring(0, [Math]::Min(20, $authToken.Length)))..." -ForegroundColor White
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Test the exact command you wanted to test
Write-Host "`n🚀 Step 3: Testing Chat Completion with Risk Detection" -ForegroundColor Yellow
Write-Host "This is the command you wanted to test:" -ForegroundColor Cyan

$chatData = @{
    model = "llama-3.3-70b-versatile"
    messages = @(
        @{
            role = "user"
            content = "Hello, my name is John Smith and my email is john@example.com"
        }
    )
} | ConvertTo-Json -Depth 10

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $authToken"
}

Write-Host "Testing: Invoke-RestMethod -Uri '$BackendUrl/v1/chat/completions' -Method POST -Headers @{'Content-Type'='application/json'; 'Authorization'='Bearer $($authToken.Substring(0, [Math]::Min(20, $authToken.Length)))...'} -Body '$chatData'" -ForegroundColor Gray

try {
    $chatResponse = Invoke-RestMethod -Uri "$BackendUrl/v1/chat/completions" -Method POST -Headers $headers -Body $chatData -TimeoutSec 30
    Write-Host "✅ Chat completion successful!" -ForegroundColor Green
    
    # Check for risk detection metadata
    if ($chatResponse.risk_metadata) {
        Write-Host "`n📊 Risk Detection Results:" -ForegroundColor Cyan
        Write-Host "   Risk Score: $($chatResponse.risk_metadata.overall_risk_score)" -ForegroundColor White
        Write-Host "   Risk Level: $($chatResponse.risk_metadata.risk_level)" -ForegroundColor White
        Write-Host "   Mitigation Applied: $($chatResponse.risk_metadata.mitigation_applied -join ', ')" -ForegroundColor White
    } else {
        Write-Host "`n⚠️ No risk metadata found in response" -ForegroundColor Yellow
    }
    
    # Show the response content
    Write-Host "`n💬 Response Content:" -ForegroundColor Cyan
    Write-Host $chatResponse.choices[0].message.content -ForegroundColor White
    
} catch {
    Write-Host "❌ Chat completion failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorResponse = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorResponse)
        $errorBody = $reader.ReadToEnd()
        Write-Host "Error Details: $errorBody" -ForegroundColor Red
    }
}

# Step 4: Check if risk data was saved
Write-Host "`n📊 Step 4: Checking if risk data was saved to database" -ForegroundColor Yellow
Start-Sleep -Seconds 2

try {
    $statsResponse = Invoke-RestMethod -Uri "$BackendUrl/api/v1/analytics/statistics?days=1" -Method GET -Headers $headers
    Write-Host "✅ Analytics data retrieved!" -ForegroundColor Green
    Write-Host "   Total Requests: $($statsResponse.total_requests)" -ForegroundColor White
    Write-Host "   Average Risk Score: $($statsResponse.avg_risk_score)" -ForegroundColor White
    Write-Host "   High Risk Count: $($statsResponse.high_risk_count)" -ForegroundColor White
    Write-Host "   PII Detections: $($statsResponse.pii_detections)" -ForegroundColor White
} catch {
    Write-Host "❌ Analytics data retrieval failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n=====================================" -ForegroundColor Green
Write-Host "📋 TEST SUMMARY" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ Test completed!" -ForegroundColor Green
Write-Host "`n🔍 What to check next:" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Login with: $testEmail / $testPassword" -ForegroundColor White
Write-Host "3. Go to /dashboard to see if risk detection numbers increased" -ForegroundColor White
Write-Host "4. Check /dashboard/risk-detection for detailed risk logs" -ForegroundColor White
Write-Host "`n🎯 The system should have:" -ForegroundColor Cyan
Write-Host "   - Detected risks in your chat message" -ForegroundColor White
Write-Host "   - Applied mitigation strategies" -ForegroundColor White
Write-Host "   - Saved risk reports to the database" -ForegroundColor White
Write-Host "   - Updated dashboard analytics" -ForegroundColor White
