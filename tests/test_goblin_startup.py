#!/usr/bin/env python3
"""Test Goblin Dev Server startup and endpoints"""

import subprocess
import time
import requests
import sys


def test_goblin():
    """Start Goblin and test endpoints"""
    print("🧌 Testing Goblin Dev Server")
    print("=" * 50)

    # Start Goblin server in background
    print("\n1. Starting Goblin server...")
    proc = subprocess.Popen(
        ["python", "dev/goblin/goblin_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give it time to start
    time.sleep(2)

    try:
        # Test root endpoint (should return HTML)
        print("\n2. Testing dashboard endpoint (GET /)")
        resp = requests.get("http://127.0.0.1:8767/", timeout=5)
        print(f"   Status: {resp.status_code}")

        if "<html" in resp.text.lower():
            print("   ✓ Returns HTML dashboard (Svelte)")
            if "Goblin" in resp.text and "Experimental" in resp.text:
                print("   ✓ Contains expected dashboard content")
            else:
                print("   ⚠ Missing expected content")
        else:
            print("   ✗ Response is not HTML")
            return False

        # Test API info endpoint
        print("\n3. Testing API info endpoint (GET /api/v0/info)")
        resp = requests.get("http://127.0.0.1:8767/api/v0/info", timeout=5)
        print(f"   Status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✓ Server: {data.get('server')}")
            print(f"   ✓ Version: {data.get('version')}")
            print(f"   ✓ Status: {data.get('status')}")
            print(f"   ✓ Port: {data.get('port')}")
        else:
            print("   ✗ API endpoint failed")
            return False

        print("\n" + "=" * 50)
        print("✅ Goblin Dev Server is working!")
        print("=" * 50)
        return True

    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to Goblin server on port 8767")
        print("  Check if port is already in use or server failed to start")
        return False
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False
    finally:
        # Kill the server
        print("\n4. Cleaning up...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
            print("   ✓ Server stopped cleanly")
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            print("   ✓ Server killed")


if __name__ == "__main__":
    success = test_goblin()
    sys.exit(0 if success else 1)
