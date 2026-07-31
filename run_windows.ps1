# StoryLab — Windows launcher
# Usage: .\run_windows.ps1 [travel_tech_ux|fan_atlas_insiders|longitude]

param(
    [string]$Config = "travel_tech_ux"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $Python) {
    Write-Host "Python was not found on PATH. Install Python 3 and try again." -ForegroundColor Red
    exit 1
}
$PythonExe = $Python.Source

Write-Host ""
Write-Host "  StoryLab -- $Config"
Write-Host "  Fetching feeds..."
& $PythonExe "$ScriptDir\core\aggregator.py" --config $Config
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Aggregator exited with an error (code $LASTEXITCODE)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Starting dashboard..."
& $PythonExe "$ScriptDir\core\server.py" --config $Config
