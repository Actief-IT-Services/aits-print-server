#!/usr/bin/env python3
"""
AITS Print Server - Main Server Application
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import platform
import socket
import traceback

# Early console output for debugging
print("=" * 60)
print("AITS Print Server - server.py loading...")
print(f"Python: {sys.version}")
print(f"Platform: {platform.system()} {platform.release()}")
print(f"Frozen: {getattr(sys, 'frozen', False)}")
print(f"Executable: {sys.executable}")
print("=" * 60)

try:
    import requests as requests_lib  # For making HTTP requests to Odoo
    print("✓ requests imported")
except ImportError as e:
    print(f"✗ Failed to import requests: {e}")
    requests_lib = None

try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    print("✓ Flask imported")
except ImportError as e:
    print(f"✗ Failed to import Flask: {e}")
    raise

try:
    import yaml
    print("✓ yaml imported")
except ImportError as e:
    print(f"✗ Failed to import yaml: {e}")
    raise


def get_data_dir():
    """Get the appropriate data directory for the platform"""
    if platform.system() == 'Windows':
        # Use LOCALAPPDATA on Windows (writable even from Program Files)
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        data_dir = Path(app_data) / 'AITS Print Server'
    else:
        # Use home directory on Linux/Mac
        data_dir = Path.home() / '.aits_print_server'
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_path():
    """Get config file path - check multiple locations"""
    # First check next to the executable/script
    base_dir = Path(__file__).parent
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_dir = Path(sys.executable).parent
    
    config_locations = [
        base_dir / 'config.yaml',
        get_data_dir() / 'config.yaml',
        Path.home() / '.aits_print_server' / 'config.yaml',
    ]
    
    for config_path in config_locations:
        if config_path.exists():
            return config_path
    
    # Return first location for error message
    return config_locations[0]


# Get base directory
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

print(f"Base directory: {BASE_DIR}")

# Get data directory for logs, etc.
DATA_DIR = get_data_dir()
print(f"Data directory: {DATA_DIR}")

# Initialize Flask app
app = Flask(__name__, static_folder=str(BASE_DIR / 'static'))
CORS(app)
print("✓ Flask app initialized")

# Load configuration
config_path = get_config_path()
print(f"Config path: {config_path}")

if not config_path.exists():
    print(f"WARNING: config.yaml not found at {config_path}")
    print(f"Creating default config...")
    # Create a default config instead of exiting
    config = {
        'server': {'host': '0.0.0.0', 'port': 8888, 'debug': False},
        'printer': {'default_printer': None, 'timeout': 30, 'max_file_size': 52428800},
        'security': {'api_keys': ['default-key-change-me']},
        'logging': {'level': 'DEBUG', 'file': 'server.log', 'max_bytes': 10485760, 'backup_count': 5},
        'odoo': {'enabled': False, 'url': '', 'database': '', 'api_key': '', 'poll_interval': 10}
    }
    # Save default config
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"✓ Created default config at {config_path}")
    except Exception as e:
        print(f"Could not save default config: {e}")
else:
    print(f"Loading config from: {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print("✓ Config loaded")

# Setup logging - use DATA_DIR for logs (writable location)
log_dir = DATA_DIR / 'logs'
try:
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"Log directory: {log_dir}")
except PermissionError as e:
    # Fallback to temp directory
    import tempfile
    log_dir = Path(tempfile.gettempdir()) / 'aits_print_server' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"Using fallback log directory: {log_dir}")

log_file = log_dir / Path(config['logging']['file']).name
log_max_bytes = config['logging'].get('max_bytes', 10485760)  # Default 10MB
log_backup_count = config['logging'].get('backup_count', 5)

print(f"Log file: {log_file}")

# Create rotating file handler
try:
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=log_max_bytes,
        backupCount=log_backup_count
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    print("✓ File handler created")
except Exception as e:
    print(f"✗ Failed to create file handler: {e}")
    file_handler = None

# Create stream handler for console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure root logger
handlers = [stream_handler]
if file_handler:
    handlers.append(file_handler)

logging.basicConfig(
    level=getattr(logging, config['logging'].get('level', 'DEBUG')),
    handlers=handlers
)

logger = logging.getLogger(__name__)
logger.info("Logging initialized")

# Import and initialize components with error handling
print("Importing components...")

try:
    from printer_manager import PrinterManager
    print("✓ PrinterManager imported")
except ImportError as e:
    print(f"✗ Failed to import PrinterManager: {e}")
    traceback.print_exc()
    raise

try:
    from job_queue import JobQueue
    print("✓ JobQueue imported")
except ImportError as e:
    print(f"✗ Failed to import JobQueue: {e}")
    traceback.print_exc()
    raise

try:
    from auth import require_api_key, init_auth
    print("✓ auth imported")
except ImportError as e:
    print(f"✗ Failed to import auth: {e}")
    traceback.print_exc()
    raise

# Initialize components
print("Initializing components...")

try:
    init_auth(config['security']['api_keys'])
    print("✓ Auth initialized")
except Exception as e:
    print(f"✗ Failed to initialize auth: {e}")
    traceback.print_exc()

try:
    printer_manager = PrinterManager(config['printer'])
    print("✓ PrinterManager initialized")
except Exception as e:
    print(f"✗ Failed to initialize PrinterManager: {e}")
    traceback.print_exc()
    printer_manager = None

try:
    job_queue = JobQueue(config['printer'])
    print("✓ JobQueue initialized")
except Exception as e:
    print(f"✗ Failed to initialize JobQueue: {e}")
    traceback.print_exc()
    job_queue = None

# Initialize Odoo client (for polling mode)
odoo_client = None
try:
    from odoo_client import OdooClient
    odoo_client = OdooClient(config, printer_manager)
    print("✓ OdooClient initialized")
except ImportError as e:
    print(f"Odoo client not available: {e}")
except Exception as e:
    print(f"Failed to initialize Odoo client: {e}")
    traceback.print_exc()


def initialize_printers_from_config():
    """Initialize printers defined in config.yaml (Linux/CUPS only)"""
    printers_config = config.get('printers', [])
    
    if not printers_config:
        logger.debug("No printers defined in config")
        return
    
    if not printer_manager or not printer_manager.platform.startswith('linux'):
        logger.info("Printer auto-configuration is only supported on Linux with CUPS")
        return
    
    logger.info(f"Initializing {len(printers_config)} printer(s) from config...")
    
    # Get existing printers to avoid duplicates
    existing_printers = {p['name'] for p in printer_manager.get_printers()}
    
    for printer_cfg in printers_config:
        name = printer_cfg.get('name')
        if not name:
            logger.warning("Printer config missing 'name', skipping")
            continue
        
        # Sanitize name
        safe_name = name.replace(' ', '_').replace('/', '_')
        
        if safe_name in existing_printers:
            logger.info(f"Printer '{safe_name}' already exists, skipping")
            continue
        
        uri = printer_cfg.get('uri')
        if not uri:
            logger.warning(f"Printer '{name}' missing 'uri', skipping")
            continue
        
        driver = printer_cfg.get('driver', 'everywhere')
        description = printer_cfg.get('description', '')
        location = printer_cfg.get('location', '')
        is_default = printer_cfg.get('default', False)
        
        try:
            result = printer_manager.add_printer(
                name=safe_name,
                uri=uri,
                driver=driver,
                description=description,
                location=location
            )
            
            if result.get('success'):
                logger.info(f"✓ Added printer '{safe_name}' ({uri})")
                
                # Set as default if requested
                if is_default:
                    try:
                        printer_manager.set_default_printer(safe_name)
                        logger.info(f"  Set '{safe_name}' as default printer")
                    except Exception as e:
                        logger.warning(f"  Could not set as default: {e}")
            else:
                logger.warning(f"✗ Failed to add printer '{safe_name}': {result.get('error')}")
                
        except Exception as e:
            logger.warning(f"✗ Error adding printer '{safe_name}': {e}")


# Initialize printers from config on startup
try:
    initialize_printers_from_config()
    print("✓ Printers initialized from config")
except Exception as e:
    print(f"Warning: Could not initialize printers from config: {e}")
    logger.warning(f"Could not initialize printers from config: {e}")

print("=" * 60)
print("Server module loaded successfully!")
print("=" * 60)


@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API information"""
    return jsonify({
        'name': 'AITS Print Server',
        'version': '19.0.1.0.0',
        'status': 'running',
        'platform': sys.platform,
        'endpoints': {
            'health': '/api/v1/health',
            'printers': '/api/v1/printers',
            'print': '/api/v1/print (POST)',
            'jobs': '/api/v1/jobs',
            'stats': '/api/v1/stats',
            'config': '/config'
        },
        'authentication': 'API Key required (X-API-Key header)',
        'documentation': 'See README.md for full API documentation'
    })


