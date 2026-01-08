#!/usr/bin/env python3
"""
Test database functionality - job history, stats, search
Tests SQLite database integration
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

def test_database():
    print("🧪 Testing database functionality...\n")

    # Setup environment
    temp_dir = tempfile.gettempdir()
    backend_main_simple.setup_environment(
        db_path=os.path.join(temp_dir, "test_data20.db"),
        upload_dir=os.path.join(temp_dir, "data20_uploads"),
        logs_dir=os.path.join(temp_dir, "data20_logs")
    )

    # Start server in background thread
    print("🚀 Starting HTTP server in background thread...")
    server_thread = Thread(target=backend_main_simple.run_server, args=("127.0.0.1", 8006), daemon=True)
    server_thread.start()

    # Wait for server to start
    print("⏳ Waiting 2 seconds for server to start...\n")
    time.sleep(2)

    all_passed = True

    # Test 1: Run several jobs to populate database
    try:
        print("=" * 60)
        print("Test 1: Run several jobs to populate database")
        print("=" * 60)

        jobs_to_run = [
            {'tool_name': 'calculate_statistics', 'parameters': {'data': [1, 2, 3, 4, 5], 'metrics': ['mean', 'std']}},
            {'tool_name': 'text_analysis', 'parameters': {'text': 'Hello world', 'language': 'en'}},
            {'tool_name': 'word_frequency', 'parameters': {'text': 'apple banana apple', 'top_n': 5}},
            {'tool_name': 'base64_encode', 'parameters': {'text': 'Test', 'operation': 'encode'}},
            {'tool_name': 'hash_calculator', 'parameters': {'text': 'Test', 'algorithm': 'md5'}},
        ]

        job_ids = []
        for job_data in jobs_to_run:
            request_data = json.dumps(job_data).encode('utf-8')
            req = Request(
                "http://127.0.0.1:8006/api/run",
                data=request_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            response = urlopen(req, timeout=5)
            result = json.loads(response.read().decode('utf-8'))
            job_ids.append(result['job_id'])
            print(f"   ✅ Job {result['job_id']}: {job_data['tool_name']} - {result['status']}")

        print(f"\n   ✅ Created {len(job_ids)} jobs in database")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 2: Get all jobs from /api/jobs
    try:
        print("\n" + "=" * 60)
        print("Test 2: Get all jobs from /api/jobs")
        print("=" * 60)

        response = urlopen("http://127.0.0.1:8006/api/jobs", timeout=5)
        jobs = json.loads(response.read().decode('utf-8'))

        print(f"   Retrieved {len(jobs)} jobs from database")
        if len(jobs) >= 5:
            print("   ✅ All jobs retrieved successfully")
            print(f"\n   Latest job:")
            print(f"      Job ID: {jobs[0]['job_id']}")
            print(f"      Tool: {jobs[0]['tool_name']}")
            print(f"      Status: {jobs[0]['status']}")
            print(f"      Created: {jobs[0]['created_at']}")
        else:
            print(f"   ❌ Expected at least 5 jobs, got {len(jobs)}")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 3: Get jobs filtered by tool_name
    try:
        print("\n" + "=" * 60)
        print("Test 3: Get jobs filtered by tool_name")
        print("=" * 60)

        response = urlopen("http://127.0.0.1:8006/api/jobs?tool_name=calculate_statistics", timeout=5)
        jobs = json.loads(response.read().decode('utf-8'))

        print(f"   Retrieved {len(jobs)} calculate_statistics jobs")
        if len(jobs) >= 1 and all(j['tool_name'] == 'calculate_statistics' for j in jobs):
            print("   ✅ Filter by tool_name working correctly")
        else:
            print(f"   ❌ Filter failed")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 4: Get statistics from /api/stats
    try:
        print("\n" + "=" * 60)
        print("Test 4: Get statistics from /api/stats")
        print("=" * 60)

        response = urlopen("http://127.0.0.1:8006/api/stats", timeout=5)
        stats = json.loads(response.read().decode('utf-8'))

        print(f"   Total jobs: {stats.get('total_jobs', 0)}")
        print(f"   By status: {stats.get('by_status', {})}")
        print(f"   Top tools: {stats.get('top_tools', [])}")

        if stats.get('total_jobs', 0) >= 5:
            print("   ✅ Statistics working correctly")
        else:
            print(f"   ❌ Expected at least 5 total jobs")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 5: Search for tools using /api/search
    try:
        print("\n" + "=" * 60)
        print("Test 5: Search for tools using /api/search")
        print("=" * 60)

        # Search for "statistics" (safer for URL encoding)
        from urllib.parse import quote
        query = "statistics"
        url = f"http://127.0.0.1:8006/api/search?q={quote(query)}"
        response = urlopen(url, timeout=5)
        search_result = json.loads(response.read().decode('utf-8'))

        print(f"   Query: '{search_result['query']}'")
        print(f"   Results: {search_result['count']} tools found")

        if search_result['count'] > 0:
            print("   ✅ Search working correctly")
            print(f"   Found tools:")
            for tool in search_result['results'][:3]:
                print(f"      - {tool['name']}: {tool.get('display_name', 'N/A')}")
        else:
            print(f"   ❌ Expected at least 1 result")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    # Test 6: Search for "text" category
    try:
        print("\n" + "=" * 60)
        print("Test 6: Search for 'text' category")
        print("=" * 60)

        response = urlopen("http://127.0.0.1:8006/api/search?q=text", timeout=5)
        search_result = json.loads(response.read().decode('utf-8'))

        print(f"   Query: '{search_result['query']}'")
        print(f"   Results: {search_result['count']} tools found")

        if search_result['count'] > 0:
            print("   ✅ Category search working correctly")
        else:
            print(f"   ❌ Expected at least 1 result")
            all_passed = False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    return all_passed

if __name__ == "__main__":
    success = test_database()

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL DATABASE TESTS PASSED!")
        print("   Database, stats, and search are working correctly.")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Check the output above for details.")
        sys.exit(1)
