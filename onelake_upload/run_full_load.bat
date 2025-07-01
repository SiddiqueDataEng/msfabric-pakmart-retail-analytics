@echo off
:: ============================================================
:: PakMart → OneLake  |  FULL LOAD
:: Uploads ALL dimension tables + ALL fact_sale year files.
:: ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   PakMart OneLake Upload  ^|  FULL LOAD
echo ============================================================
echo.

python main.py --mode full --data-root ..\pakmart_data --log-level INFO

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Full load failed. Check the log above.
    pause
    exit /b 1
)

echo.
echo [OK] Full load complete.
pause
