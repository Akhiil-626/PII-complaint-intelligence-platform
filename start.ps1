# One-Command Start Script for Privacy-Preserving Complaint Intelligence Platform
$ErrorActionPreference = "Continue"

$RootPath = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }

Write-Host "----------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Starting Complaint Intelligence Platform..." -ForegroundColor Cyan
Write-Host "Project Root: $RootPath" -ForegroundColor Gray
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

# 1. Free port 8000 if occupied
$connections = netstat -ano | Select-String ":8000.*LISTENING"
if ($connections) {
    foreach ($conn in $connections) {
        $parts = ($conn -split '\s+') | Where-Object { $_ -ne "" }
        $procId = $parts[-1]
        if ($procId -and $procId -ne "0") {
            Write-Host "Freeing port 8000 (terminating lingering process PID $procId)..." -ForegroundColor Yellow
            taskkill /F /PID $procId 2>$null
        }
    }
    Start-Sleep -Seconds 1
} else {
    Write-Host "Port 8000 is clean and available." -ForegroundColor Green
}

# 2. Start Backend FastAPI server in a new PowerShell window
Write-Host "Launching Backend API (uvicorn) on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RootPath'; Write-Host 'Starting FastAPI Backend...' -ForegroundColor Green; uvicorn api.main:app --port 8000"

# 3. Start Frontend Vite server in a new PowerShell window
Write-Host "Launching React Frontend dev server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RootPath\frontend'; Write-Host 'Starting Vite Frontend...' -ForegroundColor Green; npm run dev"

# 4. Print running information
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Services Launched Successfully!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Web Application:   http://localhost:5173" -ForegroundColor White
Write-Host " Interactive API:   http://localhost:8000/docs" -ForegroundColor White
Write-Host " Health Endpoint:   http://localhost:8000/api/health" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Note: Neural models load and warm up asynchronously in the background." -ForegroundColor Gray
Write-Host "The frontend top bar health badge will turn green once models are ready." -ForegroundColor Gray
