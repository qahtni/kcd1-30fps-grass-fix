@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem 30 FPS Grass and Water Fix 1.1.0 - installer for Windows.
rem Double-click it in the extracted archive, wherever that is (for example Downloads).
rem It finds the game itself: in every Steam library, else in the GOG Galaxy and Epic default
rem folders. To pick a folder yourself, drag the game folder onto this file.
rem What it does (nothing else):
rem   1. Checks the game is closed.
rem   2. Copies install\KCDGrassFix.asi (grass), install\KCDWater.asi (water ripples) and
rem      install\version.dll (Ultimate ASI Loader) to Bin\Win64, next to KingdomCome.exe.
rem      A different version.dll that is already there is left alone.
rem      If the mod "Native DLSS Support" (KCDDLSS.asi) is installed: it already contains the grass
rem      fix, so the grass plugin is stored as KCDGrassFix.asi.off (not loaded; the DLSS uninstaller
rem      turns it back on). The water plugin is installed as usual.
rem   3. Copies the uninstaller to the game folder as 30FPSGrassWaterFix-Uninstall.bat (and removes
rem      30FPSGrassFix-Uninstall.bat of version 1.0.0).
rem No game file is changed. Windows needs no launch option: it loads version.dll from the game
rem folder by itself. Files are recognised by their exact size in bytes.
title 30 FPS Grass ^& Water Fix - install
set "ASI_SIZE=@ASI_SIZE@"
set "WATER_SIZE=@WATER_SIZE@"
set "UAL_SIZE=@UAL_SIZE@"
set "SELF=%~dp0"
set "SELF=%SELF:~0,-1%"
set "ARG=%~1"
echo 30 FPS Grass ^& Water Fix 1.1.0 - install
call :findgame
if not defined GAME goto :nogame
echo Game folder: "%GAME%"
set "B=%GAME%\Bin\Win64"
tasklist /fi "imagename eq KingdomCome.exe" 2>nul | find /i "KingdomCome.exe" >nul && goto :running
if not exist "%SELF%\install\KCDGrassFix.asi" (set "ERR=install\KCDGrassFix.asi is missing from the extracted folder." & goto :fail)
if not exist "%SELF%\install\KCDWater.asi" (set "ERR=install\KCDWater.asi is missing from the extracted folder." & goto :fail)
if not exist "%SELF%\install\version.dll" (set "ERR=install\version.dll is missing from the extracted folder." & goto :fail)
call :size "%SELF%\install\KCDGrassFix.asi" SZ
if not "%SZ%"=="%ASI_SIZE%" (set "ERR=install\KCDGrassFix.asi is damaged. Download the mod again." & goto :fail)
call :size "%SELF%\install\KCDWater.asi" SZ
if not "%SZ%"=="%WATER_SIZE%" (set "ERR=install\KCDWater.asi is damaged. Download the mod again." & goto :fail)
call :size "%SELF%\install\version.dll" SZ
if not "%SZ%"=="%UAL_SIZE%" (set "ERR=install\version.dll is damaged. Download the mod again." & goto :fail)

