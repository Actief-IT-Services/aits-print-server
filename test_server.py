#!/usr/bin/env python3
"""
Test print server connection and printer discovery
"""

import sys
import requests
import argparse

def test_connection(url, api_key):
    """Test connection to print server"""
    headers = {'X-API-Key': api_key}
    
    print("=" * 60)
    print("Testing Print Server Connection")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"API Key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
    print()
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{url}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Server is healthy")
            print(f"   Version: {data.get('version')}")
            print(f"   Platform: {data.get('platform')}")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False
    
    print()
    
    # Test authentication
    print("2. Testing authentication...")
    try:
        response = requests.get(f"{url}/api/printers", headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Authentication successful")
        elif response.status_code == 401:
            print(f"   ✗ Authentication failed: API key required")
            return False
        elif response.status_code == 403:
            print(f"   ✗ Authentication failed: Invalid API key")
            return False
        else:
            print(f"   ✗ Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Request failed: {e}")
        return False
    
    print()
    
    # Test printer discovery
    print("3. Testing printer discovery...")
    try:
        response = requests.get(f"{url}/api/printers", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            printers = data.get('printers', [])
            print(f"   ✓ Found {len(printers)} printer(s)")
            
            if printers:
                print("\n   Available Printers:")
                for printer in printers:
                    print(f"   - {printer['name']}")
                    print(f"     Model: {printer.get('model', 'N/A')}")
                    print(f"     State: {printer.get('state', 'N/A')}")
                    print(f"     Location: {printer.get('location', 'N/A')}")
                    print()
            else:
                print("   ⚠ No printers found")
                print("   Make sure printers are installed on this system")
        else:
            print(f"   ✗ Failed to get printers: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Request failed: {e}")
        return False
    
    print("=" * 60)
    print("✓ All tests passed successfully!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test print server connection')
    parser.add_argument('--url', default='http://localhost:8888',
                       help='Print server URL (default: http://localhost:8888)')
    parser.add_argument('--api-key', required=True,
                       help='API key for authentication')
    
    args = parser.parse_args()
    
    success = test_connection(args.url, args.api_key)
    sys.exit(0 if success else 1)
