# RulePilot Launcher (PowerShell)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$env:NO_PROXY = "localhost,127.0.0.1,::1,192.168.*,10.*,172.16.*"
$env:no_proxy = $env:NO_PROXY

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Launching RulePilot v3.2.0 Local Routing Rule Console" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python 3 not found. Please install Python 3 first." -ForegroundColor Red
    pause
    exit 1
}

python rule_pilot.py ui
