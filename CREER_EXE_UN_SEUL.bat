@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo Python n'est pas installe ou n'est pas dans PATH.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" python -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements_windows.txt
if errorlevel 1 goto :error

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --noconfirm --clean --onefile --windowed --name "MON SALAIRE" --icon "icon.ico" --add-data "icon.png;." --add-data "assets;assets" main.py
if errorlevel 1 goto :error

echo.
echo APK non concerne : ceci est la version WINDOWS.
echo EXE cree : dist\MON SALAIRE.exe
start "" "%~dp0dist\MON SALAIRE.exe"
pause
exit /b 0

:error
echo Echec de la construction.
pause
exit /b 1
