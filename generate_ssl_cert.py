#!/usr/bin/env python3
"""
Generate self-signed SSL certificate for AITS Print Server
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_ssl_cert():
    """Generate self-signed SSL certificate"""
    cert_dir = Path(__file__).parent / 'certs'
    cert_dir.mkdir(exist_ok=True)
    
    key_file = cert_dir / 'server.key'
    cert_file = cert_dir / 'server.crt'
    
    if key_file.exists() and cert_file.exists():
        print(f"Certificate already exists at {cert_dir}")
        response = input("Regenerate? (y/n): ").lower()
        if response != 'y':
            return str(cert_file), str(key_file)
    
    # Generate self-signed certificate using openssl
    print("Generating self-signed SSL certificate...")
    
    # Get hostname for certificate
    import socket
    hostname = socket.gethostname()
    
    # OpenSSL command to generate self-signed cert
    cmd = [
        'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
        '-keyout', str(key_file),
        '-out', str(cert_file),
        '-days', '365',
        '-nodes',  # No password
        '-subj', f'/CN={hostname}/O=AITS Print Server/C=US',
        '-addext', f'subjectAltName=DNS:{hostname},DNS:localhost,IP:127.0.0.1'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ Certificate generated successfully!")
        print(f"  Certificate: {cert_file}")
        print(f"  Private Key: {key_file}")
        print(f"\nTo use HTTPS, update config.yaml:")
        print(f"  ssl:")
        print(f"    enabled: true")
        print(f"    cert_file: certs/server.crt")
        print(f"    key_file: certs/server.key")
        return str(cert_file), str(key_file)
    except subprocess.CalledProcessError as e:
        print(f"Error generating certificate: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: openssl not found. Please install openssl.")
        sys.exit(1)

if __name__ == '__main__':
    generate_ssl_cert()
