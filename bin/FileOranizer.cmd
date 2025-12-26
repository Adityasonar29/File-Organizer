@echo off
setlocal
title File Organizer Pro - Launcher

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found. Please install Python and add it to PATH.
    pause
    exit /b
)

:: 2. Get the directory of this BAT file (the bin folder)
set "BIN_DIR=%~dp0"

:: 3. Go up one level to the root folder
cd /d "%BIN_DIR%.."
set "ROOT_DIR=%cd%"

:: 4. Run the main.py from the src folder relative to root
echo Launching File Organizer...
python "%ROOT_DIR%\scr\main.py"

if %errorlevel% neq 0 (
    echo.
    echo [PROCESS ENDED WITH ERRORS]
    echo Looked for main.py at: %ROOT_DIR%\src\main.py
    pause
)