@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Creating Python virtual environment...
  py -m venv .venv
  if errorlevel 1 goto error
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo Open http://127.0.0.1:5000 in your browser. Keep this window open.
.venv\Scripts\python.exe app.py
goto end
:error
echo Setup failed. Check Python installation and internet connection, then read README.md.
:end
pause
