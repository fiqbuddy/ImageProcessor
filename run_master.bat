@echo off
setlocal

echo ==========================================
echo 🎮 Image Processing Master Node Launcher
echo ==========================================
echo.

set /p WORKER_IP="Enter Device 1 (Worker) IP Address: "

echo.
echo ⚙️ Configuring Environment...
set RESIZE_SERVICE_HOSTS=%WORKER_IP%:50052,%WORKER_IP%:50062,%WORKER_IP%:50072
set FILTER_SERVICE_HOSTS=%WORKER_IP%:50053,%WORKER_IP%:50063,%WORKER_IP%:50073
set WATERMARK_SERVICE_HOSTS=%WORKER_IP%:50054,%WORKER_IP%:50064

echo.
echo 📋 Configuration:
echo    Worker IP: %WORKER_IP%
echo    Resize Hosts: %RESIZE_SERVICE_HOSTS%
echo.

echo 🚀 Starting Orchestrator...
python services/orchestrator_service.py

pause
