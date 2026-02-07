@echo off
echo === PastryCalc Windows Build ===
echo.
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller
echo.
echo Building executable...
pyinstaller --onefile --windowed --name PastryCalc --add-data "src/data;data" src/main.py
echo.
echo Done! Executable is in dist\PastryCalc.exe
pause
