@echo off
REM Build script for UserChrome Loader (Windows)

setlocal enabledelayedexpansion

REM Configuration
set APP_NAME=UserChrome Loader
set APP_VERSION=1.0.0
set PYTHON_MIN_VERSION=3.8

REM Colors (if supported)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set CYAN=[96m
set BOLD=[1m
set NC=[0m

echo %CYAN%%BOLD%================================%NC%
echo %CYAN%%BOLD% %APP_NAME% Build Script%NC%
echo %CYAN%%BOLD% Version %APP_VERSION%%NC%
echo %CYAN%%BOLD%================================%NC%
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%Error: Python is not installed or not in PATH%NC%
    echo Please install Python %PYTHON_MIN_VERSION% or higher from https://python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%Found Python %PYTHON_VERSION%%NC%

REM Parse command line arguments
set CLEAN_ONLY=false
set DEPS_ONLY=false
set NO_TEST=false
set DEBUG=false

:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-h" goto :show_help
if /i "%~1"=="--clean" (
    set CLEAN_ONLY=true
    shift
    goto :parse_args
)
if /i "%~1"=="--deps" (
    set DEPS_ONLY=true
    shift
    goto :parse_args
)
if /i "%~1"=="--no-test" (
    set NO_TEST=true
    shift
    goto :parse_args
)
if /i "%~1"=="--debug" (
    set DEBUG=true
    shift
    goto :parse_args
)
echo %RED%Unknown option: %~1%NC%
goto :show_help

:args_done

REM Change to script directory
cd /d "%~dp0"

if "%CLEAN_ONLY%"=="true" goto :clean_build
if "%DEPS_ONLY%"=="true" goto :install_deps

REM Full build process
goto :install_deps

:install_deps
echo.
echo %CYAN%%BOLD%Installing Dependencies%NC%
echo ================================

echo %BLUE%Upgrading pip...%NC%
python -m pip install --upgrade pip
if errorlevel 1 (
    echo %RED%Failed to upgrade pip%NC%
    pause
    exit /b 1
)

if exist requirements.txt (
    echo %BLUE%Installing from requirements.txt...%NC%
    python -m pip install -r requirements.txt
) else (
    echo %BLUE%Installing basic dependencies...%NC%
    python -m pip install PyQt6 pyinstaller pycurl libarchive-c
)

if errorlevel 1 (
    echo %RED%Failed to install dependencies%NC%
    echo.
    echo Try installing dependencies manually:
    echo pip install PyQt6 pyinstaller pycurl libarchive-c
    pause
    exit /b 1
)

echo %GREEN%Dependencies installed successfully%NC%

if "%DEPS_ONLY%"=="true" goto :end

:clean_build
echo.
echo %CYAN%%BOLD%Cleaning Previous Build%NC%
echo ================================

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM Clean Python cache files
for /f "delims=" %%i in ('dir /s /b /ad __pycache__ 2^>nul') do rmdir /s /q "%%i" 2>nul
for /f "delims=" %%i in ('dir /s /b *.pyc 2^>nul') do del /q "%%i" 2>nul

echo %GREEN%Build artifacts cleaned%NC%

if "%CLEAN_ONLY%"=="true" goto :end

:build_executable
echo.
echo %CYAN%%BOLD%Building Executable%NC%
echo ================================

if exist main.spec (
    echo %BLUE%Using spec file: main.spec%NC%
    python -m PyInstaller --clean --noconfirm main.spec
) else (
    echo %BLUE%Building without spec file%NC%
    python -m PyInstaller --onefile --windowed --name userchrome-loader --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui --hidden-import PyQt6.sip --hidden-import pycurl --hidden-import libarchive src/launcher.py
)

if errorlevel 1 (
    echo %RED%Build failed%NC%
    pause
    exit /b 1
)

echo %GREEN%Build completed successfully%NC%

if "%NO_TEST%"=="true" goto :build_complete

:test_executable
echo.
echo %CYAN%%BOLD%Testing Executable%NC%
echo ================================

if exist "dist\userchrome-loader.exe" (
    echo %BLUE%Testing executable...%NC%
    
    REM Get file size
    for %%A in ("dist\userchrome-loader.exe") do set FILE_SIZE=%%~zA
    set /a FILE_SIZE_MB=!FILE_SIZE!/1024/1024
    
    echo %BLUE%Executable size: !FILE_SIZE_MB! MB%NC%
    echo %BLUE%Location: %CD%\dist\userchrome-loader.exe%NC%
    
    REM Try to run with timeout (basic test)
    timeout 3 >nul 2>&1
    if errorlevel 1 (
        echo %YELLOW%Cannot test executable automatically%NC%
    ) else (
        echo %GREEN%Executable created successfully%NC%
    )
) else (
    echo %RED%Executable not found in dist\%NC%
    pause
    exit /b 1
)

:build_complete
echo.
echo %CYAN%%BOLD%Build Complete%NC%
echo ================================
echo %GREEN%✓ %APP_NAME% built successfully!%NC%
echo %BLUE%Executable location: %CD%\dist\userchrome-loader.exe%NC%
echo.
echo You can now run the application from:
echo   %CD%\dist\userchrome-loader.exe
echo.
goto :end

:show_help
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   --help, -h          Show this help message
echo   --clean             Clean build artifacts only
echo   --deps              Install dependencies only
echo   --no-test           Skip executable testing
echo   --debug             Enable debug output
echo.
echo Examples:
echo   %~nx0                  # Full build
echo   %~nx0 --clean          # Clean only
echo   %~nx0 --deps           # Install deps only
echo.
goto :end

:end
if "%DEBUG%"=="true" pause
endlocal