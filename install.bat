@echo off
echo ====================================
echo Smart File Organizer - Installation
echo ====================================
echo.

echo Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    echo Veuillez installer Python depuis https://python.org
    pause
    exit /b 1
)

echo Python detecte avec succes!
echo.

echo Installation des dependances...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERREUR: Echec de l'installation des dependances
    echo Verifiez votre connexion internet et reessayez
    pause
    exit /b 1
)

echo.
echo ====================================
echo Installation terminee avec succes!
echo ====================================
echo.
echo Pour lancer le programme: python main.py
echo.
pause
