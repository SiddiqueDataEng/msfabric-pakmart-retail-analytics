@echo off
:: ============================================================
:: Load ALL PakMart data into the pakmart workspace lakehouse
:: Full load (dimensions + fact 2019-2022) + incremental (2023)
:: ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   PakMart ELT Pipeline
echo   Target: pakmart workspace ^> pakmart Lakehouse ^> Files/pakmart
echo ============================================================
echo.

:: ── Check OneLake Explorer is synced ──────────────────────────────────────
set EXPLORER_PATH=C:\Users\Admin\OneLake - Microsoft\pakmart
if not exist "%EXPLORER_PATH%" (
    echo [ERROR] The pakmart workspace is not synced in OneLake Explorer.
    echo.
    echo  To fix:
    echo    1. Click the OneLake icon in the Windows system tray
    echo    2. Click "Add a workspace"
    echo    3. Select "pakmart" and click Sync
    echo    4. Wait for this folder to appear:
    echo       %EXPLORER_PATH%
    echo    5. Re-run this script
    echo.
    pause
    exit /b 1
)

echo [OK] pakmart workspace found in OneLake Explorer.
echo.

:: ── Step 1: Full load ─────────────────────────────────────────────────────
echo [1/2] Running FULL LOAD (dimensions + fact 2019-2022) ...
python main.py --mode full --data-root ..\pakmart_data --log-level INFO
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Full load failed.
    pause
    exit /b 1
)

echo.

:: ── Step 2: Incremental load ──────────────────────────────────────────────
echo [2/2] Running INCREMENTAL LOAD (fact 2023) ...
python main.py --mode incremental --data-root ..\pakmart_data --log-level INFO
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Incremental load failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   DONE. All PakMart data is now in OneLake.
echo.
echo   Next step: open Fabric and run the notebook:
echo   "PakMart - Data Transformation - Bronze to Silver"
echo   Lakehouse: attach to the lakehouse in the pakmart workspace
echo ============================================================
echo.
pause
