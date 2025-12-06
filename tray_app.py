#!/usr/bin/env python3
"""
AITS Print Server - System Tray Application
Cross-platform system tray application for the print server
"""

import sys
import os
import threading
import webbrowser
import socket
import tempfile
import logging
from pathlib import Path

# Add pystray to requirements
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Required packages not installed")
    print("Please run: pip install pystray Pillow")
    sys.exit(1)

# Import server components
try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    import yaml
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
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
        self.waitress_server = None
        
        # Get the directory where the script/exe is located
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            self.base_dir = Path(sys.executable).parent
        else:
            # Running as script
            self.base_dir = Path(__file__).parent
        
        # Initialize Flask app
        self._init_flask_app()
    
    def _init_flask_app(self):
        """Initialize the Flask application"""
        self.flask_app = Flask(__name__, static_folder=str(self.base_dir / 'static'))
        CORS(self.flask_app)
        
        # Load configuration
        config_path = self.base_dir / 'config.yaml'
        if not config_path.exists():
            # Create default config if not exists
            self._create_default_config(config_path)
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.server_port = self.config.get('server', {}).get('port', 8888)
        
        # Setup routes
        self._setup_routes()
    
    def _create_default_config(self, config_path):
        """Create a default configuration file"""
        default_config = {
            'server': {
                'host': '0.0.0.0',
                'port': 8888,
                'debug': False
            },
            'printer': {
                'default_printer': None,
                'timeout': 30
            },
            'security': {
                'api_keys': ['default-key-change-me']
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/server.log',
                'max_bytes': 10485760,
                'backup_count': 5
            }
        }
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
    
    def _setup_routes(self):
        """Setup Flask routes"""
        app = self.flask_app
        
        @app.route('/')
        def index():
            return jsonify({
                'name': 'AITS Print Server',
                'version': '19.0.1.0.0',
                'status': 'running'
            })
        
        @app.route('/config')
        def config_page():
            return send_from_directory(self.base_dir / 'static', 'config.html')
        
        @app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory(self.base_dir / 'static', filename)
        
        @app.route('/api/health', methods=['GET'])
        @app.route('/api/v1/health', methods=['GET'])
        def health():
            return jsonify({'status': 'healthy', 'version': '19.0.1.0.0'})
        
        @app.route('/api/printers', methods=['GET'])
        @app.route('/api/v1/printers', methods=['GET'])
        def get_printers():
            try:
                if sys.platform == 'win32':
                    import win32print
                    printers = []
                    for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                        printers.append({
                            'name': p[2],
                            'status': 'ready'
                        })
                    return jsonify({'printers': printers})
                else:
                    import subprocess
                    result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                    printers = []
                    for line in result.stdout.split('\n'):
                        if line.startswith('printer'):
                            name = line.split()[1]
                            printers.append({'name': name, 'status': 'ready'})
                    return jsonify({'printers': printers})
            except Exception as e:
                return jsonify({'printers': [], 'error': str(e)})
        
        @app.route('/api/print', methods=['POST'])
        @app.route('/api/v1/print', methods=['POST'])
        def print_document():
            try:
                data = request.get_json()
                printer_name = data.get('printer')
                content = data.get('content')
                content_type = data.get('content_type', 'raw')
                
                if not printer_name or not content:
                    return jsonify({'success': False, 'error': 'Missing printer or content'}), 400
                
                # Decode content if base64
                import base64
                if content_type == 'pdf' or content_type == 'base64':
                    content = base64.b64decode(content)
                
                if sys.platform == 'win32':
                    import win32print
                    import win32api
                    
                    # For raw printing
                    if content_type == 'raw':
                        hPrinter = win32print.OpenPrinter(printer_name)
                        try:
                            hJob = win32print.StartDocPrinter(hPrinter, 1, ("AITS Print Job", None, "RAW"))
                            win32print.StartPagePrinter(hPrinter)
                            win32print.WritePrinter(hPrinter, content if isinstance(content, bytes) else content.encode())
                            win32print.EndPagePrinter(hPrinter)
                            win32print.EndDocPrinter(hPrinter)
                        finally:
                            win32print.ClosePrinter(hPrinter)
                    else:
                        # For PDF, save to temp file and print
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                            f.write(content)
                            temp_path = f.name
                        win32api.ShellExecute(0, "print", temp_path, f'/d:"{printer_name}"', ".", 0)
                        
                    return jsonify({'success': True, 'message': 'Print job sent'})
                else:
                    import subprocess
                    subprocess.run(['lp', '-d', printer_name], input=content if isinstance(content, bytes) else content.encode())
                    return jsonify({'success': True, 'message': 'Print job sent'})
                    
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
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
        """Start the print server in a thread"""
        if not self.server_running:
            try:
                def run_server():
                    from waitress import serve
                    self.server_running = True
                    serve(self.flask_app, host='0.0.0.0', port=self.server_port, _quiet=True)
                
                self.server_thread = threading.Thread(target=run_server, daemon=True)
                self.server_thread.start()
                print(f"Print server started on port {self.server_port}")
            except Exception as e:
                print(f"Error starting server: {e}")
    
    def stop_server(self):
        """Stop the print server"""
        self.server_running = False
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
        if self.server_running:
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
