#!/usr/bin/env python3
"""
AITS Print Server - Simplified version with web config
"""

import os
import sys
import base64
import logging
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import yaml

# Conditional imports based on platform
if sys.platform == 'win32':
    import win32print
    import win32api
else:
    try:
        import cups
    except ImportError:
        print("Warning: pycups not installed. Printer discovery will be limited.")
        cups = None

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = Path(__file__).parent / 'config.yaml'


def load_config():
    """Load configuration from YAML file"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    else:
        # Return default configuration
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 8888,
                'debug': False
            },
            'printing': {
                'default_printer': None,
                'temp_dir': '/tmp' if sys.platform != 'win32' else 'C:\\Temp',
                'auto_cleanup': True,
                'max_file_size': 50
            },
            'logging': {
                'level': 'INFO',
                'file': 'server.log',
                'max_size': 10,
                'backup_count': 5
            }
        }


def save_config(config_data):
    """Save configuration to YAML file"""
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)


def get_printers_list():
    """Get list of available printers"""
    printers = []
    
    try:
        if sys.platform == 'win32':
            # Windows printer enumeration
            printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for printer in printer_info:
                printers.append({
                    'name': printer[2],
                    'status': 'Available',
                    'default': printer[2] == win32print.GetDefaultPrinter()
                })
        else:
            # CUPS printer enumeration (Linux/macOS)
            if cups:
                conn = cups.Connection()
                cups_printers = conn.getPrinters()
                default_printer = conn.getDefault()
                
                for name, printer_info in cups_printers.items():
                    printers.append({
                        'name': name,
                        'status': printer_info.get('printer-state-message', 'Available'),
                        'default': name == default_printer
                    })
    except Exception as e:
        logger.error(f"Error getting printers: {e}")
    
    return printers


def print_pdf(printer_name, pdf_data, copies=1):
    """Print PDF to specified printer"""
    try:
        # Decode base64 PDF
        pdf_bytes = base64.b64decode(pdf_data)
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name
        
        try:
            if sys.platform == 'win32':
                # Windows printing
                win32api.ShellExecute(
                    0,
                    'print',
                    tmp_path,
                    f'/d:"{printer_name}"',
                    '.',
                    0
                )
            else:
                # CUPS printing (Linux/macOS)
                if cups:
                    conn = cups.Connection()
                    conn.printFile(
                        printer_name,
                        tmp_path,
                        "Odoo Print Job",
                        {
                            'copies': str(copies)
                        }
                    )
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
        
        return True
    except Exception as e:
        logger.error(f"Error printing: {e}", exc_info=True)
        raise


# Routes

@app.route('/')
def index():
    """Redirect to config page"""
    return send_from_directory(app.static_folder, 'config.html')


@app.route('/config')
def config_page():
    """Configuration web interface"""
    return send_from_directory(app.static_folder, 'config.html')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'platform': sys.platform
    })


@app.route('/printers', methods=['GET'])
def list_printers():
    """List all available printers"""
    try:
        printers = get_printers_list()
        return jsonify({
            'success': True,
            'printers': printers
        })
    except Exception as e:
        logger.error(f"Error listing printers: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/print', methods=['POST'])
def submit_print_job():
    """Submit a print job"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'printer' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: printer'
            }), 400
        
        if 'document' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: document'
            }), 400
        
        # Print the document
        print_pdf(
            printer_name=data['printer'],
            pdf_data=data['document'],
            copies=data.get('copies', 1)
        )
        
        logger.info(f"Print job submitted to printer: {data['printer']}")
        
        return jsonify({
            'success': True,
            'message': 'Print job submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting print job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        config = load_config()
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return jsonify({
            'error': 'Failed to load configuration'
        }), 500


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        new_config = request.get_json()
        save_config(new_config)
        logger.info("Configuration updated")
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully'
        })
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    logger.info("Starting AITS Print Server...")
    logger.info(f"Platform: {sys.platform}")
    
    # Load configuration
    config = load_config()
    
    host = config['server']['host']
    port = config['server']['port']
    debug = config['server']['debug']
    
    logger.info(f"Server will listen on {host}:{port}")
    logger.info(f"Web config interface: http://localhost:{port}/config")
    
    try:
        if sys.platform == 'win32':
            # Use waitress on Windows
            try:
                from waitress import serve
                logger.info("Using Waitress server (Windows)")
                serve(app, host=host, port=port)
            except ImportError:
                logger.warning("Waitress not installed, using Flask development server")
                app.run(host=host, port=port, debug=debug)
        else:
            # Use Flask's built-in server (or gunicorn in production)
            logger.info("Using Flask development server")
            app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
