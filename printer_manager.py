"""
Cross-platform printer management
Supports CUPS (Linux) and Win32 (Windows)
"""

import sys
import logging
from typing import List, Dict, Optional
import base64
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class PrinterManager:
    """Manages printer discovery and communication"""
    
    def __init__(self, config: dict):
        """Initialize printer manager with configuration"""
        self.config = config
        self.platform = sys.platform
        
        # Initialize platform-specific backend
        if self.platform.startswith('linux'):
            self._init_cups()
        elif self.platform == 'win32':
            self._init_win32()
        else:
            raise RuntimeError(f"Unsupported platform: {self.platform}")
    
    def _init_cups(self):
        """Initialize CUPS backend for Linux"""
        try:
            import cups
            self.cups_conn = cups.Connection()
            logger.info("CUPS backend initialized")
        except ImportError:
            logger.error("python-cups not installed. Install with: pip install pycups")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to CUPS: {e}")
            raise
    
    def _init_win32(self):
        """Initialize Win32 backend for Windows"""
        try:
            import win32print
            self.win32print = win32print
            logger.info("Win32 print backend initialized")
        except ImportError:
            logger.error("pywin32 not installed. Install with: pip install pywin32")
            raise
    
    def get_printers(self) -> List[Dict]:
        """Get list of all available printers"""
        if self.platform.startswith('linux'):
            return self._get_printers_cups()
        elif self.platform == 'win32':
            return self._get_printers_win32()
    
    def _get_printers_cups(self) -> List[Dict]:
        """Get printers from CUPS"""
        printers = []
        try:
            cups_printers = self.cups_conn.getPrinters()
            
            for name, info in cups_printers.items():
                printers.append({
                    'name': name,
                    'description': info.get('printer-info', ''),
                    'location': info.get('printer-location', ''),
                    'model': info.get('printer-make-and-model', ''),
                    'state': self._parse_printer_state_cups(info.get('printer-state', 3)),
                    'accepting_jobs': info.get('printer-is-accepting-jobs', False),
                    'uri': info.get('device-uri', '')
                })
            
            logger.info(f"Found {len(printers)} printer(s) via CUPS")
            return printers
            
        except Exception as e:
            logger.error(f"Error getting CUPS printers: {e}", exc_info=True)
            return []
    
    def _get_printers_win32(self) -> List[Dict]:
        """Get printers from Windows"""
        printers = []
        try:
            # Get default printer
            try:
                default_printer = self.win32print.GetDefaultPrinter()
            except:
                default_printer = None
            
            # Enumerate all printers
            flags = self.win32print.PRINTER_ENUM_LOCAL | self.win32print.PRINTER_ENUM_CONNECTIONS
            printer_list = self.win32print.EnumPrinters(flags)
            
            for printer_info in printer_list:
                name = printer_info[2]
                
                try:
                    # Get detailed printer info
                    handle = self.win32print.OpenPrinter(name)
                    properties = self.win32print.GetPrinter(handle, 2)
                    self.win32print.ClosePrinter(handle)
                    
                    printers.append({
                        'name': name,
                        'description': properties.get('pComment', ''),
                        'location': properties.get('pLocation', ''),
                        'model': properties.get('pDriverName', ''),
                        'state': self._parse_printer_state_win32(properties.get('Status', 0)),
                        'accepting_jobs': properties.get('Status', 0) == 0,
                        'is_default': name == default_printer,
                        'port': properties.get('pPortName', '')
                    })
                except Exception as e:
                    logger.warning(f"Could not get details for printer {name}: {e}")
            
            logger.info(f"Found {len(printers)} printer(s) via Win32")
            return printers
            
        except Exception as e:
            logger.error(f"Error getting Win32 printers: {e}", exc_info=True)
            return []
    
    def get_printer_info(self, printer_name: str) -> Optional[Dict]:
        """Get detailed information about a specific printer"""
        printers = self.get_printers()
        for printer in printers:
            if printer['name'] == printer_name:
                return printer
        return None
    
    def get_printer_options(self, printer_name: str) -> Dict:
        """Get default options/capabilities for a printer"""
        if self.platform.startswith('linux'):
            return self._get_printer_options_cups(printer_name)
        elif self.platform == 'win32':
            return self._get_printer_options_win32(printer_name)
        return {}
    
    def _get_printer_options_cups(self, printer_name: str) -> Dict:
        """Get printer options from CUPS PPD"""
        options = {}
        try:
            import cups
            
            # Get PPD (PostScript Printer Description) file
            ppd_file = self.cups_conn.getPPD(printer_name)
            if ppd_file:
                ppd = cups.PPD(ppd_file)
                
                # Get common options with their defaults
                # Paper size
                option = ppd.findOption('PageSize')
                if option:
                    options['paper_size'] = option.defchoice
                    options['paper_sizes'] = [choice['choice'] for choice in option.choices]
                
                # Duplex
                option = ppd.findOption('Duplex')
                if option:
                    options['duplex'] = option.defchoice
                    options['duplex_options'] = [choice['choice'] for choice in option.choices]
                
                # Color mode
                option = ppd.findOption('ColorModel')
                if option:
                    options['color_mode'] = option.defchoice
                    options['color_modes'] = [choice['choice'] for choice in option.choices]
                
                # Orientation (not always in PPD, might be application-level)
                option = ppd.findOption('Orientation')
                if option:
                    options['orientation'] = option.defchoice
                
                # Resolution
                option = ppd.findOption('Resolution')
                if option:
                    options['resolution'] = option.defchoice
                    options['resolutions'] = [choice['choice'] for choice in option.choices]
                
                # Media type
                option = ppd.findOption('MediaType')
                if option:
                    options['media_type'] = option.defchoice
                    options['media_types'] = [choice['choice'] for choice in option.choices]
                
                # Clean up PPD file
                import os
                try:
                    os.unlink(ppd_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error getting CUPS printer options for {printer_name}: {e}", exc_info=True)
        
        return options
    
    def _get_printer_options_win32(self, printer_name: str) -> Dict:
        """Get printer options from Windows"""
        options = {}
        try:
            handle = self.win32print.OpenPrinter(printer_name)
            properties = self.win32print.GetPrinter(handle, 2)
            
            # Get DEVMODE structure for printer defaults
            # This contains default settings
            devmode = properties.get('pDevMode')
            if devmode:
                # Paper size
                options['paper_size'] = devmode.PaperSize
                
                # Orientation
                if devmode.Orientation == 1:
                    options['orientation'] = 'portrait'
                elif devmode.Orientation == 2:
                    options['orientation'] = 'landscape'
                
                # Duplex
                if devmode.Duplex == 1:
                    options['duplex'] = 'none'
                elif devmode.Duplex == 2:
                    options['duplex'] = 'horizontal'
                elif devmode.Duplex == 3:
                    options['duplex'] = 'vertical'
                
                # Color
                if devmode.Color == 1:
                    options['color'] = False  # Monochrome
                elif devmode.Color == 2:
                    options['color'] = True  # Color
                
                # Copies
                options['copies'] = devmode.Copies
                
                # Print quality
                options['print_quality'] = devmode.PrintQuality
            
            self.win32print.ClosePrinter(handle)
            
        except Exception as e:
            logger.error(f"Error getting Win32 printer options for {printer_name}: {e}", exc_info=True)
        
        return options
    
    def print_document(self, printer_name: str, document: str, document_name: str,
                      copies: int = 1, options: dict = None) -> bool:
        """
        Print a document
        
        Args:
            printer_name: Name of the printer
            document: Base64-encoded document or file path
            document_name: Name of the document
            copies: Number of copies to print
            options: Printer-specific options
        
        Returns:
            True if successful, False otherwise
        """
        if self.platform.startswith('linux'):
            return self._print_cups(printer_name, document, document_name, copies, options)
        elif self.platform == 'win32':
            return self._print_win32(printer_name, document, document_name, copies, options)
    
    def _print_cups(self, printer_name: str, document: str, document_name: str,
                    copies: int, options: dict) -> bool:
        """Print using CUPS"""
        import time
        import os
        
        temp_file = None
        try:
            # Decode base64 document
            document_data = base64.b64decode(document)
            
            # Determine file type from document name
            file_type = 'pdf'  # default
            if document_name:
                if document_name.lower().endswith('.txt'):
                    file_type = 'txt'
                elif document_name.lower().endswith('.pdf'):
                    file_type = 'pdf'
                elif document_name.lower().endswith('.ps'):
                    file_type = 'ps'
                elif document_name.lower().endswith('.pcl'):
                    file_type = 'pcl'
            
            # Convert text to PDF if needed
            if file_type == 'txt':
                logger.info(f"Converting text file to PDF for better printer compatibility")
                document_data = self._convert_text_to_pdf(document_data, document_name)
                file_type = 'pdf'
            
            # Create temporary file
            suffix = f'.{file_type}'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(document_data)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Ensure data is written to disk
            temp_file.close()
            
            logger.info(f"Created temp file {temp_file.name} ({len(document_data)} bytes) for printing")
            
            # Prepare print options
            cups_options = {
                'copies': str(copies)
            }
            
            # Add custom options
            if options:
                for key, value in options.items():
                    if isinstance(value, bool):
                        # Convert boolean to CUPS format
                        cups_options[key] = 'true' if value else 'false'
                    else:
                        cups_options[key] = str(value)
            
            logger.info(f"Printing {document_name} to {printer_name} with options: {cups_options}")
            
            # Submit print job
            job_id = self.cups_conn.printFile(
                printer_name,
                temp_file.name,
                document_name,
                cups_options
            )
            
            logger.info(f"CUPS job {job_id} submitted to {printer_name}")
            
            # Give CUPS time to read the file before we delete it
            time.sleep(1)
            
            # Verify job was accepted
            try:
                jobs = self.cups_conn.getJobs(which_jobs='not-completed')
                if job_id in jobs:
                    logger.info(f"CUPS job {job_id} is in queue: {jobs[job_id]}")
                else:
                    # Job might have already completed or failed
                    jobs_completed = self.cups_conn.getJobs(which_jobs='completed')
                    if job_id in jobs_completed:
                        logger.info(f"CUPS job {job_id} completed immediately")
                    else:
                        logger.warning(f"CUPS job {job_id} not found in queue")
            except Exception as e:
                logger.warning(f"Could not verify job status: {e}")
            
            return True
                        
        except Exception as e:
            logger.error(f"CUPS print error: {e}", exc_info=True)
            return False
        
        finally:
            # Clean up temporary file after delay
            if temp_file:
                try:
                    # Delete after a delay to ensure CUPS has read it
                    time.sleep(0.5)
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                        logger.debug(f"Cleaned up temp file {temp_file.name}")
                except Exception as e:
                    logger.warning(f"Could not delete temp file: {e}")
    
    def _convert_text_to_pdf(self, text_data: bytes, document_name: str = "document") -> bytes:
        """Convert plain text to PDF using reportlab"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            # Create PDF in memory
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Set up text formatting
            c.setFont("Courier", 10)
            
            # Decode text
            try:
                text = text_data.decode('utf-8')
            except:
                text = text_data.decode('latin-1', errors='ignore')
            
            # Split into lines
            lines = text.split('\n')
            
            # Page dimensions
            width, height = A4
            margin = 0.75 * inch
            y = height - margin
            line_height = 12  # points
            
            # Write text to PDF
            for line in lines:
                # Check if we need a new page
                if y < margin:
                    c.showPage()
                    c.setFont("Courier", 10)
                    y = height - margin
                
                # Write line
                c.drawString(margin, y, line)
                y -= line_height
            
            # Save PDF
            c.save()
            
            # Get PDF data
            pdf_data = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Converted text to PDF ({len(pdf_data)} bytes)")
            return pdf_data
            
        except ImportError:
            logger.error("reportlab not installed. Install with: pip install reportlab")
            logger.warning("Falling back to plain text printing (may not work on all printers)")
            return text_data
        except Exception as e:
            logger.error(f"Error converting text to PDF: {e}", exc_info=True)
            return text_data
    
    
    def _print_win32(self, printer_name: str, document: str, document_name: str,
                     copies: int, options: dict) -> bool:
        """Print using Win32"""
        try:
            import win32api
            
            # Create temporary file from base64 data
            temp_file = None
            try:
                # Decode base64 document
                document_data = base64.b64decode(document)
                
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(document_data)
                temp_file.close()
                
                # Print the file
                # Note: This uses the default application for PDF files
                # For more control, you'd need to use win32print.StartDocPrinter
                win32api.ShellExecute(
                    0,
                    "print",
                    temp_file.name,
                    f'/d:"{printer_name}"',
                    ".",
                    0
                )
                
                logger.info(f"Win32 print job submitted to {printer_name}")
                return True
                
            finally:
                # Note: Don't delete immediately on Windows as print spooler may still need it
                # Consider using a cleanup job to delete old temp files
                pass
                
        except Exception as e:
            logger.error(f"Win32 print error: {e}", exc_info=True)
            return False
    
    def _parse_printer_state_cups(self, state: int) -> str:
        """Parse CUPS printer state"""
        states = {
            3: 'idle',
            4: 'printing',
            5: 'stopped'
        }
        return states.get(state, 'unknown')
    
    def _parse_printer_state_win32(self, status: int) -> str:
        """Parse Win32 printer status"""
        if status == 0:
            return 'ready'
        elif status & 0x00000001:
            return 'paused'
        elif status & 0x00000002:
            return 'error'
        elif status & 0x00000004:
            return 'pending_deletion'
        elif status & 0x00000008:
            return 'paper_jam'
        elif status & 0x00000010:
            return 'paper_out'
        elif status & 0x00000020:
            return 'manual_feed'
        elif status & 0x00000040:
            return 'paper_problem'
        elif status & 0x00000080:
            return 'offline'
        elif status & 0x00000200:
            return 'busy'
        elif status & 0x00000400:
            return 'printing'
        else:
            return 'unknown'
