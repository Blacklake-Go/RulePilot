@echo off
cd /d "%~dp0"
title RulePilot v3.2.0 - Companion Window
set NO_PROXY=localhost,127.0.0.1,::1,192.168.*,10.*,172.16.*
set no_proxy=%NO_PROXY%
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3 not found. Please install Python 3 from https://www.python.org/downloads/ and check "Add Python to PATH".
    pause
    exit /b 1
)
python rule_pilot.py ui --app
if errorlevel 1 pause
