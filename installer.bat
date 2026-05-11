@echo off
chcp 65001 >nul
echo.
echo  ╔══════════════════════════════════════╗
echo  ║   CkiLePatron — Installation         ║
echo  ╚══════════════════════════════════════╝
echo.

:: ── 1. Trouver ou installer Python ───────────────────────────────────────
set PYTHON=

:: Chercher Python dans le PATH
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    goto :python_ok
)

:: Chercher dans les emplacements courants
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%~P
        goto :python_ok
    )
)

:: Python introuvable — téléchargement automatique
echo  Python n'est pas installé. Téléchargement en cours...
echo  (environ 25 Mo, merci de patienter)
echo.

set PY_URL=https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe
set PY_INSTALLER=%TEMP%\python_installer.exe

powershell -NoProfile -Command "Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_INSTALLER%'" >nul 2>&1

if not exist "%PY_INSTALLER%" (
    echo  [ERREUR] Le téléchargement a échoué. Vérifiez votre connexion internet.
    echo  Vous pouvez installer Python manuellement : https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  Installation de Python...
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
del "%PY_INSTALLER%"

set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if not exist "%PYTHON%" (
    echo  [ERREUR] L'installation de Python a échoué.
    pause
    exit /b 1
)

echo  ✓ Python installé.
echo.

:python_ok
"%PYTHON%" --version
echo.

:: ── 2. Installer Flask ────────────────────────────────────────────────────
echo  Installation des dépendances...
echo.
"%PYTHON%" -m pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo  [ERREUR] L'installation des dépendances a échoué.
    pause
    exit /b 1
)

:: Mettre à jour lancer.pyw pour utiliser le bon Python si hors PATH
if not "%PYTHON%"=="python" (
    powershell -NoProfile -Command " ^
        $f = Get-Content 'lancer.pyw' -Raw; ^
        $f = $f -replace 'import os', ('import os' + [char]10 + 'import sys'); ^
        if (-not ($f -match 'sys.executable')) { ^
            $insert = 'import subprocess, sys' + [char]10; ^
            $f = $insert + $f ^
        }; ^
        Set-Content 'lancer.pyw' $f ^
    " >nul 2>&1
)

echo.
echo  ✓ Application installée !
echo.
echo  Pour lancer l'application, double-cliquez sur :
echo     lancer.pyw
echo.
echo  Astuce : clic droit sur lancer.pyw ^> "Envoyer vers ^> Bureau"
echo  pour créer un raccourci sur le bureau.

:: ── 3. Extension navigateur ───────────────────────────────────────────────
echo.
echo  ────────────────────────────────────────
echo  Installation de l'extension navigateur
echo  ────────────────────────────────────────
echo.
echo  L'extension permet d'importer un patron depuis Klafoutis en un clic.
echo.
set /p INSTALL_EXT="  Voulez-vous installer l'extension maintenant ? (O/N) : "
if /i not "%INSTALL_EXT%"=="O" goto :FIN

set BROWSER=
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"      set BROWSER=chrome
if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" set BROWSER=chrome
if "%BROWSER%"=="" (
    if exist "%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe" set BROWSER=edge
    if exist "%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"      set BROWSER=edge
)

echo.
echo  Suivez ces 3 étapes dans votre navigateur :
echo.
echo  1. Activez le "Mode developpeur" (interrupteur en haut a droite)
echo  2. Cliquez sur "Charger l'extension non empaquetee"
echo  3. Selectionnez le dossier : %~dp0extension
echo.

start "" explorer "%~dp0extension"

if "%BROWSER%"=="chrome" (
    start "" "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" "chrome://extensions" 2>nul || ^
    start "" "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" "chrome://extensions"
) else if "%BROWSER%"=="edge" (
    start "" msedge "edge://extensions"
) else (
    echo  Navigateur non detecte — ouvrez chrome://extensions manuellement.
)

:FIN
echo.
echo  ✓ Terminé !
echo.
pause
