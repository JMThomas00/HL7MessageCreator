@echo off
cd /d "%~dp0"

REM --- Install Python 3.11 if not already installed ---
where python3.11 >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing Python 3.11...
    winget install --silent --accept-package-agreements --accept-source-agreements Python.Python.3.11
) else (
    echo Python 3.11 already installed.
)

REM --- Create virtual environment if not already created ---
if not exist ".venv" (
    echo Creating virtual environment...
    python3.11 -m venv .venv
)

REM --- Activate virtual environment ---
call .venv\Scripts\activate

REM --- Ensure pip is up to date inside venv ---
python -m pip install --upgrade pip

REM --- Install required packages inside venv ---
python -m pip install ^
    altgraph==0.17.4 ^
    hl7apy==1.3.5 ^
    numpy ^
    packaging==25.0 ^
    pandas==2.3.2 ^
    pefile==2023.2.7 ^
    pyinstaller==6.1.5 ^
    pyinstaller-hooks-contrib==2025.8 ^
    python-dateutil==2.9.0.post0 ^
    pytz==2025.2 ^
    pywin32-ctypes==0.2.3 ^
    setuptools==80.9.0 ^
    six==1.17.0 ^
    tzdata==2025.2

REM --- Run your Python script inside the venv ---
echo.
echo 🚀 Running HL7MessageCreatorFileView24Allergies.py ...
python HL7MessageCreatorFileView24Allergies.py

echo.
echo ✅ All done! Virtual environment is still active.
echo To deactivate, type: deactivate
echo.

pause
