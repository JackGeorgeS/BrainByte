import os
import sys
import subprocess

def install_and_setup():
    print("--- BrainByte System Initialization ---")
    
    # 1. Install necessary libraries
    # 'Pillow' is needed to convert your image to an icon automatically
    libs = ['pywin32', 'winshell', 'Pillow']
    try:
        print("Checking data packets (libraries)...")
        for lib in libs:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        print("Libraries verified.")
    except Exception as e:
        print(f"CRITICAL ERROR: Could not install libraries. Error: {e}")
        return

    import winshell
    from win32com.client import Dispatch
    from PIL import Image

    # 2. Convert PNG to ICO for perfect Windows display
    png_path = os.path.join(os.getcwd(), "static", "processor.png") #
    ico_path = os.path.join(os.getcwd(), "static", "processor.ico")
    
    try:
        if os.path.exists(png_path):
            img = Image.open(png_path)
            # Save as ICO with multiple standard sizes for Windows
            img.save(ico_path, sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print("Neural Image converted to .ico format.")
        else:
            print(f"WARNING: Icon source not found at {png_path}")
    except Exception as e:
        print(f"Icon conversion failed: {e}")

    # 3. Create the Silent Shortcut
    try:
        desktop = winshell.desktop()
        path = os.path.join(desktop, "BrainByte.lnk")
        
        # Point to the silent launcher
        target = os.path.join(os.getcwd(), "launch.vbs") 
        
        if not os.path.exists(target):
            print(f"ERROR: 'launch.vbs' missing. Create it in the root folder first.")
            return

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.getcwd() #
        
        # Apply the new icon
        if os.path.exists(ico_path):
            shortcut.IconLocation = ico_path
        else:
            shortcut.IconLocation = png_path
            
        shortcut.save()
        print(f"Neural Link established! Shortcut created at: {path}")

    except Exception as e:
        print(f"SHORTCUT FAILED: {e}")

if __name__ == "__main__":
    install_and_setup()