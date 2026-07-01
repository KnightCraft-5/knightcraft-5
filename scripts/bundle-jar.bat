@echo off
REM CurseForge/Modrinth'te olmayan ya da indirilemeyen bir modu pakete gomer.
REM jar'i mods\ icine kopyalar, git ve packwiz satirlarini ekler, index'i tazeler.
REM Kullanim: scripts\bundle-jar.bat C:\yol\mod.jar
setlocal
cd /d "%~dp0.."

if "%~1"=="" ( echo Kullanim: scripts\bundle-jar.bat C:\yol\mod.jar & exit /b 1 )
if not exist "%~1" ( echo Dosya yok: %~1 & exit /b 1 )

set "NAME=%~nx1"
copy /y "%~1" "mods\%NAME%" >nul

findstr /x /c:"!mods/%NAME%" .gitignore >nul 2>nul || echo !mods/%NAME%>>.gitignore
findstr /x /c:"!mods/%NAME%" .packwizignore >nul 2>nul || echo !mods/%NAME%>>.packwizignore

where packwiz >nul 2>nul && ( packwiz refresh ) || (
  if exist "%USERPROFILE%\go\bin\packwiz.exe" ( "%USERPROFILE%\go\bin\packwiz.exe" refresh ) else ( echo packwiz bulunamadi; elle "packwiz refresh" calistir. )
)

echo Gomuldu: mods\%NAME% - simdi GitHub Desktop'ta commit'leyip push'la.
