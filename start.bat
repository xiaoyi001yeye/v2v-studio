@echo off
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run setup.bat first.
  exit /b 1
)

if not exist .env (
  copy .env.example .env >nul
  echo Created .env. Please set ARK_API_KEY before starting.
  notepad .env
  exit /b 1
)

.venv\Scripts\python.exe app.py
