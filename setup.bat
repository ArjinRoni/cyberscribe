@echo off
title CyberScribe Transcriptor Setup

echo ===== CyberScribe Transcriptor Setup =====
echo This script will set up the virtual environment and install dependencies.
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.10 or later.
    pause
    exit /b 1
)

:: Check Python version (basic check)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set version=%%V
echo Detected Python %version%

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please install venv package.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
pip install --upgrade pip

:: Install requirements
echo Installing dependencies... (this may take a while)
pip install -r requirements.txt

:: Check FFmpeg (basic check)
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: FFmpeg not found in PATH. It's recommended for video file processing.
    echo Please install FFmpeg from https://ffmpeg.org/ and add it to your PATH.
    echo.
)

echo.
echo Setup complete! You can now run the application with:
echo transcriptor.bat
echo.

pause 