@echo off
cd "%~dp0"
call venv\Scripts\activate.bat
python transcriptor.py
pause 