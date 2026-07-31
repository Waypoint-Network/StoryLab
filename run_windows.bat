@echo off
REM StoryLab -- Windows one-click launcher
REM Usage: run_windows.bat [travel_tech_ux|fan_atlas_insiders|longitude]

setlocal
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=travel_tech_ux"
set "SCRIPT_DIR=%~dp0"

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY=python"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "PY=py"
    ) else (
        echo Python was not found on PATH. Install Python 3 and try again.
        pause
        exit /b 1
    )
)

echo.
echo   StoryLab -- %CONFIG%
echo   Fetching feeds...
%PY% "%SCRIPT_DIR%core\aggregator.py" --config %CONFIG%

echo.
echo   Starting dashboard...
%PY% "%SCRIPT_DIR%core\server.py" --config %CONFIG%

pause
