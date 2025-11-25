@echo off
REM Stop all running gRPC services

echo Stopping all services...

REM Kill any Python processes running our services
taskkill /F /IM python.exe /FI "WINDOWTITLE eq User Service*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Movie Service*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Payment Service*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Notification Service*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Booking Service*" 2>nul

REM Kill by PID if found on our ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":50051.*LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":50052.*LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":50053.*LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":50054.*LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":50055.*LISTENING"') do taskkill /F /PID %%a 2>nul

echo.
echo All services stopped!
