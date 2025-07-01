@echo off
echo Generating Pakistani retail data for MS Fabric project...
cd /d %~dp0
python pakistani_retail_data_generator.py
echo.
echo Done! Data generated in pakmart_data folder.
pause
