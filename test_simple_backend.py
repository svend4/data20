#!/usr/bin/env python3
"""
Quick test script for backend_main_simple.py
Tests that HTTP server starts and /health endpoint responds
"""

import sys
import time
import json
from urllib.request import urlopen
from urllib.error import URLError
from threading import Thread

# Add path to import the module
sys.path.insert(0, '/home/user/data20/mobile-app-versions/v5-full/android/app/src/main/python')

import backend_main_simple
import tempfile
import os

def test_backend():
    print("🧪 Testing simple backend HTTP server...")

    # Setup environment
    temp_dir = tempfile.gettempdir()
    backend_main_simple.setup_environment(
        db_path=os.path.join(temp_dir, "test_data20.db"),
        upload_dir=os.path.join(temp_dir, "data20_uploads"),
        logs_dir=os.path.join(temp_dir, "data20_logs")
    )

    # Start server in background thread
    print("🚀 Starting HTTP server in background thread...")
    server_thread = Thread(target=backend_main_simple.run_server, args=("127.0.0.1", 8001), daemon=True)
    server_thread.start()

    # Wait for server to start
    print("⏳ Waiting 2 seconds for server to start...")
    time.sleep(2)

    # Test /health endpoint
    try:
        print("📡 Testing /health endpoint...")
        response = urlopen("http://127.0.0.1:8001/health", timeout=5)
        data = json.loads(response.read().decode('utf-8'))

        print(f"✅ Health check successful!")
        print(f"   Status: {data.get('status')}")
        print(f"   Service: {data.get('service')}")
        print(f"   Message: {data.get('message')}")

        return True
    except URLError as e:
        print(f"❌ Health check failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_backend()

    if success:
        print("\n✅ All tests passed! HTTP server is working correctly.")
        print("   The /health endpoint responds with proper JSON.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! HTTP server is not working.")
        sys.exit(1)
