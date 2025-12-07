#!/usr/bin/env python3
"""
AITS Print Server - Main Server Application
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import requests as requests_lib  # For making HTTP requests to Odoo

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yaml

from printer_manager import PrinterManager
from job_queue import JobQueue
from auth import require_api_key, init_auth

# Get base directory
BASE_DIR = Path(__file__).parent

# Initialize Flask app
app = Flask(__name__, static_folder=str(BASE_DIR / 'static'))
CORS(app)

# Load configuration
config_path = Path(__file__).parent / 'config.yaml'
if not config_path.exists():
    print("Error: config.yaml not found. Copy config.example.yaml to config.yaml")
    sys.exit(1)

with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

log_file = log_dir / Path(config['logging']['file']).name
log_max_bytes = config['logging'].get('max_bytes', 10485760)  # Default 10MB
log_backup_count = config['logging'].get('backup_count', 5)

# Create rotating file handler
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=log_max_bytes,
    backupCount=log_backup_count
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Create stream handler for console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure root logger
logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    handlers=[file_handler, stream_handler]
)

logger = logging.getLogger(__name__)

# Initialize components
init_auth(config['security']['api_keys'])
printer_manager = PrinterManager(config['printer'])
job_queue = JobQueue(config['printer'])

# Initialize Odoo client (for polling mode)
odoo_client = None
try:
    from odoo_client import OdooClient
    odoo_client = OdooClient(config, printer_manager)
except ImportError:
    logger.warning("Odoo client not available")
except Exception as e:
    logger.warning(f"Failed to initialize Odoo client: {e}")


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


@app.route('/api/odoo/test', methods=['POST'])
@app.route('/api/v1/odoo/test', methods=['POST'])
def test_odoo_connection():
    """Test connection to Odoo instance"""
    data = request.get_json() or {}
    
    # Use provided values or current config
    odoo_url = data.get('url', config.get('odoo', {}).get('url', ''))
    api_key = data.get('api_key', config.get('odoo', {}).get('api_key', ''))
    database = data.get('database', config.get('odoo', {}).get('database', ''))
    
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
        response = requests_lib.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Connection successful',
                'odoo_version': response.json().get('version', 'unknown')
            })
        elif response.status_code == 401:
            return jsonify({
                'success': False,
                'error': 'Authentication failed - check API key'
            }), 401
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Odoo Direct Print module not installed or API endpoint not found'
            }), 404
        else:
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
