# Hotel Booking Engine - Development Server
# Professional Django application startup script

Write-Host "🏨 Hotel Booking Engine - Development Server" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Set environment variables
$env:DJANGO_ENVIRONMENT = "development"
$env:DJANGO_SETTINGS_MODULE = "hotel_booking.settings.development"

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "Python Version: $pythonVersion" -ForegroundColor Cyan

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "✓ Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠ Virtual environment not found." -ForegroundColor Yellow
    Write-Host "Please create one with: python -m venv venv" -ForegroundColor Red
    Write-Host "Then activate: venv\Scripts\Activate.ps1" -ForegroundColor Red
    Write-Host "And install requirements: pip install -r requirements.txt" -ForegroundColor Red
    Write-Host ""
    Write-Host "Continuing without virtual environment..." -ForegroundColor Yellow
}

# Database setup
Write-Host "🗄️ Running database migrations..." -ForegroundColor Yellow
python manage.py makemigrations
python manage.py migrate

# Cleanup tokens
Write-Host "🧹 Cleaning up expired tokens..." -ForegroundColor Yellow
python manage.py cleanup_tokens

# Display server information
Write-Host "🚀 Starting development server..." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "🌐 Server URL: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "⚙️  Admin Panel: http://127.0.0.1:8000/admin" -ForegroundColor Cyan
Write-Host "📋 API Endpoints: /api/accounts/" -ForegroundColor Cyan
Write-Host "📚 Documentation: docs/ folder" -ForegroundColor Cyan
Write-Host "Environment: $($env:DJANGO_ENVIRONMENT)" -ForegroundColor Yellow
Write-Host "Settings: $($env:DJANGO_SETTINGS_MODULE)" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Green

# Start the development server
python manage.py runserver
