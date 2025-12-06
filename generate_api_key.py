#!/usr/bin/env python3
"""
Generate a secure random API key for authentication
"""

import secrets
import string

def generate_api_key(length=32):
    """Generate a cryptographically secure random API key"""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key

if __name__ == '__main__':
    api_key = generate_api_key()
    print("=" * 60)
    print("New API Key Generated")
    print("=" * 60)
    print(f"\nAPI Key: {api_key}")
    print("\nAdd this key to your config.yaml file:")
    print("\nsecurity:")
    print("  api_keys:")
    print(f"    - '{api_key}'")
    print("\nThen configure this API key in Odoo:")
    print("Settings > Technical > Print Servers")
    print("Add a new Print Server with this API key")
    print("=" * 60)
