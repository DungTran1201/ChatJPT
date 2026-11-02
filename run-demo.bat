@echo off
setlocal enabledelayedexpansion

:: Resolve root directory from script location
set "SCRIPT_DIR=%~dp0"

:: Auto-heal PATH for Node.js and Git if session has stale environment
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "C:\Program Files\nodejs\node.exe" set "PATH=C:\Program Files\nodejs;%APPDATA%\npm;!PATH!"
)
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "C:\Program Files\Git\cmd\git.exe" set "PATH=C:\Program Files\Git\cmd;!PATH!"
)

:: Forward all arguments to PowerShell supervisor
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run-demo.ps1" %*
exit /b %ERRORLEVEL%
