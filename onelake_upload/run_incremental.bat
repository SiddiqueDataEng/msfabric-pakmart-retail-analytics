@echo off
:: ============================================================
:: PakMart → OneLake  |  INCREMENTAL LOAD
:: Uploads only the 2023 incremental fact_sale CSV.
:: ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   PakMart OneLake Upload  ^|  INCREMENTAL LOAD
echo ============================================================
echo.

python main.py --mode incremental --data-root ..\pakmart_data --log-level INFO

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Incremental load failed. Check the log above.
    pause
    exit /b 1
)

echo.
echo [OK] Incremental load complete.
pause
