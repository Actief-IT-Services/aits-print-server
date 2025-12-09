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
