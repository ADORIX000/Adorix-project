#!/usr/bin/env pwsh
<#
.SYNOPSIS
Adorix Project - Complete Startup Script
Launches all required components
#>

Write-Host "`n"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      ADORIX PROJECT - STARTUP          " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will open 3 terminals in new windows:"
Write-Host "  1. Core Controller (vision + ads detection)" -ForegroundColor Yellow
Write-Host "  2. WebSocket Server (backend server)" -ForegroundColor Yellow
Write-Host "  3. Frontend UI (http://localhost:5173)" -ForegroundColor Yellow
Write-Host ""

# Get the project root
$ProjectRoot = Split-Path -Parent $PSCommandPath

# Terminal 1: Core Controller
Write-Host "Starting Core Controller..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$ProjectRoot'; python -m core_controller.main`"" -WindowStyle Normal

Start-Sleep -Seconds 2

# Terminal 2: WebSocket Server
Write-Host "Starting WebSocket Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$ProjectRoot'; python -m core_controller.websocket_server`"" -WindowStyle Normal

Start-Sleep -Seconds 2

# Terminal 3: Frontend
Write-Host "Starting Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$ProjectRoot\frontend'; npm run dev`"" -WindowStyle Normal

Write-Host "`n"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ All components are starting!         " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n📱 Open browser: http://localhost:5173`n" -ForegroundColor Yellow
Write-Host "📷 Camera window should pop up now`n" -ForegroundColor Yellow
Write-Host "⏸️  Press Ctrl+C in each terminal to stop`n" -ForegroundColor Yellow
