# Setup Azure OpenAI Environment Variables for azd
Write-Host "`n=== Azure OpenAI Configuration Setup ===" -ForegroundColor Cyan
Write-Host "This script will configure the Azure OpenAI settings for your deployment.`n" -ForegroundColor White

# Image Generation (gpt-image-1)
Write-Host "📸 Image Generation (gpt-image-1)" -ForegroundColor Yellow
$IMAGEGEN_RESOURCE = Read-Host "Enter your Azure OpenAI resource name for image generation (e.g., 'tribixo')"
$IMAGEGEN_DEPLOYMENT = Read-Host "Enter your gpt-image-1 deployment name (e.g., 'gpt-image-1')"
$IMAGEGEN_API_KEY = Read-Host "Enter your image generation API key" -AsSecureString
$IMAGEGEN_API_KEY_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($IMAGEGEN_API_KEY))

# LLM (GPT-4o)
Write-Host "`n🤖 LLM Service (GPT-4o)" -ForegroundColor Yellow
$LLM_RESOURCE = Read-Host "Enter your Azure OpenAI resource name for LLM (e.g., 'tribixo')"
$LLM_DEPLOYMENT = Read-Host "Enter your GPT-4o deployment name (e.g., 'gpt-4o')"
$LLM_API_KEY = Read-Host "Enter your LLM API key" -AsSecureString
$LLM_API_KEY_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($LLM_API_KEY))

# Sora (Video Generation) - Optional
Write-Host "`n🎬 Video Generation (Sora) - Optional" -ForegroundColor Yellow
$configureSora = Read-Host "Do you want to configure Sora? (y/N)"
if ($configureSora -eq 'y' -or $configureSora -eq 'Y') {
    $SORA_RESOURCE = Read-Host "Enter your Azure OpenAI resource name for Sora (e.g., 'tribixo')"
    $SORA_DEPLOYMENT = Read-Host "Enter your Sora deployment name (e.g., 'sora')"
    $SORA_API_KEY = Read-Host "Enter your Sora API key" -AsSecureString
    $SORA_API_KEY_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SORA_API_KEY))
} else {
    $SORA_RESOURCE = ""
    $SORA_DEPLOYMENT = ""
    $SORA_API_KEY_PLAIN = ""
}

Write-Host "`n⚙️  Configuring azd environment..." -ForegroundColor Cyan

# Set environment variables using azd
azd env set IMAGEGEN_AOAI_RESOURCE $IMAGEGEN_RESOURCE
azd env set IMAGEGEN_DEPLOYMENT $IMAGEGEN_DEPLOYMENT
azd env set IMAGEGEN_AOAI_API_KEY $IMAGEGEN_API_KEY_PLAIN

azd env set LLM_AOAI_RESOURCE $LLM_RESOURCE
azd env set LLM_DEPLOYMENT $LLM_DEPLOYMENT
azd env set LLM_AOAI_API_KEY $LLM_API_KEY_PLAIN

if ($SORA_RESOURCE) {
    azd env set SORA_AOAI_RESOURCE $SORA_RESOURCE
    azd env set SORA_DEPLOYMENT $SORA_DEPLOYMENT
    azd env set SORA_AOAI_API_KEY $SORA_API_KEY_PLAIN
}

Write-Host "`n✅ Environment variables configured!" -ForegroundColor Green
Write-Host "`n📦 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Run 'azd provision' to update the infrastructure" -ForegroundColor White
Write-Host "   2. Or run 'azd up' to provision and deploy everything" -ForegroundColor White
Write-Host ""
