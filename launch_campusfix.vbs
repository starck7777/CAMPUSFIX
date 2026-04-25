Set shell = CreateObject("WScript.Shell")
projectPath = "C:\Users\bhupe\OneDrive\Desktop\campusfix"
pythonwPath = projectPath & "\.venv\Scripts\pythonw.exe"
launcherPath = projectPath & "\launch_campusfix.pyw"

shell.CurrentDirectory = projectPath
shell.Run """" & pythonwPath & """ """ & launcherPath & """", 0, False
