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

    all_passed = True

    # Test /health endpoint
    try:
        print("\n📡 Testing /health endpoint...")
        response = urlopen("http://127.0.0.1:8001/health", timeout=5)
        data = json.loads(response.read().decode('utf-8'))

        print(f"✅ Health check successful!")
        print(f"   Status: {data.get('status')}")
        print(f"   Service: {data.get('service')}")
        print(f"   Message: {data.get('message')}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        all_passed = False

    # Test /api/tools endpoint
    try:
        print("\n📡 Testing /api/tools endpoint...")
        response = urlopen("http://127.0.0.1:8001/api/tools", timeout=5)
        data = json.loads(response.read().decode('utf-8'))

        print(f"✅ Tools endpoint successful!")
        print(f"   Returned {len(data)} tools (empty is OK for now)")
    except Exception as e:
        print(f"❌ Tools endpoint failed: {e}")
        all_passed = False

    # Test /api/jobs endpoint
    try:
        print("\n📡 Testing /api/jobs endpoint...")
        response = urlopen("http://127.0.0.1:8001/api/jobs", timeout=5)
        data = json.loads(response.read().decode('utf-8'))

        print(f"✅ Jobs endpoint successful!")
        print(f"   Returned {len(data)} jobs (empty is OK for now)")
    except Exception as e:
        print(f"❌ Jobs endpoint failed: {e}")
        all_passed = False

    # Test /api/run endpoint (POST)
    try:
        from urllib.request import Request
        print("\n📡 Testing /api/run endpoint (POST)...")

        request_data = json.dumps({'tool_name': 'test_tool', 'parameters': {}}).encode('utf-8')
        req = Request(
            "http://127.0.0.1:8001/api/run",
            data=request_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urlopen(req, timeout=5)
        data = json.loads(response.read().decode('utf-8'))

        print(f"✅ Run endpoint successful!")
        print(f"   Job ID: {data.get('job_id')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
    except Exception as e:
        print(f"❌ Run endpoint failed: {e}")
        all_passed = False

    return all_passed

if __name__ == "__main__":
    success = test_backend()

    if success:
        print("\n✅ All tests passed! HTTP server is working correctly.")
        print("   The /health endpoint responds with proper JSON.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! HTTP server is not working.")
        sys.exit(1)
