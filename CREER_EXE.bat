@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo        MON SALAIRE - CREATION APP WINDOWS
echo ================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo ERREUR : Python n'est pas installe ou n'est pas dans PATH.
  echo Installe Python 3.11 ou 3.12 puis coche "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creation de l'environnement Python...
  python -m venv .venv
  if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"

echo [2/4] Mise a jour de pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [3/4] Installation de Kivy et PyInstaller...
python -m pip install -r requirements_windows.txt
if errorlevel 1 goto :error

echo [4/4] Construction de l'application...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --noconfirm --clean --windowed --name "MON SALAIRE" --icon "icon.ico" --add-data "icon.png;." --add-data "assets;assets" main.py
if errorlevel 1 goto :error

echo.
echo ================================================
echo     CREATION TERMINEE AVEC SUCCES !
echo ================================================
echo.
echo Application :
dist\MON SALAIRE\MON SALAIRE.exe
echo.
echo Double-clique sur le fichier EXE pour lancer MON SALAIRE.
echo.
start "" "%~dp0dist\MON SALAIRE\MON SALAIRE.exe"
pause
exit /b 0

:error
echo.
echo ================================================
echo              ERREUR DE CONSTRUCTION
echo ================================================
echo Consulte le message ci-dessus.
pause
exit /b 1
