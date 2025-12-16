@echo off
REM ============================================================================
REM Build script for spch2txt Recorder Client on Windows
REM ============================================================================
REM This creates a standalone executable that only includes the recording
REM client without server components or ML models.

echo ========================================
echo Building spch2txt Recorder Client
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
if exist "build" (
    echo Cleaning previous build...
    rmdir /s /q build
)
if exist "dist" (
    echo Cleaning previous dist...
    rmdir /s /q dist
)

REM Install minimal dependencies (client only)
echo.
echo Installing client dependencies...
pip install --upgrade pip
pip install streamlit sounddevice requests python-dotenv numpy pyaudiowpatch

REM Build with PyInstaller
echo.
echo Building executable...
pyinstaller recorder_client.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\SpchToText_Recorder\SpchToText_Recorder.exe
echo.
echo To run the application:
echo 1. Copy the entire 'dist\SpchToText_Recorder' folder to your desired location
echo 2. Create a .env file in that folder with your API server URL:
echo    API_BASE_URL=http://your-server:5001
echo 3. Run SpchToText_Recorder.exe
echo.

pause
