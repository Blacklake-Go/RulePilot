@echo off
cd /d "%~dp0"
title RulePilot v3.2.0 - Public Edition
set NO_PROXY=localhost,127.0.0.1,::1,192.168.*,10.*,172.16.*
set no_proxy=%NO_PROXY%
python rule_pilot.py ui
if errorlevel 1 pause
