@echo off
REM ============================================================================
REM Nuitka Build Script for spch2txt Recorder Client on Windows
REM ============================================================================
REM This creates a native compiled executable using Nuitka instead of PyInstaller.
REM Nuitka compiles Python to C code, resulting in better antivirus compatibility.

echo ========================================
echo Building spch2txt Recorder Client (Nuitka)
echo ========================================
echo.

REM Try to find Python using multiple methods
set PYTHON_CMD=

REM Method 1: Try py launcher (recommended on Windows)
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    echo Found Python via launcher: 
    py --version
    goto :python_found
)

REM Method 2: Try python command
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    echo Found Python: 
    python --version
    goto :python_found
)

REM Method 3: Try python3 command
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    echo Found Python3: 
    python3 --version
    goto :python_found
)

REM Method 4: Check common installation paths
if exist "C:\Python313\python.exe" (
    set PYTHON_CMD=C:\Python313\python.exe
    echo Found Python at: C:\Python313\python.exe
    goto :python_found
)
if exist "C:\Python312\python.exe" (
    set PYTHON_CMD=C:\Python312\python.exe
    echo Found Python at: C:\Python312\python.exe
    goto :python_found
)
if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    echo Found Python at: C:\Python311\python.exe
    goto :python_found
)
if exist "C:\Python310\python.exe" (
    set PYTHON_CMD=C:\Python310\python.exe
    echo Found Python at: C:\Python310\python.exe
    goto :python_found
)

echo.
echo ERROR: Python not found!
echo.
echo Please install Python 3.10 or higher from:
echo https://www.python.org/downloads/
echo.
echo Make sure to check "Add Python to PATH" during installation.
pause
exit /b 1

:python_found
echo.

REM Check Python version
echo Checking Python version...
%PYTHON_CMD% -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo.
    echo ERROR: Python 3.10 or higher is required!
    echo Your version:
    %PYTHON_CMD% --version
    pause
    exit /b 1
)
echo Python version OK
echo.

REM Install/upgrade pip
echo Ensuring pip is up to date...
%PYTHON_CMD% -m pip install --upgrade pip --quiet
echo.

REM Check if Nuitka is installed
echo Checking for Nuitka...
%PYTHON_CMD% -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo Nuitka not found. Installing...
    %PYTHON_CMD% -m pip install nuitka ordered-set --quiet
    echo Nuitka installed!
) else (
    echo Nuitka found:
    %PYTHON_CMD% -m nuitka --version
)
echo.

REM Check for C compiler (informational only)
echo Checking for C compiler...
where cl >nul 2>&1
if errorlevel 1 (
    echo Microsoft Visual C++ compiler not found.
) else (
    echo Found Microsoft Visual C++ compiler (will use MinGW64 anyway)
)
echo Nuitka will download and use MinGW64 automatically...
echo.

REM Install runtime dependencies
echo ========================================
echo Installing Runtime Dependencies
echo ========================================
echo.
echo Installing Streamlit...
%PYTHON_CMD% -m pip install streamlit --quiet
echo Installing SoundDevice...
%PYTHON_CMD% -m pip install sounddevice --quiet
echo Installing PyAudioWPatch (Windows audio)...
%PYTHON_CMD% -m pip install pyaudiowpatch --quiet
echo Installing Requests (HTTP client)...
%PYTHON_CMD% -m pip install requests --quiet
echo Installing Python-dotenv (config)...
%PYTHON_CMD% -m pip install python-dotenv --quiet
echo Installing NumPy (arrays)...
%PYTHON_CMD% -m pip install numpy --quiet
echo.
echo All dependencies installed!
echo.

REM Clean previous build
if exist "dist\SpchToText_Recorder_Nuitka" (
    echo Cleaning previous build...
    rmdir /s /q "dist\SpchToText_Recorder_Nuitka"
)

REM Build with Nuitka
echo.
echo ========================================
echo Building with Nuitka (using MinGW64)...
echo This will take 10-30 minutes - please be patient
echo ========================================
echo.

%PYTHON_CMD% -m nuitka ^
    --mingw64 ^
    --standalone ^
    --onefile ^
    --windows-console-mode=attach ^
    --enable-plugin=anti-bloat ^
    --noinclude-pytest-mode=nofollow ^
    --noinclude-setuptools-mode=nofollow ^
    --noinclude-IPython-mode=nofollow ^
    --include-package=streamlit ^
    --include-package=sounddevice ^
    --include-package=pyaudiowpatch ^
    --include-package=requests ^
    --include-package=dotenv ^
    --include-package=numpy ^
    --include-package-data=streamlit ^
    --include-data-dir=src/audio=src/audio ^
    --include-data-dir=src/client=src/client ^
    --include-data-dir=src/ui=src/ui ^
    --include-data-file=src/config.py=src/config.py ^
    --include-data-file=.env.example=.env.example ^
    --output-dir=dist ^
    --output-filename=SpchToText_Recorder.exe ^
    --company-name="spch2txt" ^
    --product-name="Speech to Text Recorder" ^
    --file-version=0.1.0 ^
    --product-version=0.1.0 ^
    --file-description="Audio recording client for speech-to-text transcription" ^
    --windows-icon-from-ico=icon.ico ^
    --assume-yes-for-downloads ^
    --show-progress ^
    launcher.py

set BUILD_ERROR=%errorlevel%

if %BUILD_ERROR% neq 0 (
    echo.
    echo ========================================
    echo ERROR: Nuitka build failed! (Error code: %BUILD_ERROR%)
    echo ========================================
    echo.
    echo Common issues:
    echo 1. Missing C compiler - see instructions above
    echo 2. Out of memory - close other applications
    echo 3. Antivirus blocking - temporarily disable
    echo 4. Missing dependencies - check output above
    echo.
    echo Full command that failed:
    echo %PYTHON_CMD% -m nuitka --show-progress launcher.py
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b %BUILD_ERROR%
)

REM Rename output directory
if exist "launcher.dist" (
    move "launcher.dist" "dist\SpchToText_Recorder_Nuitka"
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\SpchToText_Recorder_Nuitka\SpchToText_Recorder.exe
echo.
echo Benefits of Nuitka build:
echo - Compiled native code (better performance)
echo - No PyInstaller bootloader (better AV compatibility)
echo - No runtime unpacking (faster startup)
echo.
echo To run the application:
echo 1. Copy the 'dist\SpchToText_Recorder_Nuitka' folder to your desired location
echo 2. Create a .env file in that folder with your API server URL:
echo    API_BASE_URL=http://your-server:5001
echo 3. Run SpchToText_Recorder.exe
echo.

pause
