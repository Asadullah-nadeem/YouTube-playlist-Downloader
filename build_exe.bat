@echo off
REM ====================================================================
REM Media Studio Pro - 1-Click Windows .exe Builder
REM Double-click this script on Windows to package into MediaStudioPro.exe
REM ====================================================================

title Media Studio Pro - Building .EXE
echo ====================================================================
echo  Media Studio Pro - Automated Windows .EXE Generator
echo ====================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your Windows PATH.
    echo Please install Python 3.10+ from python.org and check "Add to PATH".
    pause
    exit /b 1
)

echo [*] Installing required build packages...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [*] Packaging into single-file Windows Executable...
python build_exe.py

echo.
echo ====================================================================
echo Build process completed! Check the 'dist' folder for MediaStudioPro.exe
echo ====================================================================
pause

