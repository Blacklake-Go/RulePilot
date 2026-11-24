$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "RulePilot.lnk"

$BaseDir = $PSScriptRoot
$TargetScript = Join-Path -Path $BaseDir -ChildPath "start-app-window.bat"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetScript
$Shortcut.WorkingDirectory = $BaseDir
$Shortcut.Description = "RulePilot - Local Routing Rule & Mainland Direct Companion"
$Shortcut.IconLocation = "shell32.dll, 14"
$Shortcut.Save()

Write-Host "Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
