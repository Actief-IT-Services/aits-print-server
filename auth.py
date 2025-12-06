"""
Authentication module for API key validation
"""

from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

# Global variable to store valid API keys
VALID_API_KEYS = []


def init_auth(api_keys):
    """Initialize authentication with API keys"""
    global VALID_API_KEYS
    VALID_API_KEYS = api_keys
    logger.info(f"Authentication initialized with {len(api_keys)} API key(s)")


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("Request without API key")
            return jsonify({
                'success': False,
                'error': 'API key required'
            }), 401
        
        if api_key not in VALID_API_KEYS:
            logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
            return jsonify({
                'success': False,
                'error': 'Invalid API key'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
