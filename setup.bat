@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set PYTHON=py
) else (
  set PYTHON=python
)

if not exist .venv (
  %PYTHON% -m venv .venv
  if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :error
pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist .env copy .env.example .env >nul

echo.
echo Setup complete.
echo Edit .env and set ARK_API_KEY, then run start.bat
exit /b 0

:error
echo.
echo Setup failed.
exit /b 1
