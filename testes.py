import ctypes
from win32 import win32gui
from win32.lib import win32con
import win32com.client

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
 
titles = []
def foreach_window(hwnd, lParam):
    if IsWindowVisible(hwnd):
        length = GetWindowTextLength(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buff, length + 1)
        titles.append(buff.value)
    return True
EnumWindows(EnumWindowsProc(foreach_window), 0)
 
print(titles)

# And SetAsForegroundWindow becomes
def SetAsForegroundWindow(window):
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    win32gui.SetForegroundWindow(window)
    win32gui.ShowWindow(window, win32con.SW_RESTORE)#https://msdn.microsoft.com/pt-br/library/windows/desktop/ms633548(v=vs.85).aspx

name = "(1) WhatsApp - Google Chrome"
window = win32gui.FindWindow(None, name)
if win32gui.IsIconic( window ):# se minimizado entao:
    #win32gui.ShowWindow(window, win32con.SW_MAXIMIZE)
    #SetAsForegroundWindow(window)
    None
    #win32gui.DestroyWindow(window)
    SetAsForegroundWindow(window)
print ( win32gui.IsIconic( window ) )

