#!/usr/bin/env python3
"""
AITS Print Server - System Tray Application
Cross-platform system tray application that runs the full print server
"""

import sys
import os
import threading
import webbrowser
import socket
import tempfile
import logging

# Setup basic logging first
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports when running as script
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
        self.server_thread = None
        self.server_running = False
        self.icon = None
        self.server_port = 8888
        self.flask_app = None
        
        # Get the directory where the script/exe is located
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            self.base_dir = Path(sys.executable).parent
        else:
            # Running as script
            self.base_dir = Path(__file__).parent
        
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"Frozen (PyInstaller): {getattr(sys, 'frozen', False)}")
        
        # Load configuration to get port
        self._load_config()
        
    def _load_config(self):
        """Load configuration from config.yaml"""
        import yaml
        
        config_path = self.base_dir / 'config.yaml'
        logger.info(f"Looking for config at: {config_path}")
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                self.server_port = config.get('server', {}).get('port', 8888)
                logger.info(f"Loaded config, port: {self.server_port}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        else:
            logger.warning(f"Config file not found at {config_path}")
    
    def create_image(self):
        """Create icon image"""
        # Try to load icon from file first
        icon_path = self.base_dir / 'static' / 'icon.ico'
        if icon_path.exists():
            try:
                return Image.open(icon_path)
            except:
                pass
        
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
        """Start the FULL print server (server.py) in a thread"""
        if self.server_running:
            logger.info("Server already running")
            return
            
        try:
            def run_server():
                try:
                    logger.info("Starting full server from server.py...")
                    
                    # Import the full server module
                    # This will set up logging, load config, etc.
                    import server
                    
                    # Get the Flask app and config from server module
                    self.flask_app = server.app
                    
                    # Start Odoo client if available
                    if hasattr(server, 'odoo_client') and server.odoo_client:
                        logger.info("Starting Odoo client...")
                        server.odoo_client.start()
                    
                    # Run with waitress
                    from waitress import serve
                    self.server_running = True
                    
                    host = server.config.get('server', {}).get('host', '0.0.0.0')
                    port = server.config.get('server', {}).get('port', 8888)
                    self.server_port = port
                    
                    logger.info(f"Starting waitress server on {host}:{port}")
                    serve(self.flask_app, host=host, port=port, _quiet=False)
                    
                except Exception as e:
                    logger.error(f"Server error: {e}", exc_info=True)
                    self.server_running = False
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Wait a moment and check if server started
            import time
            time.sleep(2)
            
            if self.server_thread.is_alive():
                logger.info(f"Print server started on port {self.server_port}")
            else:
                logger.error("Server thread died unexpectedly")
                
        except Exception as e:
            logger.error(f"Error starting server: {e}", exc_info=True)
    
    def stop_server(self):
        """Stop the print server"""
        self.server_running = False
        logger.info("Print server stopped")
    
    def restart_server(self, icon, item):
        """Restart the print server"""
        logger.info("Restarting server...")
        self.stop_server()
        import time
        time.sleep(1)
        self.start_server()
    
    def open_config(self, icon, item):
        """Open configuration page in browser"""
        url = f'http://localhost:{self.server_port}/config'
        logger.info(f"Opening config: {url}")
        webbrowser.open(url)
    
    def open_logs(self, icon, item):
        """Open logs folder"""
        import platform
        import subprocess
        
        if platform.system() == 'Windows':
            log_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'AITS Print Server' / 'logs'
        else:
            log_dir = Path.home() / '.aits_print_server' / 'logs'
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Opening logs folder: {log_dir}")
        
        if platform.system() == 'Windows':
            os.startfile(str(log_dir))
        elif platform.system() == 'Darwin':
            subprocess.run(['open', str(log_dir)])
        else:
            subprocess.run(['xdg-open', str(log_dir)])
    
    def quit_app(self, icon, item):
        """Quit the application"""
        logger.info("Quitting application...")
        self.stop_server()
        icon.stop()
    
    def get_status_text(self):
        """Get server status text"""
        if self.server_running:
            return f"✓ Running on port {self.server_port}"
        return "✗ Stopped"
    
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
                'Open Logs Folder',
                self.open_logs
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
        logger.info("Starting AITS Print Server tray application...")
        
        # Start the server
        self.start_server()
        
        # Create and run the system tray icon
        self.icon = Icon(
            "AITS Print Server",
            self.create_image(),
            "AITS Print Server",
            self.setup_menu()
        )
        
        logger.info("Running system tray icon...")
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
    print("=" * 60)
    print("AITS Print Server Starting...")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Frozen: {getattr(sys, 'frozen', False)}")
    print(f"Executable: {sys.executable}")
    print("=" * 60)
    
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
        print("Port 8888 already in use - server may already be running")
        instance_checker.release()
        
        # Open browser to existing server
        webbrowser.open('http://localhost:8888/config')
        sys.exit(0)
    
    try:
        app = PrintServerTray()
        app.run()
    except Exception as e:
        # Log error and show message
        import traceback
        error_msg = f"Failed to start AITS Print Server:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        show_message("Error", error_msg)
        raise
    finally:
        # Release the lock when app exits
        instance_checker.release()
