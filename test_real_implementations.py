#!/usr/bin/env python3
"""
Test real tool implementations
Tests that tools return real calculations instead of mock data
"""

import sys
import time
import json
from urllib.request import urlopen, Request
from threading import Thread

# Add path to import the module
sys.path.insert(0, '/home/user/data20/mobile-app-versions/v5-full/android/app/src/main/python')

import backend_main_simple
import tempfile
import os

def test_real_implementations():
    print("🧪 Testing real tool implementations...\n")

    # Setup environment
    temp_dir = tempfile.gettempdir()
    backend_main_simple.setup_environment(
        db_path=os.path.join(temp_dir, "test_data20.db"),
        upload_dir=os.path.join(temp_dir, "data20_uploads"),
        logs_dir=os.path.join(temp_dir, "data20_logs")
    )

    # Start server in background thread
    print("🚀 Starting HTTP server in background thread...")
    server_thread = Thread(target=backend_main_simple.run_server, args=("127.0.0.1", 8005), daemon=True)
    server_thread.start()

    # Wait for server to start
    print("⏳ Waiting 2 seconds for server to start...\n")
    time.sleep(2)

    all_passed = True

    # Test 1: calculate_statistics
    try:
        print("=" * 60)
        print("Test 1: calculate_statistics")
        print("=" * 60)

        test_data = {
            'tool_name': 'calculate_statistics',
            'parameters': {
                'data': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'metrics': ['mean', 'median', 'std', 'min', 'max']
            }
        }

        request_data = json.dumps(test_data).encode('utf-8')
        req = Request(
            "http://127.0.0.1:8005/api/run",
            data=request_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read().decode('utf-8'))

        print(f"✅ Status: {result['status']}")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Message: {result['message']}")
        print(f"   Result: {json.dumps(result['result'], indent=2)}")

        # Verify it's real calculation (mean should be 5.5)
        if 'mean' in result['result'] and abs(result['result']['mean'] - 5.5) < 0.01:
            print("   ✅ Real calculation verified (mean = 5.5)")
        else:
            print("   ❌ Calculation incorrect!")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 2: text_analysis
    try:
        print("\n" + "=" * 60)
        print("Test 2: text_analysis")
        print("=" * 60)

        test_data = {
            'tool_name': 'text_analysis',
            'parameters': {
                'text': 'Hello world hello Python hello coding world',
                'language': 'en'
            }
        }

        request_data = json.dumps(test_data).encode('utf-8')
        req = Request(
            "http://127.0.0.1:8005/api/run",
            data=request_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read().decode('utf-8'))

        print(f"✅ Status: {result['status']}")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Message: {result['message']}")
        print(f"   Result: {json.dumps(result['result'], indent=2)}")

        # Verify it's real calculation (should have 7 total words)
        if result['result'].get('total_words') == 7:
            print("   ✅ Real calculation verified (7 words)")
        else:
            print(f"   ❌ Expected 7 words, got {result['result'].get('total_words')}")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 3: word_frequency
    try:
        print("\n" + "=" * 60)
        print("Test 3: word_frequency")
        print("=" * 60)

        test_data = {
            'tool_name': 'word_frequency',
            'parameters': {
                'text': 'apple banana apple cherry apple banana',
                'top_n': 5
            }
        }

        request_data = json.dumps(test_data).encode('utf-8')
        req = Request(
            "http://127.0.0.1:8005/api/run",
            data=request_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read().decode('utf-8'))

        print(f"✅ Status: {result['status']}")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Message: {result['message']}")
        print(f"   Result: {json.dumps(result['result'], indent=2)}")

        # Verify apple is most frequent
        if result['result']['top_words'][0]['word'] == 'apple':
            print("   ✅ Real calculation verified ('apple' is most frequent)")
        else:
            print(f"   ❌ Expected 'apple' to be most frequent")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 4: base64_encode
    try:
        print("\n" + "=" * 60)
        print("Test 4: base64_encode")
        print("=" * 60)

        test_data = {
            'tool_name': 'base64_encode',
            'parameters': {
                'text': 'Hello World',
                'operation': 'encode'
            }
        }

        request_data = json.dumps(test_data).encode('utf-8')
        req = Request(
            "http://127.0.0.1:8005/api/run",
            data=request_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read().decode('utf-8'))

        print(f"✅ Status: {result['status']}")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Message: {result['message']}")
        print(f"   Result: {json.dumps(result['result'], indent=2)}")

        # Verify encoding is correct
        if result['result']['result'] == 'SGVsbG8gV29ybGQ=':
            print("   ✅ Real calculation verified (correct base64)")
        else:
            print(f"   ❌ Incorrect base64 encoding")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 5: Unimplemented tool (should return mock)
    try:
        print("\n" + "=" * 60)
        print("Test 5: Unimplemented tool (should return mock)")
        print("=" * 60)

        test_data = {
            'tool_name': 'unimplemented_tool',
            'parameters': {}
        }

        request_data = json.dumps(test_data).encode('utf-8')
        req = Request(
            "http://127.0.0.1:8005/api/run",
            data=request_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read().decode('utf-8'))

        print(f"✅ Status: {result['status']}")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Message: {result['message']}")
        print(f"   Result: {json.dumps(result['result'], indent=2)}")

        # Verify it returns mock message
        if 'not yet implemented' in result['message']:
            print("   ✅ Correctly returns mock for unimplemented tool")
        else:
            print(f"   ❌ Should return mock message")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    return all_passed

if __name__ == "__main__":
    success = test_real_implementations()

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("   Real implementations are working correctly.")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Check the output above for details.")
        sys.exit(1)
