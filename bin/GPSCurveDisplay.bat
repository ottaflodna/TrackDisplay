@echo off

REM Initialize Conda for cmd.exe
call "%USERPROFILE%\AppData\Local\anaconda3\Scripts\activate.bat"

REM Activate Anaconda base environment
call conda activate base
echo Conda base environment activated


REM Change to project root and set PYTHONPATH
cd /d "%~dp0.."
set PYTHONPATH=%CD%

REM Run the curve viewer application
python scripts\curve_main.py