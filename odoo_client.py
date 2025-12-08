#!/usr/bin/env python3
"""
Odoo Client - Polls Odoo for print jobs
This allows the print server to work behind NAT/firewall
"""

import requests
import logging
import threading
import time
import base64
import tempfile
import os
import sys
import platform
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Windows SSL certificate fix
def get_ssl_cert_path():
    """Get the SSL certificate bundle path, with Windows fix"""
    if platform.system() == 'Windows':
        # Check if running as PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Try to use certifi if available
            try:
                import certifi
                return certifi.where()
            except ImportError:
                pass
            # Fallback to Windows cert store (by returning True, requests uses Windows certs)
            return True
    return None  # Use default


class OdooClient:
    """Client for polling Odoo for print jobs"""
    
    def __init__(self, config: dict, printer_manager):
        """
        Initialize Odoo client
        
        Args:
            config: Configuration dict with odoo settings
            printer_manager: PrinterManager instance for printing
        """
        self.config = config.get('odoo', {})
        self.printer_manager = printer_manager
        self.enabled = self.config.get('enabled', False)
        self.poll_interval = self.config.get('poll_interval', 10)  # seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Odoo connection settings
        self.odoo_url = self.config.get('url', '').rstrip('/')
        self.database = self.config.get('database', '')
        self.api_key = self.config.get('api_key', '')
        self.server_id = self.config.get('server_id')  # Print server ID in Odoo
        
        # Session with SSL handling for Windows
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
        })
        
        # Configure SSL verification
        ssl_cert = get_ssl_cert_path()
        if ssl_cert is not None:
            self.session.verify = ssl_cert
            logger.debug(f"SSL verification configured: {ssl_cert}")
        
        # Log platform info for debugging
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Frozen (PyInstaller): {getattr(sys, 'frozen', False)}")
        
        if not self.enabled:
            logger.info("Odoo polling disabled in config")
        elif not self.odoo_url or not self.api_key:
            logger.warning("Odoo polling enabled but URL or API key not configured")
            self.enabled = False
    
    def start(self):
        """Start the polling thread"""
        if not self.enabled:
            return
        
        if self.running:
            logger.warning("Odoo client already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info(f"Odoo client started - polling {self.odoo_url} every {self.poll_interval}s")
    
    def stop(self):
        """Stop the polling thread"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("Odoo client stopped")
    
    def _poll_loop(self):
        """Main polling loop"""
        heartbeat_counter = 0
        while self.running:
            try:
                # Send heartbeat every 3rd poll (every 30 seconds at default 10s interval)
                if heartbeat_counter % 3 == 0:
                    self._send_heartbeat()
                heartbeat_counter += 1
                
                self._check_and_process_jobs()
            except Exception as e:
                logger.error(f"Error in poll loop: {e}", exc_info=True)
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(int(self.poll_interval)):
                if not self.running:
                    break
                time.sleep(1)
    
    def _send_heartbeat(self):
        """Send heartbeat to Odoo with printer information"""
        try:
            # Get list of printers from printer manager
            printers = []
            if self.printer_manager:
                printer_list = self.printer_manager.get_printers()
                for p in printer_list:
                    printers.append({
                        'name': p.get('name', ''),
                        'description': p.get('description', p.get('name', '')),
                        'location': p.get('location', ''),
                        'status': p.get('status', 'ready')
                    })
            
            data = {
                'printers': printers,
                'server_name': self.config.get('server_name', 'Print Server')
            }
            
            result = self._make_request('/api/v1/print/server/heartbeat', method='POST', data=data)
            
            if result and result.get('success'):
                logger.debug(f"Heartbeat sent - {len(printers)} printer(s) synced")
            else:
                logger.warning(f"Heartbeat failed: {result}")
                
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: dict = None) -> Optional[dict]:
        """Make authenticated request to Odoo"""
        url = f"{self.odoo_url}{endpoint}"
        
        # Get server name from config
        server_name = self.config.get('server_name', 'Print Server')
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'DATABASE': self.database,
            'X-Server-Name': server_name,
        }
        
        # Extended debug logging
        logger.debug(f"=== Making {method} request ===")
        logger.debug(f"  URL: {url}")
        logger.debug(f"  Database: {self.database}")
        logger.debug(f"  API Key: {self.api_key[:8]}..." if self.api_key else "  API Key: (not set)")
        logger.debug(f"  Server Name: {server_name}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Log response details
            logger.debug(f"  Response Status: {response.status_code}")
            logger.debug(f"  Response Headers: {dict(response.headers)}")
            content_type = response.headers.get('Content-Type', '')
            logger.debug(f"  Content-Type: {content_type}")
            
            # Check if response is HTML instead of JSON
            if 'text/html' in content_type:
                logger.error(f"  ERROR: Received HTML instead of JSON!")
                logger.error(f"  Response preview: {response.text[:500]}...")
                logger.error(f"  This usually means:")
                logger.error(f"    1. The URL is wrong or redirecting to a login page")
                logger.error(f"    2. The aits_direct_print module is not installed in Odoo")
                logger.error(f"    3. There's a proxy/firewall intercepting the request")
                return None
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    logger.debug(f"  JSON Response: {json_response}")
                    return json_response
                except Exception as json_err:
                    logger.error(f"  Failed to parse JSON: {json_err}")
                    logger.error(f"  Raw response: {response.text[:500]}")
                    return None
            elif response.status_code == 401:
                logger.error("Odoo authentication failed - check API key")
                return None
            elif response.status_code == 404:
                logger.warning(f"Endpoint not found: {endpoint}")
                logger.warning(f"  Full URL was: {url}")
                logger.warning(f"  Response: {response.text[:200]}")
                return None
            else:
                logger.warning(f"Odoo request failed: {response.status_code}")
                logger.warning(f"  Response: {response.text[:500]}")
                return None
                
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error connecting to Odoo: {e}")
            logger.error(f"  This may be a certificate issue on Windows")
            logger.error(f"  Try setting verify=False or updating certifi package")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Cannot connect to Odoo at {self.odoo_url}")
            logger.warning(f"  Connection error: {e}")
            return None
        except requests.exceptions.Timeout:
            logger.warning("Odoo request timed out")
            return None
        except Exception as e:
            logger.error(f"Odoo request error: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"  Traceback: {traceback.format_exc()}")
            return None
    
    def _check_and_process_jobs(self):
        """Check for pending jobs and process them"""
        # Get pending jobs for this print server
        params = {}
        if self.server_id:
            params['server_id'] = self.server_id
        
        endpoint = '/api/v1/print/jobs/pending'
        if params:
            endpoint += '?' + '&'.join(f"{k}={v}" for k, v in params.items())
        
        result = self._make_request(endpoint)
        
        if not result:
            return
        
        jobs = result.get('jobs', [])
        if not jobs:
            logger.debug("No pending jobs")
            return
        
        logger.info(f"Found {len(jobs)} pending job(s)")
        
        for job in jobs:
            self._process_job(job)
    
    def _process_job(self, job: dict):
        """Process a single print job"""
        job_id = job.get('id')
        printer_name = job.get('printer_name')
        document_type = job.get('document_type', 'pdf')
        
        # If no printer specified, use system default or first available
        if not printer_name:
            printers = self.printer_manager.get_printers()
            if printers:
                printer_name = printers[0].get('name')
                logger.info(f"No printer specified, using default: {printer_name}")
            else:
                logger.error(f"Job {job_id}: No printer specified and no printers available")
                self._update_job_status(job_id, 'failed', 'No printer available')
                return
        
        logger.info(f"Processing job {job_id} for printer {printer_name}")
        
        try:
            # Mark job as processing (claim it)
            claim_result = self._make_request(f'/api/v1/print/jobs/{job_id}/claim', method='POST')
            if not claim_result or not claim_result.get('success'):
                logger.warning(f"Failed to claim job {job_id}, skipping")
                return
            
            # Get the document content - try various field names
            content_b64 = job.get('document_data') or job.get('content') or job.get('file_data')
            content_url = job.get('content_url') or job.get('document_url')
            
            if content_url:
                # Download content from URL
                content = self._download_content(content_url)
            elif content_b64:
                # Content is inline (base64 encoded)
                content = base64.b64decode(content_b64)
            else:
                raise ValueError("No document data in job")
            
            if not content:
                raise ValueError("Failed to get job content")
            
            # Print the document
            success = self._print_document(
                printer_name=printer_name,
                content=content,
                content_type=document_type,
                options=job.get('options', {})
            )
            
            if success:
                self._update_job_status(job_id, 'completed')
                logger.info(f"Job {job_id} completed successfully")
            else:
                self._update_job_status(job_id, 'failed', 'Print failed')
                logger.error(f"Job {job_id} failed")
                
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
            self._update_job_status(job_id, 'failed', str(e))
    
    def _download_content(self, url: str) -> Optional[bytes]:
        """Download content from URL"""
        try:
            # Add authentication if it's an Odoo URL
            headers = {}
            if url.startswith(self.odoo_url):
                headers['Authorization'] = f'Bearer {self.api_key}'
                headers['DATABASE'] = self.database
            
            response = self.session.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to download content: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading content: {e}")
            return None
    
    def _print_document(self, printer_name: str, content: bytes, 
                        content_type: str, options: dict) -> bool:
        """Print document using printer manager"""
        try:
            # Determine file extension
            if content_type == 'pdf':
                suffix = '.pdf'
            elif content_type in ('raw', 'text'):
                suffix = '.txt'
            else:
                suffix = '.pdf'  # Default to PDF
            
            # Re-encode content to base64 for printer manager
            document_b64 = base64.b64encode(content).decode('utf-8')
            document_name = f"odoo_job{suffix}"
            
            # Extract options
            copies = options.get('copies', 1) if options else 1
            
            # Use printer manager to print
            result = self.printer_manager.print_document(
                printer_name=printer_name,
                document=document_b64,
                document_name=document_name,
                copies=copies,
                options=options
            )
            return result
                    
        except Exception as e:
            logger.error(f"Print error: {e}")
            return False
    
    def _update_job_status(self, job_id: int, status: str, error_message: str = None):
        """Update job status in Odoo"""
        data = {
            'status': status,
        }
        if error_message:
            data['error'] = error_message
        
        result = self._make_request(f'/api/v1/print/jobs/{job_id}/update', method='POST', data=data)
        if result:
            logger.info(f"Job {job_id} status updated to {status}")
        else:
            logger.warning(f"Failed to update job {job_id} status to {status}")
    
    def register_server(self) -> bool:
        """Register this print server with Odoo"""
        if not self.enabled:
            return False
        
        import socket
        hostname = socket.gethostname()
        
        # Get local printers
        printers = []
        try:
            printers = self.printer_manager.get_printers()
        except:
            pass
        
        data = {
            'name': hostname,
            'printers': printers,
            'version': '19.0.1.0.0',
        }
        
        result = self._make_request('/api/v1/print/server/register', method='POST', data=data)
        
        if result and result.get('success'):
            self.server_id = result.get('server_id')
            logger.info(f"Registered with Odoo as server ID {self.server_id}")
            return True
        
        return False
    
    def test_connection(self) -> dict:
        """Test connection to Odoo"""
        result = self._make_request('/api/v1/print/ping')
        
        if result:
            return {
                'success': True,
                'message': 'Connected to Odoo',
                'odoo_version': result.get('version'),
            }
        else:
            return {
                'success': False,
                'message': f'Cannot connect to {self.odoo_url}',
            }
