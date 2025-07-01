@echo off
:: ============================================================
:: PakMart → OneLake  |  PARTIAL / SELECTIVE LOAD
::
:: Edit the variables below before running:
::   MODE    – dimensions | fact | table:<name>
::   TABLES  – space-separated list of dimension tables (or leave empty)
::   YEARS   – space-separated list of years (or leave empty)
::
:: Examples:
::   MODE=dimensions  TABLES=dimension_city dimension_stock_item
::   MODE=fact        YEARS=2022
::   MODE=table:fact_sale:2021
:: ============================================================
setlocal
cd /d "%~dp0"

:: ── Configure your partial load here ──────────────────────────────────────
set MODE=fact
set TABLES=
set YEARS=2022

:: ── Build argument list ────────────────────────────────────────────────────
set ARGS=--mode %MODE%

if not "%TABLES%"=="" set ARGS=%ARGS% --tables %TABLES%
if not "%YEARS%"==""  set ARGS=%ARGS% --years %YEARS%

echo.
echo ============================================================
echo   PakMart OneLake Upload  ^|  PARTIAL LOAD
echo   Mode   : %MODE%
echo   Tables : %TABLES%
echo   Years  : %YEARS%
echo ============================================================
echo.

python main.py %ARGS% --data-root ..\pakmart_data --log-level INFO

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Partial load failed. Check the log above.
    pause
    exit /b 1
)

echo.
echo [OK] Partial load complete.
pause
