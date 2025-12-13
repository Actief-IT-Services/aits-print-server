"""Cross-platform printer management
Supports CUPS (Linux) and Win32 (Windows)
"""

import os
import sys
import logging
import subprocess
import shlex
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
        self.cups_conn = None
        self.win32print = None
        self.backend_available = False
        
        # Initialize platform-specific backend
        if self.platform.startswith('linux'):
            self._init_cups()
        elif self.platform == 'win32':
            self._init_win32()
        else:
            logger.warning(f"Unsupported platform: {self.platform}, using fallback mode")
    
    def _init_cups(self):
        """Initialize CUPS backend for Linux"""
        try:
            import cups
            self.cups_conn = cups.Connection()
            self.backend_available = True
            logger.info("CUPS backend initialized")
        except ImportError:
            logger.warning("python-cups not installed. Printer features will be limited. Install with: pip install pycups")
            self.backend_available = False
        except Exception as e:
            logger.warning(f"Failed to connect to CUPS: {e}. Printer features will be limited.")
            self.backend_available = False
    
    def _init_win32(self):
        """Initialize Win32 backend for Windows"""
        try:
            import win32print
            self.win32print = win32print
            self.backend_available = True
            logger.info("Win32 print backend initialized")
        except ImportError:
            logger.warning("pywin32 not installed. Printer features will be limited. Install with: pip install pywin32")
            self.backend_available = False
    
    def get_printers(self) -> List[Dict]:
        """Get list of all available printers"""
        if self.backend_available:
            if self.platform.startswith('linux'):
                return self._get_printers_cups()
            elif self.platform == 'win32':
                return self._get_printers_win32()
        
        # Fallback: use command line tools
        logger.info("Using fallback printer detection via command line")
        if self.platform.startswith('linux'):
            return self._get_printers_lpstat()
        elif self.platform == 'win32':
            return self._get_printers_powershell()
        
        logger.warning("No printer detection method available")
        return []
    
    def _get_printers_lpstat(self) -> List[Dict]:
        """Get printers using lpstat command (fallback for Linux without pycups)"""
        printers = []
        try:
            # Get list of printers
            result = subprocess.run(
                ['lpstat', '-p', '-d'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"lpstat failed: {result.stderr}")
                return []
            
            default_printer = None
            
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Parse "printer HP-LaserJet is idle." or similar
                if line.startswith('printer '):
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[1]
                        state = 'ready'
                        if 'disabled' in line.lower():
                            state = 'offline'
                        elif 'idle' in line.lower():
                            state = 'idle'
                        elif 'printing' in line.lower():
                            state = 'printing'
                        
                        printers.append({
                            'name': name,
                            'description': '',
                            'location': '',
                            'model': '',
                            'state': state,
                            'accepting_jobs': 'disabled' not in line.lower(),
                            'is_default': False
                        })
                
                # Parse "system default destination: HP-LaserJet"
                elif line.startswith('system default destination:'):
                    default_printer = line.split(':')[1].strip()
            
            # Mark default printer
            for printer in printers:
                if printer['name'] == default_printer:
                    printer['is_default'] = True
            
            logger.info(f"Found {len(printers)} printer(s) via lpstat")
            return printers
            
        except FileNotFoundError:
            logger.warning("lpstat command not found. Is CUPS installed?")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("lpstat command timed out")
            return []
        except Exception as e:
            logger.error(f"Error running lpstat: {e}")
            return []
    
    def _get_printers_powershell(self) -> List[Dict]:
        """Get printers using PowerShell (fallback for Windows without pywin32)"""
        printers = []
        try:
            # Use PowerShell to get printers
            ps_cmd = 'Get-Printer | Select-Object Name, DriverName, PortName, PrinterStatus, Default | ConvertTo-Json'
            result = subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"PowerShell failed: {result.stderr}")
                return []
            
            import json
            data = json.loads(result.stdout)
            
            # Handle single printer (not a list)
            if isinstance(data, dict):
                data = [data]
            
            for p in data:
                printers.append({
                    'name': p.get('Name', ''),
                    'description': p.get('DriverName', ''),
                    'location': '',
                    'model': p.get('DriverName', ''),
                    'state': 'ready' if p.get('PrinterStatus') == 0 else 'offline',
                    'accepting_jobs': True,
                    'is_default': p.get('Default', False)
                })
            
            logger.info(f"Found {len(printers)} printer(s) via PowerShell")
            return printers
            
        except FileNotFoundError:
            logger.warning("PowerShell not found")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("PowerShell command timed out")
            return []
        except Exception as e:
            logger.error(f"Error running PowerShell: {e}")
            return []
    
    def _get_printers_cups(self) -> List[Dict]:
        """Get printers from CUPS"""
        printers = []
        if not self.cups_conn:
            return printers
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
            # CUPS can accept both 'copies' option or via printFile API
            cups_options = {}
            
            logger.info(f"Printing {copies} copies")
            
            # Add custom options
            if options:
                for key, value in options.items():
                    if isinstance(value, bool):
                        # Convert boolean to CUPS format
                        cups_options[key] = 'true' if value else 'false'
                    else:
                        cups_options[key] = str(value)
            
            logger.info(f"Printing {document_name} to {printer_name} with options: {cups_options}")
            
            # Use CUPS library if available, otherwise fall back to lp command
            if self.cups_conn:
                # Set copies option - CUPS requires string value
                if copies > 1:
                    cups_options['copies'] = str(copies)
                
                # Submit print job via CUPS library
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
            else:
                # Fallback: use lp command
                logger.info(f"Using lp command fallback (pycups not installed)")
                cmd = ['lp', '-d', printer_name]
                
                # Add copies
                if copies > 1:
                    cmd.extend(['-n', str(copies)])
                
                # Add title
                if document_name:
                    cmd.extend(['-t', document_name])
                
                # Add the file to print
                cmd.append(temp_file.name)
                
                logger.info(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info(f"lp command succeeded: {result.stdout.strip()}")
                else:
                    logger.error(f"lp command failed: {result.stderr.strip()}")
                    return False
                
                # Give CUPS time to process
                time.sleep(1)
            
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
        """Print using Win32 - tries multiple methods"""
        try:
            # Decode base64 document
            document_data = base64.b64decode(document)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(document_data)
            temp_file.close()
            temp_path = temp_file.name
            
            logger.info(f"Created temp file: {temp_path} ({len(document_data)} bytes)")
            
            # Try multiple print methods
            success = False
            
            # Method 1: Try using SumatraPDF (common silent PDF printer)
            try:
                import subprocess
                sumatra_paths = [
                    r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                    r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\SumatraPDF\SumatraPDF.exe"),
                ]
                
                sumatra_exe = None
                for path in sumatra_paths:
                    if os.path.exists(path):
                        sumatra_exe = path
                        break
                
                if sumatra_exe:
                    logger.info(f"Using SumatraPDF: {sumatra_exe}")
                    # Build print settings string with copies
                    print_settings = f"{copies}x" if copies > 1 else "noscale"
                    
                    result = subprocess.run([
                        sumatra_exe,
                        "-print-to", printer_name,
                        "-print-settings", print_settings,
                        "-silent",
                        temp_path
                    ], capture_output=True, timeout=60)
                    
                    if result.returncode == 0:
                        success = True
                        logger.info(f"Printed {copies} copies via SumatraPDF to {printer_name}")
                        return True
                    else:
                        logger.warning(f"SumatraPDF returned: {result.returncode}")
            except Exception as e:
                logger.debug(f"SumatraPDF method failed: {e}")
            
            # Method 2: Try using Foxit Reader
            try:
                import subprocess
                foxit_paths = [
                    r"C:\Program Files\Foxit Software\Foxit PDF Reader\FoxitPDFReader.exe",
                    r"C:\Program Files (x86)\Foxit Software\Foxit PDF Reader\FoxitPDFReader.exe",
                    r"C:\Program Files\Foxit Software\Foxit Reader\FoxitReader.exe",
                    r"C:\Program Files (x86)\Foxit Software\Foxit Reader\FoxitReader.exe",
                ]
                
                foxit_exe = None
                for path in foxit_paths:
                    if os.path.exists(path):
                        foxit_exe = path
                        break
                
                if foxit_exe:
                    logger.info(f"Using Foxit Reader: {foxit_exe}")
                    for _ in range(copies):
                        result = subprocess.run([
                            foxit_exe,
                            "/t", temp_path, printer_name
                        ], capture_output=True, timeout=60)
                    
                    success = True
                    logger.info(f"Printed via Foxit Reader to {printer_name}")
                    return True
            except Exception as e:
                logger.debug(f"Foxit Reader method failed: {e}")
            
            # Method 3: Try using Adobe Reader
            try:
                import subprocess
                import time
                adobe_paths = [
                    r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                    r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                    r"C:\Program Files\Adobe\Reader 11.0\Reader\AcroRd32.exe",
                    r"C:\Program Files (x86)\Adobe\Reader 11.0\Reader\AcroRd32.exe",
                    r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
                    r"C:\Program Files (x86)\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
                ]
                
                adobe_exe = None
                for path in adobe_paths:
                    if os.path.exists(path):
                        adobe_exe = path
                        break
                
                if adobe_exe:
                    logger.info(f"Using Adobe Reader: {adobe_exe}")
                    for _ in range(copies):
                        # /t = print to printer and exit, /h = start minimized
                        result = subprocess.run([
                            adobe_exe,
                            "/t", temp_path, printer_name,
                            "/h"
                        ], capture_output=True, timeout=120, shell=False)
                    
                    # Give Adobe some time to spool
                    time.sleep(3)
                    success = True
                    logger.info(f"Printed via Adobe Reader to {printer_name}")
                    return True
            except subprocess.TimeoutExpired:
                logger.warning("Adobe Reader print timed out")
            except Exception as e:
                logger.debug(f"Adobe Reader method failed: {e}")
            
            # Method 4: Try using win32print directly (RAW printing - for PCL/PostScript printers)
            try:
                import win32print
                import win32con
                
                # This sends RAW PDF data - works on printers with PDF support
                hprinter = win32print.OpenPrinter(printer_name)
                try:
                    job_info = win32print.StartDocPrinter(hprinter, 1, (document_name, None, "RAW"))
                    try:
                        win32print.StartPagePrinter(hprinter)
                        for _ in range(copies):
                            win32print.WritePrinter(hprinter, document_data)
                        win32print.EndPagePrinter(hprinter)
                    finally:
                        win32print.EndDocPrinter(hprinter)
                    success = True
                    logger.info(f"Printed via win32print RAW to {printer_name}")
                    return True
                finally:
                    win32print.ClosePrinter(hprinter)
            except Exception as e:
                logger.debug(f"win32print RAW method failed: {e}")
            
            # Method 5: Fallback to ShellExecute (original method)
            try:
                import win32api
                
                logger.info(f"Trying ShellExecute print to {printer_name}")
                win32api.ShellExecute(
                    0,
                    "print",
                    temp_path,
                    f'/d:"{printer_name}"',
                    ".",
                    0
                )
                
                logger.info(f"Win32 ShellExecute print job submitted to {printer_name}")
                return True
                
            except Exception as e:
                logger.error(f"ShellExecute print error: {e}")
            
            # If all methods failed
            if not success:
                logger.error(f"All print methods failed for printer: {printer_name}")
                logger.error("Please install SumatraPDF for reliable PDF printing: https://www.sumatrapdfreader.org/")
                return False
            
            return success
                
        except Exception as e:
            logger.error(f"Win32 print error: {e}", exc_info=True)
            return False
        finally:
            # Schedule temp file cleanup after some time to let spooler finish
            if 'temp_path' in locals():
                try:
                    import threading
                    def cleanup_temp():
                        import time
                        time.sleep(60)  # Wait 60 seconds for print spooler
                        try:
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                                logger.debug(f"Cleaned up temp file: {temp_path}")
                        except Exception:
                            pass
                    threading.Thread(target=cleanup_temp, daemon=True).start()
                except Exception:
                    pass
    
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

    # ============== Printer Management Methods ==============
    # These methods allow remote management of printers

    def discover_printers(self) -> List[Dict]:
        """Discover/refresh available printers - same as get_printers but forces refresh"""
        # Re-initialize the backend to refresh the connection
        if self.platform.startswith('linux'):
            self._init_cups()
        elif self.platform == 'win32':
            self._init_win32()
        
        return self.get_printers()

    def add_printer(self, name: str, uri: str, driver: str = 'everywhere',
                    description: str = '', location: str = '', 
                    options: dict = None) -> Dict:
        """Add a new printer to CUPS (Linux only)
        
        Args:
            name: Printer name (no spaces)
            uri: Device URI (e.g., ipp://192.168.1.100/ipp/print, socket://192.168.1.100:9100)
            driver: PPD driver or 'everywhere' for driverless IPP
            description: Human-readable description
            location: Physical location
            options: Additional CUPS options
        """
        if not self.platform.startswith('linux'):
            return {
                'success': False,
                'error': 'Adding printers is only supported on Linux with CUPS'
            }
        
        try:
            # Sanitize printer name (CUPS doesn't allow spaces)
            safe_name = name.replace(' ', '_').replace('/', '_')
            
            if self.cups_conn:
                # Use CUPS API directly
                import cups
                
                # For IPP Everywhere (driverless) printers
                if driver == 'everywhere' or driver == 'driverless':
                    # Use lpadmin command for driverless printers
                    cmd = [
                        'lpadmin',
                        '-p', safe_name,
                        '-v', uri,
                        '-m', 'everywhere',
                        '-E'  # Enable printer
                    ]
                    if description:
                        cmd.extend(['-D', description])
                    if location:
                        cmd.extend(['-L', location])
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode != 0:
                        return {
                            'success': False,
                            'error': f'lpadmin failed: {result.stderr}'
                        }
                else:
                    # Use specific PPD file
                    self.cups_conn.addPrinter(
                        safe_name,
                        device=uri,
                        ppdname=driver,
                        info=description,
                        location=location
                    )
                    self.cups_conn.enablePrinter(safe_name)
                    self.cups_conn.acceptJobs(safe_name)
                
                logger.info(f"Added printer '{safe_name}' with URI '{uri}'")
                return {
                    'success': True,
                    'printer_name': safe_name,
                    'message': f'Printer {safe_name} added successfully'
                }
            else:
                # Fallback to lpadmin command
                cmd = ['lpadmin', '-p', safe_name, '-v', uri, '-E']
                if driver and driver != 'everywhere':
                    cmd.extend(['-m', driver])
                else:
                    cmd.extend(['-m', 'everywhere'])
                if description:
                    cmd.extend(['-D', description])
                if location:
                    cmd.extend(['-L', location])
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'printer_name': safe_name,
                        'message': f'Printer {safe_name} added successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'lpadmin failed: {result.stderr}'
                    }
                    
        except Exception as e:
            logger.error(f"Error adding printer: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def remove_printer(self, printer_name: str) -> Dict:
        """Remove a printer from the system"""
        if self.platform.startswith('linux'):
            return self._remove_printer_cups(printer_name)
        elif self.platform == 'win32':
            return self._remove_printer_win32(printer_name)
        else:
            return {
                'success': False,
                'error': f'Unsupported platform: {self.platform}'
            }

    def _remove_printer_cups(self, printer_name: str) -> Dict:
        """Remove a printer from CUPS"""
        try:
            if self.cups_conn:
                self.cups_conn.deletePrinter(printer_name)
            else:
                result = subprocess.run(
                    ['lpadmin', '-x', printer_name],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Failed to remove printer: {result.stderr}'
                    }
            
            logger.info(f"Removed printer: {printer_name}")
            return {
                'success': True,
                'message': f'Printer {printer_name} removed successfully'
            }
        except Exception as e:
            logger.error(f"Error removing printer: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _remove_printer_win32(self, printer_name: str) -> Dict:
        """Remove a printer from Windows"""
        try:
            result = subprocess.run(
                ['rundll32', 'printui.dll,PrintUIEntry', '/dl', '/n', printer_name],
                capture_output=True, text=True, timeout=30
            )
            
            # Note: rundll32 may not return error codes properly
            logger.info(f"Attempted to remove printer: {printer_name}")
            return {
                'success': True,
                'message': f'Printer {printer_name} removal initiated'
            }
        except Exception as e:
            logger.error(f"Error removing printer: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def set_default_printer(self, printer_name: str) -> Dict:
        """Set a printer as the default"""
        try:
            if self.platform.startswith('linux'):
                if self.cups_conn:
                    self.cups_conn.setDefault(printer_name)
                else:
                    result = subprocess.run(
                        ['lpoptions', '-d', printer_name],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode != 0:
                        return {
                            'success': False,
                            'error': f'Failed to set default: {result.stderr}'
                        }
            elif self.platform == 'win32':
                result = subprocess.run(
                    ['rundll32', 'printui.dll,PrintUIEntry', '/y', '/n', printer_name],
                    capture_output=True, text=True, timeout=30
                )
            
            logger.info(f"Set default printer: {printer_name}")
            return {
                'success': True,
                'message': f'Default printer set to {printer_name}'
            }
        except Exception as e:
            logger.error(f"Error setting default printer: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def enable_printer(self, printer_name: str, enabled: bool = True) -> Dict:
        """Enable or disable a printer"""
        try:
            if self.platform.startswith('linux'):
                if self.cups_conn:
                    if enabled:
                        self.cups_conn.enablePrinter(printer_name)
                        self.cups_conn.acceptJobs(printer_name)
                    else:
                        self.cups_conn.disablePrinter(printer_name)
                        self.cups_conn.rejectJobs(printer_name)
                else:
                    if enabled:
                        subprocess.run(['cupsenable', printer_name], timeout=30)
                        subprocess.run(['cupsaccept', printer_name], timeout=30)
                    else:
                        subprocess.run(['cupsdisable', printer_name], timeout=30)
                        subprocess.run(['cupsreject', printer_name], timeout=30)
                
                action = 'enabled' if enabled else 'disabled'
                logger.info(f"Printer {printer_name} {action}")
                return {
                    'success': True,
                    'message': f'Printer {printer_name} {action}'
                }
            elif self.platform == 'win32':
                # Windows doesn't have a simple enable/disable
                # Would need to use WMI or modify printer properties
                return {
                    'success': False,
                    'error': 'Enable/disable not supported on Windows via this API'
                }
            else:
                return {
                    'success': False,
                    'error': f'Unsupported platform: {self.platform}'
                }
        except Exception as e:
            logger.error(f"Error enabling/disabling printer: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def print_test_page(self, printer_name: str) -> Dict:
        """Print a test page to the specified printer"""
        try:
            # Create a simple test page
            test_content = f"""
╔══════════════════════════════════════════════════════════════╗
║               AITS PRINT SERVER - TEST PAGE                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Printer: {printer_name:<48} ║
║  Server:  AITS Print Server                                  ║
║  Date:    {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<48} ║
║                                                              ║
║  If you can read this, the printer is working correctly!     ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║             https://www.actief-it.be                         ║
╚══════════════════════════════════════════════════════════════╝
"""
            
            if self.platform.startswith('linux'):
                # Use lp command
                process = subprocess.Popen(
                    ['lp', '-d', printer_name],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate(input=test_content.encode(), timeout=30)
                
                if process.returncode == 0:
                    logger.info(f"Test page sent to {printer_name}")
                    return {
                        'success': True,
                        'message': f'Test page sent to {printer_name}'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to print test page: {stderr.decode()}'
                    }
            elif self.platform == 'win32':
                # Create temp file and print
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(test_content)
                    temp_path = f.name
                
                try:
                    import win32api
                    win32api.ShellExecute(0, "print", temp_path, f'/d:"{printer_name}"', ".", 0)
                    logger.info(f"Test page sent to {printer_name}")
                    return {
                        'success': True,
                        'message': f'Test page sent to {printer_name}'
                    }
                finally:
                    # Schedule cleanup
                    import threading
                    def cleanup():
                        import time
                        time.sleep(30)
                        try:
                            import os
                            os.unlink(temp_path)
                        except:
                            pass
                    threading.Thread(target=cleanup, daemon=True).start()
            else:
                return {
                    'success': False,
                    'error': f'Unsupported platform: {self.platform}'
                }
        except Exception as e:
            logger.error(f"Error printing test page: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_cups_status(self) -> Dict:
        """Get CUPS server status (Linux only)"""
        if not self.platform.startswith('linux'):
            return {
                'available': False,
                'error': 'CUPS is only available on Linux'
            }
        
        try:
            # Check if CUPS service is running
            result = subprocess.run(
                ['systemctl', 'is-active', 'cups'],
                capture_output=True, text=True, timeout=10
            )
            cups_active = result.stdout.strip() == 'active'
            
            # Get CUPS version
            version_result = subprocess.run(
                ['cupsd', '-V'],
                capture_output=True, text=True, timeout=10
            )
            version = version_result.stderr.strip() if version_result.stderr else 'Unknown'
            
            # Count printers
            printers = self.get_printers()
            
            return {
                'available': True,
                'service_running': cups_active,
                'version': version,
                'printer_count': len(printers),
                'backend_connected': self.cups_conn is not None
            }
        except Exception as e:
            logger.error(f"Error getting CUPS status: {e}")
            return {
                'available': False,
                'error': str(e)
            }
