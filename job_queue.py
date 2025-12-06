"""
Print job queue manager with SQLite persistence
"""

import sqlite3
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


class JobQueue:
    """Manages print job queue with retry logic"""
    
    def __init__(self, config: dict):
        """Initialize job queue"""
        self.config = config
        self.db_path = Path(__file__).parent / 'jobs.db'
        self.start_time = datetime.now()
        self.running = False
        self.worker_thread = None
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_jobs (
                job_id TEXT PRIMARY KEY,
                printer_name TEXT NOT NULL,
                document_name TEXT NOT NULL,
                document BLOB NOT NULL,
                copies INTEGER DEFAULT 1,
                options TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON print_jobs(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON print_jobs(created_at)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Job queue database initialized at {self.db_path}")
    
    def submit_job(self, printer_name: str, document: str, document_name: str,
                   copies: int = 1, options: dict = None) -> str:
        """Submit a new print job to the queue"""
        job_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO print_jobs (job_id, printer_name, document_name, document, 
                                       copies, options, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            ''', (
                job_id,
                printer_name,
                document_name,
                document,
                copies,
                json.dumps(options) if options else None
            ))
            
            conn.commit()
            logger.info(f"Job {job_id} submitted to queue")
            return job_id
            
        except Exception as e:
            logger.error(f"Error submitting job: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job details"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT job_id, printer_name, document_name, document, copies, options,
                       status, error_message, retry_count, created_at, 
                       updated_at, completed_at
                FROM print_jobs
                WHERE job_id = ?
            ''', (job_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        finally:
            conn.close()
    
    def get_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get list of jobs, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute('''
                    SELECT job_id, printer_name, document_name, document, copies, options,
                           status, error_message, retry_count, created_at,
                           updated_at, completed_at
                    FROM print_jobs
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (status, limit))
            else:
                cursor.execute('''
                    SELECT job_id, printer_name, document_name, document, copies, options,
                           status, error_message, retry_count, created_at,
                           updated_at, completed_at
                    FROM print_jobs
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def update_job_status(self, job_id: str, status: str, error_message: str = None):
        """Update job status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if status == 'completed':
                cursor.execute('''
                    UPDATE print_jobs
                    SET status = ?, updated_at = CURRENT_TIMESTAMP,
                        completed_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE job_id = ?
                ''', (status, error_message, job_id))
            else:
                cursor.execute('''
                    UPDATE print_jobs
                    SET status = ?, updated_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE job_id = ?
                ''', (status, error_message, job_id))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def increment_retry(self, job_id: str):
        """Increment retry count for a job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE print_jobs
                SET retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            ''', (job_id,))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE print_jobs
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ? AND status IN ('pending', 'failed')
            ''', (job_id,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    def cleanup_old_jobs(self):
        """Clean up old completed/failed/cancelled jobs"""
        retention_days = self.config.get('retention_days', 7)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM print_jobs
                WHERE status IN ('completed', 'failed', 'cancelled')
                AND created_at < ?
            ''', (cutoff_date.isoformat(),))
            
            deleted = cursor.rowcount
            conn.commit()
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old job(s)")
            
        except Exception as e:
            logger.error(f"Error cleaning up jobs: {e}", exc_info=True)
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict:
        """Get job statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Count by status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM print_jobs
                GROUP BY status
            ''')
            
            for row in cursor.fetchall():
                stats[row[0]] = row[1]
            
            # Total jobs
            cursor.execute('SELECT COUNT(*) FROM print_jobs')
            stats['total'] = cursor.fetchone()[0]
            
            return stats
            
        finally:
            conn.close()
    
    def get_uptime(self) -> str:
        """Get server uptime"""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m {seconds}s"
    
    def start(self):
        """Start job queue processor"""
        if self.running:
            logger.warning("Job queue already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.info("Job queue processor started")
    
    def stop(self):
        """Stop job queue processor"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Job queue processor stopped")
    
    def _process_queue(self):
        """Background thread to process pending jobs"""
        from printer_manager import PrinterManager
        
        printer_manager = PrinterManager(self.config)
        max_retries = self.config.get('max_retries', 3)
        
        while self.running:
            try:
                # Get pending jobs
                pending_jobs = self.get_jobs(status='pending', limit=10)
                
                for job in pending_jobs:
                    if not self.running:
                        break
                    
                    job_id = job['job_id']
                    
                    try:
                        # Update status to processing
                        self.update_job_status(job_id, 'processing')
                        
                        # Parse options
                        options = None
                        if job['options']:
                            options = json.loads(job['options'])
                        
                        # Attempt to print
                        success = printer_manager.print_document(
                            printer_name=job['printer_name'],
                            document=job['document'],
                            document_name=job['document_name'],
                            copies=job['copies'],
                            options=options
                        )
                        
                        if success:
                            self.update_job_status(job_id, 'completed')
                            logger.info(f"Job {job_id} completed successfully")
                        else:
                            # Print failed
                            self.increment_retry(job_id)
                            retry_count = job['retry_count'] + 1
                            
                            if retry_count >= max_retries:
                                self.update_job_status(
                                    job_id, 'failed',
                                    f"Failed after {retry_count} attempts"
                                )
                                logger.error(f"Job {job_id} failed after {retry_count} attempts")
                            else:
                                self.update_job_status(
                                    job_id, 'pending',
                                    f"Retry {retry_count}/{max_retries}"
                                )
                                logger.warning(f"Job {job_id} failed, will retry ({retry_count}/{max_retries})")
                                
                    except Exception as e:
                        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
                        self.update_job_status(job_id, 'failed', str(e))
                
                # Cleanup old jobs periodically
                self.cleanup_old_jobs()
                
                # Sleep before next iteration
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in job queue processor: {e}", exc_info=True)
                time.sleep(5)
