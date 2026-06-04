# Startup Script for TaxGenie (1040-NR Tax Filing System)
# Launch this script to run both backend and frontend servers.

$VenvPath = "backend\.venv"
$PythonPath = "C:\Users\rajag\AppData\Local\Programs\Python\Python312\python.exe"
$NpmPath = "C:\Program Files\nodejs\npm.cmd"

# Check if environment is initialized
if (-not (Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Re-initializing..." -ForegroundColor Yellow
    if (-not (Test-Path $PythonPath)) {
        Write-Error "Python 3.12 not found. Cannot auto-setup. Please run setup_all.ps1 first."
        Exit 1
    }
    Write-Host "Creating Virtual Environment..."
    & $PythonPath -m venv $VenvPath
    Write-Host "Installing dependencies..."
    & (Join-Path $VenvPath "Scripts\pip.exe") install -r backend\requirements.txt
}

Write-Host "Starting TaxGenie App..." -ForegroundColor Cyan

# 1. Start Backend FastAPI
Write-Host "Launching Backend on http://localhost:8000..." -ForegroundColor Gray
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Write-Host 'TaxGenie Backend Server Running' -ForegroundColor Cyan; cd backend; .\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"

# 2. Start Frontend Vite
Write-Host "Launching Frontend on http://localhost:5173..." -ForegroundColor Gray
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Write-Host 'TaxGenie Frontend Dev Server Running' -ForegroundColor Cyan; cd frontend; & '$NpmPath' run dev"

# 3. Open Browser
Start-Sleep -Seconds 3
Write-Host "Opening browser..." -ForegroundColor Green
Start-Process "http://localhost:5173"
