# Backend Setup Script for Windows
# Run this script to set up the development environment

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Decision Assistant - Backend Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.9+ from python.org" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists" -ForegroundColor Gray
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Create .env file if it doesn't exist
Write-Host "`nSetting up environment variables..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host ".env file already exists" -ForegroundColor Gray
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created from template" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env file and add your API keys:" -ForegroundColor Yellow
    Write-Host "   - REDDIT_CLIENT_ID" -ForegroundColor Yellow
    Write-Host "   - REDDIT_CLIENT_SECRET" -ForegroundColor Yellow
    Write-Host "   - YOUTUBE_API_KEY" -ForegroundColor Yellow
    Write-Host "   - DATABASE_URL (PostgreSQL connection string)" -ForegroundColor Yellow
    Write-Host "   - REDIS_URL" -ForegroundColor Yellow
    Write-Host "   - SECRET_KEY (generate a random string)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your API keys and database URLs" -ForegroundColor White
Write-Host "2. Make sure PostgreSQL and Redis are running" -ForegroundColor White
Write-Host "3. Run the server: uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "4. Visit http://localhost:8000/docs for API documentation" -ForegroundColor White
Write-Host ""