if exist "%B%\KCDDLSS.asi" goto :grassoff
copy /y /b "%SELF%\install\KCDGrassFix.asi" "%B%\KCDGrassFix.asi" >nul || goto :copyfail
del /q "%B%\KCDGrassFix.asi.off" "%B%\KCDGrassFix.log" 2>nul
echo Grass: Bin\Win64\KCDGrassFix.asi copied.
goto :water
:grassoff
copy /y /b "%SELF%\install\KCDGrassFix.asi" "%B%\KCDGrassFix.asi.off" >nul || goto :copyfail
del /q "%B%\KCDGrassFix.asi" "%B%\KCDGrassFix.log" 2>nul
echo Grass: Native DLSS Support is installed and already contains the grass fix.
echo        The grass plugin is stored as KCDGrassFix.asi.off (not loaded). If you uninstall
echo        the DLSS mod, its uninstaller turns it back on.
:water
copy /y /b "%SELF%\install\KCDWater.asi" "%B%\KCDWater.asi" >nul || goto :copyfail
del /q "%B%\KCDWater.log" 2>nul
echo Water: Bin\Win64\KCDWater.asi copied.
set "CUR="
if exist "%B%\version.dll" call :size "%B%\version.dll" CUR
if defined CUR if not "%CUR%"=="%UAL_SIZE%" goto :foreign
copy /y /b "%SELF%\install\version.dll" "%B%\version.dll" >nul || goto :copyfail
copy /y "%SELF%\install\Ultimate-ASI-Loader-LICENSE.txt" "%B%\Ultimate-ASI-Loader-LICENSE.txt" >nul 2>nul
echo Loader: Bin\Win64\version.dll copied (Ultimate ASI Loader).
goto :uninstaller
:foreign
echo Loader: Bin\Win64\version.dll is already there and is a different file. Left alone.
echo         If it is an ASI loader, the fix loads through it. Check Bin\Win64\KCDWater.log after a start.

:uninstaller
del /q "%GAME%\30FPSGrassFix-Uninstall.bat" 2>nul
copy /y "%SELF%\Uninstall-Windows.bat" "%GAME%\30FPSGrassWaterFix-Uninstall.bat" >nul && echo Uninstaller copied to the game folder: 30FPSGrassWaterFix-Uninstall.bat
echo.
echo Done. No launch options are needed on Windows. Start the game.
echo Bin\Win64\KCDGrassFix.log then says "grass fix applied" (with the DLSS mod: KCDDLSS.log)
echo and Bin\Win64\KCDWater.log says "mode 1 (smooth ripples)".
echo.
pause
exit /b 0

:copyfail
set "ERR=Could not copy into Bin\Win64 (no permission?). Try right-click, Run as administrator."
goto :fail
:nogame
set "ERR=Kingdom Come: Deliverance not found. Drag the game folder (the one with Bin, Data and Engine) onto this file."
goto :fail
:running
set "ERR=The game is running. Close it first."
:fail
echo.
setlocal EnableDelayedExpansion
echo ERROR: !ERR!
endlocal
echo Nothing more was changed.
echo.
pause
exit /b 1

:size
set "%~2=%~z1"
exit /b

rem Game folder search: around this file, the dragged folder, Steam libraries, GOG/Epic defaults.
:findgame
set "GAME="
for %%I in ("%SELF%\..\..") do if exist "%%~fI\Bin\Win64\KingdomCome.exe" set "GAME=%%~fI"
if defined GAME exit /b
if exist "%SELF%\Bin\Win64\KingdomCome.exe" (set "GAME=%SELF%" & exit /b)
if defined ARG call :trydir "%ARG%"
if defined GAME exit /b
set "STEAM="
for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Valve\Steam" /v SteamPath 2^>nul ^| find /i "SteamPath"') do set "STEAM=%%B"
if not defined STEAM set "STEAM=%ProgramFiles(x86)%\Steam"
set "STEAM=%STEAM:/=\%"
call :trylib "%STEAM%"
if exist "%STEAM%\steamapps\libraryfolders.vdf" for /f usebackq^ tokens^=2^,4^ delims^=^" %%A in ("%STEAM%\steamapps\libraryfolders.vdf") do if /i "%%A"=="path" call :trylib "%%B"
if defined GAME exit /b
call :trydir "%ProgramFiles(x86)%\GOG Galaxy\Games\Kingdom Come Deliverance"
call :trydir "%ProgramFiles%\Epic Games\KingdomComeDeliverance"
exit /b
:trylib
if defined GAME exit /b
set "L=%~1"
set "L=%L:\\=\%"
call :trydir "%L%\steamapps\common\KingdomComeDeliverance"
exit /b
:trydir
if not defined GAME if exist "%~1\Bin\Win64\KingdomCome.exe" set "GAME=%~f1"
exit /b
