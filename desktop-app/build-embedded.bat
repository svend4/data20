@echo off
REM ============================================================================
REM Build Script for Embedded Desktop Application (Windows)
REM Phase 7.1: Desktop Embedded Backend
REM
REM This script builds the complete Data20 Desktop Application including:
REM 1. Python backend (PyInstaller)
REM 2. React frontend (Vite)
REM 3. Electron wrapper
REM 4. Windows installer
REM
REM Usage:
REM   build-embedded.bat              # Build for Windows
REM   build-embedded.bat clean        # Clean build
REM ============================================================================

setlocal enabledelayedexpansion

REM Colors (Windows 10+)
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "NC=[0m"

REM Configuration
set "PROJECT_ROOT=%~dp0.."
set "DESKTOP_APP_DIR=%PROJECT_ROOT%\desktop-app"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "DIST_DIR=%PROJECT_ROOT%\dist"

REM Parse arguments
set "CLEAN_BUILD=false"
if "%1"=="clean" set "CLEAN_BUILD=true"
if "%1"=="--clean" set "CLEAN_BUILD=true"

echo %BLUE%============================================%NC%
echo %BLUE%  Data20 Desktop App - Embedded Build%NC%
echo %BLUE%============================================%NC%
echo.

REM ============================================================================
REM Step 0: Clean build (if requested)
REM ============================================================================

if "%CLEAN_BUILD%"=="true" (
  echo %YELLOW%Step 0: Clean Build%NC%
  echo %YELLOW%--------------------------------------%NC%

  echo Removing build artifacts...
  if exist "%DIST_DIR%" rd /s /q "%DIST_DIR%"
  if exist "%DESKTOP_APP_DIR%\dist" rd /s /q "%DESKTOP_APP_DIR%\dist"
  if exist "%DESKTOP_APP_DIR%\build" rd /s /q "%DESKTOP_APP_DIR%\build"
  if exist "%DESKTOP_APP_DIR%\node_modules\.cache" rd /s /q "%DESKTOP_APP_DIR%\node_modules\.cache"

  echo %GREEN%Clean complete%NC%
  echo.
)

REM ============================================================================
REM Step 1: Build Python Backend with PyInstaller
REM ============================================================================

echo %YELLOW%Step 1: Building Python Backend%NC%
echo %YELLOW%--------------------------------------%NC%

cd /d "%PROJECT_ROOT%"

REM Check if PyInstaller is installed
where pyinstaller >nul 2>&1
if errorlevel 1 (
  echo %RED%PyInstaller not found%NC%
  echo Installing PyInstaller...
  pip install pyinstaller
  if errorlevel 1 (
    echo %RED%Failed to install PyInstaller%NC%
    exit /b 1
  )
)

REM Check if backend.spec exists
if not exist "backend.spec" (
  echo %RED%backend.spec not found%NC%
  echo Please create backend.spec first
  exit /b 1
)

REM Build backend
echo Building backend executable...
pyinstaller backend.spec

REM Verify build
if exist "%DIST_DIR%\data20-backend.exe" (
  echo %GREEN%Backend built successfully%NC%
  dir "%DIST_DIR%\data20-backend.exe"
) else (
  echo %RED%Backend build failed%NC%
  exit /b 1
)

echo.

REM ============================================================================
REM Step 2: Install Desktop App Dependencies
REM ============================================================================

echo %YELLOW%Step 2: Installing Desktop App Dependencies%NC%
echo %YELLOW%--------------------------------------%NC%

cd /d "%DESKTOP_APP_DIR%"

if not exist "node_modules" (
  echo Installing npm dependencies...
  call npm install
  if errorlevel 1 (
    echo %RED%Failed to install dependencies%NC%
    exit /b 1
  )
) else (
  echo Dependencies already installed
)

echo %GREEN%Dependencies installed%NC%
echo.

REM ============================================================================
REM Step 3: Build React Frontend
REM ============================================================================

echo %YELLOW%Step 3: Building React Frontend%NC%
echo %YELLOW%--------------------------------------%NC%

REM Check if React app exists
if not exist "%PROJECT_ROOT%\webapp-react" (
  echo %RED%React app not found at ..\webapp-react%NC%
  exit /b 1
)

cd /d "%PROJECT_ROOT%\webapp-react"

REM Install dependencies if needed
if not exist "node_modules" (
  echo Installing React dependencies...
  call npm install
  if errorlevel 1 (
    echo %RED%Failed to install React dependencies%NC%
    exit /b 1
  )
)

REM Build React app
echo Building React frontend...
call npm run build
if errorlevel 1 (
  echo %RED%React build failed%NC%
  exit /b 1
)

REM Copy build to desktop-app
echo Copying React build to desktop-app...
if exist "%DESKTOP_APP_DIR%\build" rd /s /q "%DESKTOP_APP_DIR%\build"
xcopy /E /I /Y "build" "%DESKTOP_APP_DIR%\build"

echo %GREEN%React frontend built%NC%
echo.

REM ============================================================================
REM Step 4: Build Electron Application
REM ============================================================================

echo %YELLOW%Step 4: Building Electron Application%NC%
echo %YELLOW%--------------------------------------%NC%

cd /d "%DESKTOP_APP_DIR%"

echo Building for Windows...
call npm run build -- --win
if errorlevel 1 (
  echo %RED%Electron build failed%NC%
  exit /b 1
)

echo %GREEN%Electron app built%NC%
echo.

REM ============================================================================
REM Step 5: Summary
REM ============================================================================

echo %BLUE%============================================%NC%
echo %BLUE%  Build Complete!%NC%
echo %BLUE%============================================%NC%
echo.

echo Build Artifacts:
echo --------------------------------------

cd /d "%DESKTOP_APP_DIR%\dist"

if exist "*.exe" (
  echo %GREEN%Windows Installers:%NC%
  dir /b *.exe
  echo.
)

REM Total size
for /f "tokens=3" %%a in ('dir /-c ^| find "File(s)"') do set TOTAL_SIZE=%%a
echo Total build size: %TOTAL_SIZE% bytes
echo.

echo %BLUE%============================================%NC%
echo %GREEN%All done!%NC%
echo.
echo Next steps:
echo 1. Test the installer
echo 2. Check that backend starts automatically
echo 3. Verify all features work offline
echo 4. Distribute the installer to users
echo %BLUE%============================================%NC%

endlocal
