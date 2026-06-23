@echo off
cd /d "%~dp0"
echo Stopping old Flask instances on port 5000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo Killing PID %%a...
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__
echo Setting API key...
set GROQ_API_KEY=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
echo Starting Agentic DDR web app...
start "Agentic-DDR" cmd /c "python app.py"
echo App running at http://localhost:5000
timeout /t 3 /nobreak >nul
start http://localhost:5000
