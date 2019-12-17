'Iniciar PhraseExpress
Set WshShell = WScript.CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\SisJJ\PhraseExpress"
WshShell.Run("C:\SisJJ\PhraseExpress\PhraseExpress.exe -portable"),10, False
'
'https://superuser.com/a/62646
'CreateObject("Wscript.Shell").Run """" & WScript.Arguments(0) & """", 0, False
'https://stackoverflow.com/a/13580663
'CreateObject("Wscript.Shell").Run """" & WScript.Arguments(0) & """", 0, False
Set objShell = WScript.CreateObject("WScript.Shell")
objShell.CurrentDirectory = "C:\SisJJ\whats-automation"
objShell.Run("python.exe start.py"), 0, True
