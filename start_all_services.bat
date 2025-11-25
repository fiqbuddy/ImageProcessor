@echo off
REM Start all image processing services

echo 🚀 Starting Image Processing Pipeline Services...
echo.

start "Resize Service" cmd /k "python services\resize_service.py"
timeout /t 1 /nobreak >nul

start "Filter Service" cmd /k "python services\filter_service.py"
timeout /t 1 /nobreak >nul

start "Watermark Service" cmd /k "python services\watermark_service.py"
timeout /t 1 /nobreak >nul

start "Orchestrator Service" cmd /k "python services\orchestrator_service.py"
timeout /t 2 /nobreak >nul

echo.
echo ✅ All services started!
echo.
echo Service Ports:
echo   - Resize Service:      50052
echo   - Filter Service:      50053
echo   - Watermark Service:   50054
echo   - Orchestrator:        50055
echo.
echo To run the demo:
echo   python client\pipeline_demo.py
echo.
pause
