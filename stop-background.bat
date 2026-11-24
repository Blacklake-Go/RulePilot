@echo off
title Stop RulePilot Background Service
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter 'Name like ''python%''' | Where-Object { $_.CommandLine -like '*rule_pilot.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo RulePilot background service stopped.
timeout /t 2 >nul
