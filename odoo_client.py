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
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


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
        
        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
        })
        
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
        while self.running:
            try:
                self._check_and_process_jobs()
            except Exception as e:
                logger.error(f"Error in poll loop: {e}", exc_info=True)
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(int(self.poll_interval)):
                if not self.running:
                    break
                time.sleep(1)
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: dict = None) -> Optional[dict]:
        """Make authenticated request to Odoo"""
        url = f"{self.odoo_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'DATABASE': self.database,
        }
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("Odoo authentication failed - check API key")
                return None
            elif response.status_code == 404:
                logger.debug(f"Endpoint not found: {endpoint}")
                return None
            else:
                logger.warning(f"Odoo request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.warning(f"Cannot connect to Odoo at {self.odoo_url}")
            return None
        except requests.exceptions.Timeout:
            logger.warning("Odoo request timed out")
            return None
        except Exception as e:
            logger.error(f"Odoo request error: {e}")
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
        content_type = job.get('content_type', 'pdf')
        
        logger.info(f"Processing job {job_id} for printer {printer_name}")
        
        try:
            # Mark job as processing
            self._update_job_status(job_id, 'processing')
            
            # Get the document content
            content_url = job.get('content_url')
            if content_url:
                # Download content from URL
                content = self._download_content(content_url)
            else:
                # Content is inline (base64 encoded)
                content_b64 = job.get('content')
                if content_b64:
                    content = base64.b64decode(content_b64)
                else:
                    raise ValueError("No content or content_url in job")
            
            if not content:
                raise ValueError("Failed to get job content")
            
            # Print the document
            success = self._print_document(
                printer_name=printer_name,
                content=content,
                content_type=content_type,
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
            # Save content to temp file if needed
            if content_type == 'pdf':
                suffix = '.pdf'
            elif content_type == 'raw':
                suffix = '.txt'
            else:
                suffix = ''
            
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Use printer manager to print
                result = self.printer_manager.print_file(
                    printer_name=printer_name,
                    file_path=temp_path,
                    options=options
                )
                return result.get('success', False)
            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Print error: {e}")
            return False
    
    def _update_job_status(self, job_id: int, status: str, error_message: str = None):
        """Update job status in Odoo"""
        data = {
            'job_id': job_id,
            'status': status,
        }
        if error_message:
            data['error_message'] = error_message
        
        self._make_request('/api/v1/print/jobs/update', method='POST', data=data)
    
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
