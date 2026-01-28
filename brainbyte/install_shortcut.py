import os
import ctypes

def create_shortcut():
    # Path to your main app and icon
    app_path = os.path.join(os.getcwd(), "run_game.bat")
    icon_path = os.path.join(os.getcwd(), "static", "brain.png") #
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    shortcut_path = os.path.join(desktop, "BrainByte.lnk")

    # This creates the command that Windows uses to build a shortcut
    # It requires 'pywin32' to be installed (pip install pywin32)
    try:
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = app_path
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = icon_path
        shortcut.save()
        print(f"Neural Link established. Shortcut created on Desktop.")
    except ImportError:
        print("Error: Please run 'pip install pywin32' first to create shortcuts.")

if __name__ == "__main__":
    create_shortcut()