@echo off
:: ============================================================
:: PakMart → OneLake  |  DRY RUN
:: Shows exactly what would be uploaded without touching OneLake.
:: Safe to run without any credentials configured.
:: ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   PakMart OneLake Upload  ^|  DRY RUN  (no files uploaded)
echo ============================================================
echo.

:: Override credentials with dummies so config validation doesn't block dry-run
set AZURE_TENANT_ID=dry-run
set AZURE_CLIENT_ID=dry-run
set AZURE_CLIENT_SECRET=dry-run
set FABRIC_WORKSPACE_ID=dry-run
set FABRIC_LAKEHOUSE_ID=dry-run

python main.py --mode full --dry-run --data-root ..\pakmart_data

echo.
echo [DRY RUN] Done. No files were uploaded.
pause
