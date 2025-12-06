#!/usr/bin/env python3
"""
AITS Print Server - System Tray Application
Cross-platform system tray application for the print server
"""

import sys
import os
import subprocess
import threading
import webbrowser
import socket
import tempfile
from pathlib import Path

# Add pystray to requirements
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Required packages not installed")
    print("Please run: pip install pystray Pillow")
    sys.exit(1)

class SingleInstanceChecker:
    """Ensure only one instance of the application runs"""
    
    def __init__(self, app_name="AITS_Print_Server"):
        self.app_name = app_name
        self.lock_file = None
        self.lock_acquired = False
        
        # Create lock file in temp directory
        lock_path = os.path.join(tempfile.gettempdir(), f'{app_name}.lock')
        
        try:
            # Try to create/open lock file
            self.lock_file = open(lock_path, 'w')
            
            # Platform-specific locking
            if sys.platform == 'win32':
                # Windows: Use msvcrt for file locking
                try:
                    import msvcrt
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    self.lock_acquired = True
                except (ImportError, IOError, OSError):
                    # If locking fails, check port instead
                    self.lock_acquired = False
            else:
                # Unix/Linux/macOS: Use fcntl
                try:
                    import fcntl
                    fcntl.lockf(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.lock_acquired = True
                except (ImportError, IOError, OSError):
                    self.lock_acquired = False
                    
        except Exception as e:
            print(f"Lock file error: {e}")
            self.lock_acquired = False
    
    def is_running(self):
        """Check if another instance is already running"""
        return not self.lock_acquired
    
    def release(self):
        """Release the lock"""
        if self.lock_file:
            try:
                if sys.platform != 'win32':
                    import fcntl
                    fcntl.lockf(self.lock_file, fcntl.LOCK_UN)
                self.lock_file.close()
            except:
                pass

def check_port_in_use(port):
    """Check if a port is already in use (indicates server is running)"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True

class PrintServerTray:
    def __init__(self):
        self.server_process = None
        self.icon = None
        self.server_port = 8888
        
        # Get the directory where the script is located
        self.base_dir = Path(__file__).parent
        # Use full server.py with job queue support instead of simple server
        self.server_script = self.base_dir / 'server.py'
        
    def create_image(self):
        """Create icon image"""
        # Create a simple printer icon
        width = 64
        height = 64
        color1 = "white"
        color2 = "blue"
        
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        
        # Draw a simple printer shape
        dc.rectangle((10, 15, 54, 35), fill=color2, outline=color2)
        dc.rectangle((15, 35, 49, 50), fill=color2, outline=color2)
        dc.rectangle((20, 25, 44, 30), fill=color1, outline=color1)
        
        return image
    
    def start_server(self):
        """Start the print server"""
        if self.server_process is None or self.server_process.poll() is not None:
            try:
                python_exe = sys.executable
                self.server_process = subprocess.Popen(
                    [python_exe, str(self.server_script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.base_dir)
                )
                print("Print server started")
            except Exception as e:
                print(f"Error starting server: {e}")
    
    def stop_server(self):
        """Stop the print server"""
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            self.server_process.wait()
            print("Print server stopped")
    
    def restart_server(self, icon, item):
        """Restart the print server"""
        self.stop_server()
        self.start_server()
    
    def open_config(self, icon, item):
        """Open configuration page in browser"""
        webbrowser.open(f'http://localhost:{self.server_port}/config')
    
    def quit_app(self, icon, item):
        """Quit the application"""
        self.stop_server()
        icon.stop()
    
    def get_status_text(self):
        """Get server status text"""
        if self.server_process and self.server_process.poll() is None:
            return "Status: Running"
        return "Status: Stopped"
    
    def setup_menu(self):
        """Create the system tray menu"""
        return Menu(
            MenuItem(
                self.get_status_text(),
                lambda icon, item: None,
                enabled=False
            ),
            Menu.SEPARATOR,
            MenuItem(
                'Open Configuration',
                self.open_config
            ),
            MenuItem(
                'Restart Server',
                self.restart_server
            ),
            Menu.SEPARATOR,
            MenuItem(
                'Quit',
                self.quit_app
            )
        )
    
    def run(self):
        """Run the system tray application"""
        # Start the server
        self.start_server()
        
        # Create and run the system tray icon
        self.icon = Icon(
            "AITS Print Server",
            self.create_image(),
            "AITS Print Server",
            self.setup_menu()
        )
        
        self.icon.run()


def show_message(title, message):
    """Show a message box (cross-platform)"""
    try:
        if sys.platform == 'win32':
            # Windows: Use ctypes for message box
            import ctypes
            MessageBox = ctypes.windll.user32.MessageBoxW
            MessageBox(None, message, title, 0x40 | 0x0)  # MB_ICONINFORMATION | MB_OK
        else:
            # Linux/macOS: Just print (or could use tkinter)
            print(f"\n{title}\n{'-' * len(title)}\n{message}\n")
    except Exception as e:
        # Fallback to print
        print(f"\n{title}\n{message}\n")

if __name__ == '__main__':
    # Check for single instance
    instance_checker = SingleInstanceChecker()
    
    if instance_checker.is_running():
        message = (
            "AITS Print Server is already running!\n\n"
            "Look for the printer icon in your system tray.\n"
            "Right-click the icon to:\n"
            "  • Open Configuration\n"
            "  • Restart Server\n"
            "  • Quit\n\n"
            "If you don't see the icon, check Task Manager."
        )
        show_message("AITS Print Server", message)
        sys.exit(0)
    
    # Also check if port is in use
    if check_port_in_use(8888):
        # Port in use - likely another instance is running
        # Just exit silently since we already checked the lock file
        instance_checker.release()
        sys.exit(0)
    
    try:
        app = PrintServerTray()
        app.run()
    except Exception as e:
        # Log error and show message
        error_msg = f"Failed to start AITS Print Server:\n\n{str(e)}"
        show_message("Error", error_msg)
        raise
    finally:
        # Release the lock when app exits
        instance_checker.release()