@app.route('/config', methods=['GET'])
def config_page():
    """Serve the configuration page"""
    return send_from_directory(BASE_DIR / 'static', 'config.html')


@app.route('/static/<path:filename>', methods=['GET'])
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(BASE_DIR / 'static', filename)


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    """Serve favicon"""
    return send_from_directory(BASE_DIR / 'static', 'icon.ico')


@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '19.0.1.0.0',
        'platform': sys.platform
    })


@app.route('/printers', methods=['GET'])
@app.route('/api/printers', methods=['GET'])
@app.route('/api/v1/printers', methods=['GET'])
def list_printers():
    """List all available printers - no auth required for web UI"""
    try:
        printers = printer_manager.get_printers()
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


@app.route('/api/printers/<printer_name>', methods=['GET'])
@app.route('/api/v1/printers/<printer_name>', methods=['GET'])
@require_api_key
def get_printer(printer_name):
    """Get details about a specific printer"""
    try:
        printer_info = printer_manager.get_printer_info(printer_name)
        if printer_info:
            return jsonify({
                'success': True,
                'printer': printer_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Printer not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting printer info: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/printers/<printer_name>/options', methods=['GET'])
@app.route('/api/v1/printers/<printer_name>/options', methods=['GET'])
@require_api_key
def get_printer_options(printer_name):
    """Get default options/capabilities for a specific printer"""
    try:
        options = printer_manager.get_printer_options(printer_name)
        return jsonify({
            'success': True,
            'printer_name': printer_name,
            'options': options
        })
    except Exception as e:
        logger.error(f"Error getting printer options: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============== Printer Management Endpoints ==============
# These endpoints allow remote management of printers on the print server

@app.route('/api/v1/printers/discover', methods=['POST'])
@require_api_key
def discover_printers():
    """Discover/refresh available printers on the system"""
    try:
        printers = printer_manager.discover_printers()
        logger.info(f"Discovered {len(printers)} printers")
        return jsonify({
            'success': True,
            'printers': printers,
            'count': len(printers)
        })
    except Exception as e:
        logger.error(f"Error discovering printers: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/printers/add', methods=['POST'])
@require_api_key
def add_printer():
    """Add a new printer to CUPS (Linux only)"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'uri']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        result = printer_manager.add_printer(
            name=data['name'],
            uri=data['uri'],
            driver=data.get('driver', 'everywhere'),  # IPP Everywhere driver
            description=data.get('description', ''),
            location=data.get('location', ''),
            options=data.get('options', {})
        )
        
        if result.get('success'):
            logger.info(f"Added printer: {data['name']}")
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error adding printer: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/printers/<printer_name>/remove', methods=['DELETE'])
@require_api_key
def remove_printer(printer_name):
    """Remove a printer from the system (Linux only)"""
    try:
        result = printer_manager.remove_printer(printer_name)
        
        if result.get('success'):
            logger.info(f"Removed printer: {printer_name}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error removing printer: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/printers/<printer_name>/set-default', methods=['POST'])
@require_api_key
def set_default_printer(printer_name):
    """Set a printer as the default"""
    try:
        result = printer_manager.set_default_printer(printer_name)
        
        if result.get('success'):
            logger.info(f"Set default printer: {printer_name}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error setting default printer: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/printers/<printer_name>/enable', methods=['POST'])
@require_api_key
def enable_printer(printer_name):
    """Enable a printer (accept jobs)"""
    try:
        result = printer_manager.enable_printer(printer_name, enabled=True)
        
        if result.get('success'):
            logger.info(f"Enabled printer: {printer_name}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error enabling printer: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/printers/<printer_name>/disable', methods=['POST'])
@require_api_key
def disable_printer(printer_name):
    """Disable a printer (reject jobs)"""
    try:
        result = printer_manager.enable_printer(printer_name, enabled=False)
        
        if result.get('success'):
            logger.info(f"Disabled printer: {printer_name}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error disabling printer: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/printers/<printer_name>/test', methods=['POST'])
@require_api_key
def test_printer(printer_name):
    """Print a test page to the specified printer"""
    try:
        result = printer_manager.print_test_page(printer_name)
        
        if result.get('success'):
            logger.info(f"Test page sent to printer: {printer_name}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error printing test page: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/system/cups-status', methods=['GET'])
@require_api_key
def get_cups_status():
    """Get CUPS server status (Linux only)"""
    try:
        status = printer_manager.get_cups_status()
        return jsonify({
            'success': True,
            'cups': status
        })
    except Exception as e:
        logger.error(f"Error getting CUPS status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/print', methods=['POST'])
@app.route('/api/v1/print', methods=['POST'])
@require_api_key
def submit_print_job():
    """Submit a new print job"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['printer_name', 'document', 'document_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Submit job
        job_id = job_queue.submit_job(
            printer_name=data['printer_name'],
            document=data['document'],
            document_name=data['document_name'],
            copies=data.get('copies', 1),
            options=data.get('options', {})
        )
        
        logger.info(f"Print job {job_id} submitted for printer {data['printer_name']}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Print job submitted successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error submitting print job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs', methods=['GET'])
@app.route('/api/v1/jobs', methods=['GET'])
@require_api_key
def list_jobs():
    """List print jobs"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        jobs = job_queue.get_jobs(status=status, limit=limit)
        
        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        })
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/<job_id>', methods=['GET'])
@app.route('/api/v1/jobs/<job_id>', methods=['GET'])
@require_api_key
def get_job(job_id):
    """Get details about a specific job"""
    try:
        job = job_queue.get_job(job_id)
        
        if job:
            return jsonify({
                'success': True,
                'job': job
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
@app.route('/api/v1/jobs/<job_id>/cancel', methods=['POST'])
@require_api_key
def cancel_job(job_id):
    """Cancel a print job"""
    try:
        success = job_queue.cancel_job(job_id)
        
        if success:
            logger.info(f"Job {job_id} cancelled")
            return jsonify({
                'success': True,
                'message': 'Job cancelled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Job not found or cannot be cancelled'
            }), 404
            
    except Exception as e:
        logger.error(f"Error cancelling job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
@app.route('/api/v1/stats', methods=['GET'])
@require_api_key
def get_statistics():
    """Get server statistics"""
    try:
        stats = {
            'total_printers': len(printer_manager.get_printers()),
            'jobs': job_queue.get_statistics(),
            'uptime': job_queue.get_uptime()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============== Odoo Connection Endpoints ==============

@app.route('/api/config', methods=['GET'])
@app.route('/api/v1/config', methods=['GET'])
def get_config():
    """Get current configuration (safe subset)"""
    # Check odoo connection only if enabled and configured
    odoo_connected = False
    if odoo_client and odoo_client.enabled and odoo_client.odoo_url:
        try:
            odoo_connected = odoo_client.test_connection().get('success', False)
        except:
            pass
    
    # Return only safe config values, not API keys
    safe_config = {
        'server': {
            'host': config['server']['host'],
            'port': config['server']['port'],
        },
        'odoo': {
            'enabled': config.get('odoo', {}).get('enabled', False),
            'url': config.get('odoo', {}).get('url', ''),
            'database': config.get('odoo', {}).get('database', ''),
            'poll_interval': config.get('odoo', {}).get('poll_interval', 10),
            'server_name': config.get('odoo', {}).get('server_name', ''),
            'connected': odoo_connected,
        },
        'ssl': {
            'enabled': config.get('ssl', {}).get('enabled', False),
        }
    }
    return jsonify(safe_config)


@app.route('/api/debug', methods=['GET'])
@app.route('/api/v1/debug', methods=['GET'])
def get_debug_info():
    """Get debug information including paths and system info"""
    import platform
    
    debug_info = {
        'platform': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'python_version': sys.version,
        },
        'paths': {
            'base_dir': str(BASE_DIR),
            'data_dir': str(DATA_DIR),
            'log_dir': str(log_dir),
            'log_file': str(log_file),
            'config_file': str(config_path),
            'frozen': getattr(sys, 'frozen', False),
            'executable': sys.executable,
        },
        'logs': {
            'exists': log_dir.exists(),
            'writable': os.access(log_dir, os.W_OK) if log_dir.exists() else False,
            'log_file_exists': log_file.exists() if log_file else False,
        }
    }
    
    # Try to get recent log entries
    try:
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                debug_info['recent_logs'] = lines[-50:] if len(lines) > 50 else lines
    except Exception as e:
        debug_info['log_read_error'] = str(e)
    
    return jsonify(debug_info)


@app.route('/api/odoo/test', methods=['POST'])
@app.route('/api/v1/odoo/test', methods=['POST'])
def test_odoo_connection():
    """Test connection to Odoo instance"""
    data = request.get_json() or {}
    
    # Use provided values or current config
    odoo_url = data.get('url', config.get('odoo', {}).get('url', ''))
    api_key = data.get('api_key', config.get('odoo', {}).get('api_key', ''))
    database = data.get('database', config.get('odoo', {}).get('database', ''))
    
    # Extended logging for debugging
    logger.info(f"=== Testing Odoo Connection ===")
    logger.info(f"  URL: {odoo_url}")
    logger.info(f"  Database: {database}")
    logger.info(f"  API Key: {api_key[:8]}..." if api_key else "  API Key: (not set)")
    
    if not odoo_url:
        return jsonify({'success': False, 'error': 'Odoo URL is required'}), 400
    
    try:
        # Test connection
        headers = {
            'Authorization': f'Bearer {api_key}',
            'DATABASE': database,
            'Content-Type': 'application/json',
        }
        
        test_url = f"{odoo_url.rstrip('/')}/api/v1/print/ping"
        logger.info(f"  Full test URL: {test_url}")
        
        response = requests_lib.get(test_url, headers=headers, timeout=10)
        
        # Log response details
        logger.info(f"  Response Status: {response.status_code}")
        logger.info(f"  Response Headers: {dict(response.headers)}")
        content_type = response.headers.get('Content-Type', '')
        logger.info(f"  Content-Type: {content_type}")
        
        # Check if we got HTML instead of JSON
        if 'text/html' in content_type:
            error_msg = 'Received HTML instead of JSON - check URL and ensure aits_direct_print module is installed'
            logger.error(f"  ERROR: {error_msg}")
            logger.error(f"  Response preview: {response.text[:500]}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'debug': {
                    'content_type': content_type,
                    'status_code': response.status_code,
                    'response_preview': response.text[:200]
                }
            }), 400
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                logger.info(f"  JSON Response: {json_data}")
                return jsonify({
                    'success': True,
                    'message': 'Connection successful',
                    'odoo_version': json_data.get('version', 'unknown')
                })
            except Exception as json_err:
                error_msg = f'Failed to parse JSON response: {json_err}'
                logger.error(f"  {error_msg}")
                logger.error(f"  Raw response: {response.text[:500]}")
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'debug': {'raw_response': response.text[:200]}
                }), 400
        elif response.status_code == 401:
            return jsonify({
                'success': False,
                'error': 'Authentication failed - check API key'
            }), 401
        elif response.status_code == 404:
            logger.warning(f"  404 Response: {response.text[:200]}")
            return jsonify({
                'success': False,
                'error': 'Odoo Direct Print module not installed or API endpoint not found'
            }), 404
        else:
            logger.warning(f"  Unexpected response: {response.text[:500]}")
            return jsonify({
                'success': False,
                'error': f'Connection failed with status {response.status_code}'
            }), 400
            
    except requests_lib.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': f'Cannot connect to {odoo_url}'
        }), 400
    except requests_lib.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Connection timed out'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/odoo/save', methods=['POST'])
@app.route('/api/v1/odoo/save', methods=['POST'])
def save_odoo_config():
    """Save Odoo connection configuration"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    try:
        # Load current config
        with open(config_path, 'r') as f:
            current_config = yaml.safe_load(f)
        
        # Update Odoo section - handle both nested and flat formats
        odoo_data = data.get('odoo', data)  # Support { odoo: {...} } or flat {...}
        
        if 'odoo' not in current_config:
            current_config['odoo'] = {}
        
        if 'enabled' in odoo_data:
            current_config['odoo']['enabled'] = odoo_data['enabled']
        if 'url' in odoo_data:
            current_config['odoo']['url'] = odoo_data['url'].rstrip('/')
        if 'api_key' in odoo_data:
            current_config['odoo']['api_key'] = odoo_data['api_key']
        if 'database' in odoo_data:
            current_config['odoo']['database'] = odoo_data['database']
        if 'poll_interval' in odoo_data:
            current_config['odoo']['poll_interval'] = int(odoo_data['poll_interval'])
        if 'server_name' in odoo_data:
            current_config['odoo']['server_name'] = odoo_data['server_name']
        
        # Save config
        with open(config_path, 'w') as f:
            yaml.dump(current_config, f, default_flow_style=False)
        
        # Reload global config
        global config
        config = current_config
        
        # Restart Odoo client if needed
        global odoo_client
        if odoo_client:
            odoo_client.stop()
        odoo_client = OdooClient(config, printer_manager)
        if config.get('odoo', {}).get('enabled'):
            odoo_client.start()
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved and applied'
        })
        
    except Exception as e:
        logger.error(f"Error saving config: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==========================================
# Network Management API (Linux only)
# ==========================================

@app.route('/api/network/status', methods=['GET'])
def get_network_status():
    """Get current network status for all interfaces"""
    if platform.system() != 'Linux':
        return jsonify({
            'success': False,
            'error': 'Network management only available on Linux'
        }), 400
    
    try:
        import subprocess
        
        result = {
            'wifi': {},
            'ethernet': {}
        }
        
        # Get WiFi status
        try:
            # Get current SSID
            ssid_result = subprocess.run(
                ['iwgetid', '-r'],
                capture_output=True, text=True, timeout=5
            )
            result['wifi']['ssid'] = ssid_result.stdout.strip() if ssid_result.returncode == 0 else None
            
            # Get WiFi signal strength
            if result['wifi']['ssid']:
                signal_result = subprocess.run(
                    ['iwconfig', 'wlan0'],
                    capture_output=True, text=True, timeout=5
                )
                if 'Signal level' in signal_result.stdout:
                    import re
                    match = re.search(r'Signal level[=:](-?\d+)', signal_result.stdout)
                    if match:
                        # Convert dBm to percentage (roughly)
                        dbm = int(match.group(1))
                        result['wifi']['signal'] = min(100, max(0, 2 * (dbm + 100)))
            
            # Get WiFi IP
            ip_result = subprocess.run(
                ['ip', '-4', 'addr', 'show', 'wlan0'],
                capture_output=True, text=True, timeout=5
            )
            import re
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
            result['wifi']['ip'] = ip_match.group(1) if ip_match else None
            result['wifi']['connected'] = bool(result['wifi']['ssid'])
            
        except Exception as e:
            logger.debug(f"WiFi status error: {e}")
            result['wifi']['connected'] = False
        
        # Get Ethernet status
        try:
            # Check if eth0 exists and is up
            eth_result = subprocess.run(
                ['ip', 'link', 'show', 'eth0'],
                capture_output=True, text=True, timeout=5
            )
            result['ethernet']['exists'] = eth_result.returncode == 0
            result['ethernet']['connected'] = 'state UP' in eth_result.stdout
            
            # Get Ethernet IP
            ip_result = subprocess.run(
                ['ip', '-4', 'addr', 'show', 'eth0'],
                capture_output=True, text=True, timeout=5
            )
            import re
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', ip_result.stdout)
            if ip_match:
                result['ethernet']['ip'] = ip_match.group(1)
                # Convert CIDR to netmask
                cidr = int(ip_match.group(2))
                netmask = '.'.join([str((0xffffffff << (32 - cidr) >> i) & 0xff) for i in [24, 16, 8, 0]])
                result['ethernet']['netmask'] = netmask
            
            # Get MAC address
            mac_result = subprocess.run(
                ['cat', '/sys/class/net/eth0/address'],
                capture_output=True, text=True, timeout=5
            )
            result['ethernet']['mac'] = mac_result.stdout.strip() if mac_result.returncode == 0 else None
            
            # Get gateway
            gw_result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, timeout=5
            )
            gw_match = re.search(r'via (\d+\.\d+\.\d+\.\d+)', gw_result.stdout)
            result['ethernet']['gateway'] = gw_match.group(1) if gw_match else None
            
            # Get DNS
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    dns_servers = []
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_servers.append(line.split()[1])
                    result['ethernet']['dns'] = dns_servers
            except:
                result['ethernet']['dns'] = []
            
            # Check if using DHCP
            result['ethernet']['dhcp'] = True  # Default assumption
            try:
                dhcp_result = subprocess.run(
                    ['cat', '/etc/dhcpcd.conf'],
                    capture_output=True, text=True, timeout=5
                )
                if 'interface eth0' in dhcp_result.stdout and 'static ip_address' in dhcp_result.stdout:
                    result['ethernet']['dhcp'] = False
            except:
                pass
                
        except Exception as e:
            logger.debug(f"Ethernet status error: {e}")
            result['ethernet']['connected'] = False
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting network status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/network/wifi/scan', methods=['GET'])
def scan_wifi_networks():
    """Scan for available WiFi networks"""
    if platform.system() != 'Linux':
        return jsonify({
            'success': False,
            'error': 'WiFi scanning only available on Linux'
        }), 400
    
    try:
        import subprocess
        
        # Get current SSID
        current_ssid = None
        try:
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=5)
            current_ssid = result.stdout.strip() if result.returncode == 0 else None
        except:
            pass
        
        # Scan for networks using nmcli (if available) or iwlist
        networks = []
        
        # Try nmcli first
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi', 'list', '--rescan', 'yes'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                seen_ssids = set()
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            ssid = parts[0]
                            if ssid and ssid not in seen_ssids:
                                seen_ssids.add(ssid)
                                networks.append({
                                    'ssid': ssid,
                                    'signal': int(parts[1]) if parts[1].isdigit() else 0,
                                    'security': parts[2] if len(parts) > 2 else '',
                                    'connected': ssid == current_ssid
                                })
        except FileNotFoundError:
            # nmcli not available, try iwlist
            result = subprocess.run(
                ['sudo', 'iwlist', 'wlan0', 'scan'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                import re
                current_network = {}
                seen_ssids = set()
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'ESSID:' in line:
                        match = re.search(r'ESSID:"([^"]*)"', line)
                        if match and match.group(1):
                            current_network['ssid'] = match.group(1)
                    elif 'Signal level' in line:
                        match = re.search(r'Signal level[=:](-?\d+)', line)
                        if match:
                            dbm = int(match.group(1))
                            current_network['signal'] = min(100, max(0, 2 * (dbm + 100)))
                    elif 'Encryption key:' in line:
                        current_network['security'] = 'off' not in line.lower()
                    
                    if 'ssid' in current_network and 'signal' in current_network:
                        if current_network['ssid'] not in seen_ssids:
                            seen_ssids.add(current_network['ssid'])
                            networks.append({
                                'ssid': current_network['ssid'],
                                'signal': current_network.get('signal', 0),
                                'security': 'WPA' if current_network.get('security') else '',
                                'connected': current_network['ssid'] == current_ssid
                            })
                        current_network = {}
        
        # Sort by signal strength
        networks.sort(key=lambda x: x['signal'], reverse=True)
        
        return jsonify({
            'success': True,
            'networks': networks
        })
        
    except Exception as e:
        logger.error(f"Error scanning WiFi: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/network/wifi/connect', methods=['POST'])
def connect_wifi():
    """Connect to a WiFi network"""
    if platform.system() != 'Linux':
        return jsonify({
            'success': False,
            'error': 'WiFi management only available on Linux'
        }), 400
    
    try:
        import subprocess
        
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        
        if not ssid:
            return jsonify({
                'success': False,
                'error': 'SSID is required'
            }), 400
        
        # Try nmcli first
        try:
            if password:
                result = subprocess.run(
                    ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password],
                    capture_output=True, text=True, timeout=30
                )
            else:
                result = subprocess.run(
                    ['nmcli', 'dev', 'wifi', 'connect', ssid],
                    capture_output=True, text=True, timeout=30
                )
            
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': f'Connected to {ssid}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.stderr.strip() or 'Failed to connect'
                }), 400
                
        except FileNotFoundError:
            # nmcli not available, try wpa_supplicant
            # Create wpa_supplicant config
            wpa_config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
}}
'''
            config_file = '/etc/wpa_supplicant/wpa_supplicant.conf'
            
            # Check if we can write to the config
            try:
                subprocess.run(['sudo', 'tee', '-a', config_file], 
                             input=wpa_config, capture_output=True, text=True, timeout=10)
                subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'],
                             capture_output=True, text=True, timeout=10)
                return jsonify({
                    'success': True,
                    'message': f'WiFi configuration added for {ssid}'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to configure WiFi: {str(e)}'
                }), 500
        
    except Exception as e:
        logger.error(f"Error connecting to WiFi: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/network/config', methods=['POST'])
def save_network_config():
    """Save network configuration (IP settings)"""
    if platform.system() != 'Linux':
        return jsonify({
            'success': False,
            'error': 'Network configuration only available on Linux'
        }), 400
    
    try:
        import subprocess
        
        data = request.get_json()
        interface = data.get('interface', 'eth0')
        dhcp = data.get('dhcp', True)
        
        if interface not in ['eth0', 'wlan0']:
            return jsonify({
                'success': False,
                'error': 'Invalid interface. Use eth0 or wlan0'
            }), 400
        
        # Use dhcpcd.conf for Raspberry Pi / Debian
        dhcpcd_conf = '/etc/dhcpcd.conf'
        
        try:
            # Read current config
            with open(dhcpcd_conf, 'r') as f:
                lines = f.readlines()
            
            # Remove existing interface config
            new_lines = []
            skip_until_next_interface = False
            for line in lines:
                if line.strip().startswith('interface '):
                    if interface in line:
                        skip_until_next_interface = True
                        continue
                    else:
                        skip_until_next_interface = False
                if skip_until_next_interface and line.strip() and not line.startswith('#'):
                    if line.strip().startswith(('static', 'inform', 'nohook')):
                        continue
                new_lines.append(line)
            
            # Add new config if static
            if not dhcp:
                ip = data.get('ip')
                netmask = data.get('netmask', '255.255.255.0')
                gateway = data.get('gateway')
                dns = data.get('dns', [])
                
                if not ip:
                    return jsonify({
                        'success': False,
                        'error': 'IP address is required for static configuration'
                    }), 400
                
                # Convert netmask to CIDR
                cidr = sum([bin(int(x)).count('1') for x in netmask.split('.')])
                
                new_lines.append(f'\ninterface {interface}\n')
                new_lines.append(f'static ip_address={ip}/{cidr}\n')
                if gateway:
                    new_lines.append(f'static routers={gateway}\n')
                if dns:
                    dns_str = ' '.join(dns) if isinstance(dns, list) else dns
                    new_lines.append(f'static domain_name_servers={dns_str}\n')
            
            # Write config
            config_content = ''.join(new_lines)
            subprocess.run(
                ['sudo', 'tee', dhcpcd_conf],
                input=config_content, capture_output=True, text=True, timeout=10
            )
            
            # Restart networking
            subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'], 
                         capture_output=True, timeout=30)
            
            return jsonify({
                'success': True,
                'message': f'Network configuration for {interface} saved and applied'
            })
            
        except FileNotFoundError:
            # Try netplan for Ubuntu
            return jsonify({
                'success': False,
                'error': 'dhcpcd.conf not found. Network configuration not supported on this system.'
            }), 500
        
    except Exception as e:
        logger.error(f"Error saving network config: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """Get system information including platform"""
    import platform as plat
    return jsonify({
        'success': True,
        'platform': plat.system().lower(),
        'platform_release': plat.release(),
        'platform_version': plat.version(),
        'machine': plat.machine(),
        'hostname': socket.gethostname()
    })


@app.route('/api/network/wifi/saved', methods=['GET'])
def get_saved_networks():
    """Get list of saved WiFi networks"""
    if platform.system() != 'Linux':
        return jsonify({
            'success': False,
            'error': 'WiFi management only available on Linux'
        }), 400
    
    try:
        import subprocess
        
        # Use nmcli to list saved connections
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
            capture_output=True, text=True, timeout=10
        )
        
        networks = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 2 and parts[1] in ['802-11-wireless', 'wifi']:
                        networks.append({
                            'ssid': parts[0],
                            'type': 'wifi'
                        })
        
        return jsonify({
            'success': True,
            'networks': networks
        })
        
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'NetworkManager (nmcli) not installed'
        }), 500
    except Exception as e:
        logger.error(f"Error getting saved networks: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/network/wifi/saved', methods=['POST'])
def add_saved_network():
    """Add a WiFi network to saved connections (pre-configure)"""
    if platform.system() != 'Linux':
        return jsonify({
            'success': False,
            'error': 'WiFi management only available on Linux'
        }), 400
    
    try:
        import subprocess
        
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        security = data.get('security', 'wpa-psk')  # wpa-psk, wpa-eap, or none
        priority = data.get('priority', 0)
        
        if not ssid:
            return jsonify({
                'success': False,
                'error': 'SSID is required'
            }), 400
        
        # Use nmcli to add connection (won't auto-connect until network is in range)
        cmd = ['nmcli', 'connection', 'add', 
               'type', 'wifi',
               'con-name', ssid,
               'ssid', ssid,
               'autoconnect', 'yes',
               'connection.autoconnect-priority', str(priority)]
        
        # Handle security type
        if security == 'wpa-psk' and password:
            cmd.extend(['wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', password])
        elif security == 'wpa-eap':
            # For enterprise networks, just set the key-mgmt; user needs to configure more
            cmd.extend(['wifi-sec.key-mgmt', 'wpa-eap'])
            if password:
                cmd.extend(['wifi-sec.psk', password])
        # For 'none' (open network), no security settings needed
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Network "{ssid}" saved successfully'
            })
        else:
            # Check if connection already exists
            if 'already exists' in result.stderr:
                return jsonify({
                    'success': False,
                    'error': f'Network "{ssid}" already saved'
                }), 400
            return jsonify({
                'success': False,
                'error': result.stderr.strip() or 'Failed to save network'
            }), 400
            
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'NetworkManager (nmcli) not installed'
        }), 500
    except Exception as e:
        logger.error(f"Error adding saved network: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/network/wifi/saved/connect', methods=['POST'])
def connect_saved_network():
    """Connect to a previously saved WiFi network"""
    if platform.system() != 'Linux':
        return jsonify({
            'success': False,
            'error': 'WiFi management only available on Linux'
        }), 400
    
    try:
        import subprocess
        
        data = request.get_json()
        ssid = data.get('ssid')
        
        if not ssid:
            return jsonify({
                'success': False,
                'error': 'SSID is required'
            }), 400
        
        # Use nmcli to activate the connection
        result = subprocess.run(
            ['nmcli', 'connection', 'up', ssid],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Connecting to {ssid}'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr.strip() or 'Failed to connect'
            }), 400
            
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'NetworkManager (nmcli) not installed'
        }), 500
    except Exception as e:
        logger.error(f"Error connecting to saved network: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/network/wifi/saved/<ssid>', methods=['DELETE'])
def delete_saved_network(ssid):
    """Delete a saved WiFi network"""
    if platform.system() != 'Linux':
        return jsonify({
            'success': False,
            'error': 'WiFi management only available on Linux'
        }), 400
    
    try:
        import subprocess
        
        if not ssid:
            return jsonify({
                'success': False,
                'error': 'SSID is required'
            }), 400
        
        # Use nmcli to delete the connection
        result = subprocess.run(
            ['nmcli', 'connection', 'delete', ssid],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Network "{ssid}" deleted'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr.strip() or 'Failed to delete network'
            }), 400
            
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'NetworkManager (nmcli) not installed'
        }), 500
    except Exception as e:
        logger.error(f"Error deleting saved network: {e}", exc_info=True)
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
    
    host = config['server']['host']
    port = config['server']['port']
    
    # Check for SSL configuration
    ssl_config = config.get('ssl', {})
    ssl_enabled = ssl_config.get('enabled', False)
    ssl_context = None
    
    if ssl_enabled:
        cert_file = BASE_DIR / ssl_config.get('cert_file', 'certs/server.crt')
        key_file = BASE_DIR / ssl_config.get('key_file', 'certs/server.key')
        
        if cert_file.exists() and key_file.exists():
            ssl_context = (str(cert_file), str(key_file))
            logger.info(f"SSL enabled - Server will listen on https://{host}:{port}")
        else:
            logger.warning(f"SSL certificate not found at {cert_file}. Run 'python generate_ssl_cert.py' to generate one.")
            logger.info(f"Falling back to HTTP - Server will listen on http://{host}:{port}")
    else:
        logger.info(f"Server will listen on http://{host}:{port}")
    
    # Start job queue processor
    job_queue.start()
    
    # Start Odoo client if enabled
    if odoo_client and config.get('odoo', {}).get('enabled'):
        odoo_client.start()
        logger.info("Odoo polling client started")
    
    try:
        if sys.platform == 'win32':
            # Use waitress on Windows (doesn't support SSL directly)
            from waitress import serve
            if ssl_enabled and ssl_context:
                logger.warning("Waitress doesn't support SSL directly. Consider using a reverse proxy.")
            serve(app, host=host, port=port)
        else:
            # Use Flask's built-in server or gunicorn
            if config['server']['debug']:
                app.run(
                    host=host,
                    port=port,
                    debug=True,
                    ssl_context=ssl_context
                )
            else:
                # For production with SSL
                app.run(
                    host=host,
                    port=port,
                    debug=False,
                    ssl_context=ssl_context
                )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        job_queue.stop()
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        job_queue.stop()
        sys.exit(1)
