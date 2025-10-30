# Backend API Test Script
# Tests the deployed Visionary Lab backend API

$BackendUrl = "https://ca-backend-sbuxstudio--0000001.delightfulground-306a1d02.eastus2.azurecontainerapps.io"

Write-Host "`n=== Visionary Lab Backend API Test Suite ===" -ForegroundColor Cyan
Write-Host "Backend: $BackendUrl`n" -ForegroundColor White

# Test 1: Root Endpoint
Write-Host "Test 1: Root Endpoint..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/" -Method GET
    if ($response.message -eq "Welcome to AI Content Lab API") {
        Write-Host " ✅ PASSED" -ForegroundColor Green
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Health Check
Write-Host "Test 2: Health Check..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/health" -Method GET
    if ($response.status -eq "ok") {
        Write-Host " ✅ PASSED" -ForegroundColor Green
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Environment Variables
Write-Host "Test 3: Environment Variables..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/env/status" -Method GET
    if ($response.missing.Count -eq 0) {
        Write-Host " ✅ PASSED (All required vars set)" -ForegroundColor Green
    } else {
        Write-Host " ⚠️  WARNING (Missing: $($response.missing -join ', '))" -ForegroundColor Yellow
    }
} catch {
    Write-Host " ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Cosmos DB Status
Write-Host "Test 4: Cosmos DB Connection..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/gallery/metadata/status" -Method GET
    if ($response.metadata_service.health.status -eq "healthy") {
        Write-Host " ✅ PASSED (Total assets: $($response.metadata_service.total_assets))" -ForegroundColor Green
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Gallery Listing
Write-Host "Test 5: Gallery API..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/gallery/images?limit=5" -Method GET
    if ($response.success) {
        Write-Host " ✅ PASSED (Found $($response.total) images)" -ForegroundColor Green
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Image Generation (gpt-image-1)
Write-Host "Test 6: Image Generation (gpt-image-1)..." -NoNewline
try {
    $body = @{
        prompt = "A simple test image: blue circle on white background"
        model = "gpt-image-1"
        n = 1
        size = "auto"
        quality = "low"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/images/generate" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 120
    if ($response.success -and $response.images.Count -gt 0) {
        Write-Host " ✅ PASSED (Generated $($response.images.Count) image(s))" -ForegroundColor Green
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: LLM Prompt Enhancement
Write-Host "Test 7: LLM Service (Prompt Enhancement)..." -NoNewline
try {
    $body = @{
        original_prompt = "cat"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/videos/prompt/enhance" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 60
    if ($response.enhanced_prompt.Length -gt 10) {
        Write-Host " ✅ PASSED" -ForegroundColor Green
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host " ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Suite Complete ===" -ForegroundColor Cyan
Write-Host ""
