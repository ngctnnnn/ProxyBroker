#!/usr/bin/env python3
"""
Example script demonstrating how to use the ProxyBroker REST API.

Make sure the API service is running before executing this script:
    docker-compose up -d
    # or
    uvicorn api_service:app --host 0.0.0.0 --port 8008
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8008"


def find_proxies_example():
    """Example: Find and check proxies."""
    print("=" * 60)
    print("Example 1: Finding HTTP/HTTPS proxies from US")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/find",
        json={
            "types": ["HTTP", "HTTPS"],
            "countries": ["US"],
            "limit": 5
        },
        timeout=120
    )
    
    if response.status_code == 200:
        proxies = response.json()
        print(f"\nFound {len(proxies)} proxies:\n")
        for i, proxy in enumerate(proxies, 1):
            print(f"{i}. {proxy['host']}:{proxy['port']}")
            print(f"   Types: {', '.join(proxy.get('types', []))}")
            print(f"   Location: {proxy.get('geo', {}).get('country', {}).get('name', 'Unknown')}")
            if proxy.get('avg_resp_time'):
                print(f"   Avg Response Time: {proxy['avg_resp_time']:.2f}s")
            print()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def grab_proxies_example():
    """Example: Grab proxies without checking."""
    print("=" * 60)
    print("Example 2: Grabbing proxies without checking")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/grab",
        json={
            "limit": 10
        },
        timeout=60
    )
    
    if response.status_code == 200:
        proxies = response.json()
        print(f"\nGrabbed {len(proxies)} proxies:\n")
        for i, proxy in enumerate(proxies, 1):
            print(f"{i}. {proxy['host']}:{proxy['port']}")
            if proxy.get('geo', {}).get('country'):
                country = proxy['geo']['country'].get('name', 'Unknown')
                print(f"   Location: {country}")
            print()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def health_check_example():
    """Example: Check API health."""
    print("=" * 60)
    print("Example 3: Health check")
    print("=" * 60)
    
    response = requests.get(f"{API_BASE_URL}/health")
    if response.status_code == 200:
        print(f"\n{json.dumps(response.json(), indent=2)}\n")
    else:
        print(f"Error: {response.status_code}")


def find_socks_proxies_example():
    """Example: Find SOCKS5 proxies."""
    print("=" * 60)
    print("Example 4: Finding SOCKS5 proxies")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/find",
        json={
            "types": ["SOCKS5"],
            "limit": 3
        },
        timeout=120
    )
    
    if response.status_code == 200:
        proxies = response.json()
        print(f"\nFound {len(proxies)} SOCKS5 proxies:\n")
        for i, proxy in enumerate(proxies, 1):
            print(f"{i}. {proxy['host']}:{proxy['port']}")
            print(f"   Types: {', '.join(proxy.get('types', []))}")
            print()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    print("\nProxyBroker API Usage Examples\n")
    print("Make sure the API service is running at http://localhost:8008\n")
    
    try:
        # Health check first
        health_check_example()
        time.sleep(1)
        
        # Find proxies
        find_proxies_example()
        time.sleep(1)
        
        # Grab proxies
        grab_proxies_example()
        time.sleep(1)
        
        # Find SOCKS proxies
        find_socks_proxies_example()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API service.")
        print("   Make sure the service is running:")
        print("   docker-compose up -d")
        print("   or")
        print("   uvicorn api_service:app --host 0.0.0.0 --port 8008")
    except Exception as e:
        print(f"\n❌ Error: {e}")
