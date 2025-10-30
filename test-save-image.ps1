# Test script to generate and save an image to Cosmos DB
$BackendUrl = "https://ca-backend-sbuxstudio--0000001.delightfulground-306a1d02.eastus2.azurecontainerapps.io"

Write-Host "`n=== Testing Image Generation + Save to Cosmos DB ===" -ForegroundColor Cyan

# Step 1: Generate image with analysis and save
Write-Host "`nStep 1: Generating image with analysis and saving to storage..." -ForegroundColor Yellow

$body = @{
    prompt = "A futuristic robot in a library"
    model = "gpt-image-1"
    n = 1
    quality = "low"
    size = "auto"
    folder_path = "test-images"
    generate_filename = $true
    analyze = $true
} | ConvertTo-Json

try {
    Write-Host "Sending request (this may take 30-60 seconds)..." -ForegroundColor Gray
    $result = Invoke-RestMethod -Uri "$BackendUrl/api/v1/images/generate-with-analysis" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 180
    
    if ($result.success) {
        Write-Host "✅ Image generated and saved successfully!" -ForegroundColor Green
        Write-Host "   Blob Name: $($result.blob_name)" -ForegroundColor White
        Write-Host "   URL: $($result.url)" -ForegroundColor White
        if ($result.analysis) {
            Write-Host "   Summary: $($result.analysis.summary)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "❌ Failed: $($result.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}

# Step 2: Verify data in Cosmos DB
Write-Host "`nStep 2: Checking Cosmos DB for saved images..." -ForegroundColor Yellow

try {
    $gallery = Invoke-RestMethod -Uri "$BackendUrl/api/v1/gallery/images?limit=10" -Method GET
    
    Write-Host "✅ Gallery query successful!" -ForegroundColor Green
    Write-Host "   Total images in database: $($gallery.total)" -ForegroundColor White
    
    if ($gallery.total -gt 0) {
        Write-Host "`n📸 Images found:" -ForegroundColor Cyan
        foreach ($item in $gallery.items) {
            Write-Host "   - $($item.name)" -ForegroundColor White
            if ($item.metadata.summary) {
                Write-Host "     Summary: $($item.metadata.summary)" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "   ℹ️  No images saved yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error querying gallery: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
