# Two-step process: Generate then Save
$BackendUrl = "https://ca-backend-sbuxstudio.delightfulground-306a1d02.eastus2.azurecontainerapps.io"

Write-Host "`n=== Two-Step Test: Generate + Save ===" -ForegroundColor Cyan

# Step 1: Generate image
Write-Host "`nStep 1: Generating image..." -ForegroundColor Yellow

$generateBody = @{
    prompt = "A simple blue circle on white background"
    model = "gpt-image-1"
    n = 1
    quality = "low"
    size = "auto"
} | ConvertTo-Json

try {
    $genResult = Invoke-RestMethod -Uri "$BackendUrl/api/v1/images/generate" `
        -Method POST `
        -ContentType "application/json" `
        -Body $generateBody `
        -TimeoutSec 120
    
    if ($genResult.success -and $genResult.images.Count -gt 0) {
        Write-Host "✅ Image generated successfully!" -ForegroundColor Green
        $imageUrl = $genResult.images[0].url
        Write-Host "   Image URL (base64): $($imageUrl.Substring(0,50))..." -ForegroundColor Gray
        
        # Step 2: Save the generated image
        Write-Host "`nStep 2: Saving image to storage and Cosmos DB..." -ForegroundColor Yellow
        
        $saveBody = @{
            image_url = $imageUrl
            filename = "test-robot-$(Get-Date -Format 'yyyyMMdd-HHmmss').png"
            folder_path = "test-images"
            prompt = "A simple blue circle on white background"
            model = "gpt-image-1"
        } | ConvertTo-Json
        
        $saveResult = Invoke-RestMethod -Uri "$BackendUrl/api/v1/images/save" `
            -Method POST `
            -ContentType "application/json" `
            -Body $saveBody `
            -TimeoutSec 60
        
        if ($saveResult.success) {
            Write-Host "✅ Image saved successfully!" -ForegroundColor Green
            Write-Host "   Blob Name: $($saveResult.blob_name)" -ForegroundColor White
            Write-Host "   URL: $($saveResult.url)" -ForegroundColor White
            Write-Host "   Container: $($saveResult.container)" -ForegroundColor White
        } else {
            Write-Host "❌ Save failed: $($saveResult.message)" -ForegroundColor Red
        }
        
        # Step 3: Verify in gallery
        Write-Host "`nStep 3: Verifying in gallery..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2  # Give Cosmos DB a moment to index
        
        $gallery = Invoke-RestMethod -Uri "$BackendUrl/api/v1/gallery/images?limit=10" -Method GET
        Write-Host "✅ Total images now: $($gallery.total)" -ForegroundColor Green
        
        if ($gallery.total -gt 0) {
            Write-Host "`n📸 Images in gallery:" -ForegroundColor Cyan
            foreach ($item in $gallery.items) {
                Write-Host "   - $($item.name) ($(([math]::Round($item.size/1KB,2))) KB)" -ForegroundColor White
            }
        }
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
