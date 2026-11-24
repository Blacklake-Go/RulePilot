Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
ws.CurrentDirectory = currentDir

userProfile = ws.ExpandEnvironmentStrings("%USERPROFILE%")
pythonw = userProfile & "\AppData\Local\Programs\Python\Python313\pythonw.exe"

If Not fso.FileExists(pythonw) Then
    pythonw = userProfile & "\AppData\Local\Programs\Python\Python312\pythonw.exe"
    If Not fso.FileExists(pythonw) Then
        pythonw = "pythonw.exe"
    End If
End If

cmd = """" & pythonw & """ """ & currentDir & "\rule_pilot.py"" ui"
ws.Run cmd, 0, False
