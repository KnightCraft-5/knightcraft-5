@echo off
REM Download / update the KnightCraft 5 mod jars from the packwiz metadata.
REM Run this once during setup, and again whenever the mod list changes.
REM Windows. Needs Java (you already have it if Minecraft runs).
cd /d "%~dp0.."

set "BOOT=packwiz-installer-bootstrap.jar"
set "URL=https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest/download/packwiz-installer-bootstrap.jar"

where java >nul 2>nul
if errorlevel 1 (
  echo ERROR: Java not found on PATH. Install a JRE ^(e.g. Temurin^) or run this from Prism.
  pause
  exit /b 1
)

if not exist "%BOOT%" (
  echo Downloading packwiz-installer-bootstrap...
  curl -fsSL -o "%BOOT%" "%URL%"
)

echo Updating mods...
java -jar "%BOOT%" -s client pack.toml
echo Done. Mods are up to date.
pause
