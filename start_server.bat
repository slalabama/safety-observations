@echo off
title Safety Observations Server
cd C:\Projects\safety-observations

:loop
echo Starting Safety Observations Server...
echo Visit: http://localhost:8000/admin/
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
echo Server stopped. Restarting in 3 seconds...
timeout /t 3
goto loop
