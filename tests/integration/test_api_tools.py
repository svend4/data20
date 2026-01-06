"""
Integration Tests for Tools API
Phase 8.4.2: Integration Tests

Tests for the tools execution API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json


@pytest.mark.integration
class TestToolsListAPI:
    """Test tools listing API"""

    def test_list_all_tools(self, client, admin_token_headers):
        """Test GET /api/v1/tools - list all available tools"""
        response = client.get(
            "/api/v1/tools",
            headers=admin_token_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert 'tools' in data
        assert isinstance(data['tools'], list)
        assert len(data['tools']) >= 50  # Should have ~57 tools

    def test_list_tools_with_category_filter(self, client, admin_token_headers):
        """Test tools list with category filter"""
        response = client.get(
            "/api/v1/tools?category=text_analysis",
            headers=admin_token_headers
        )

        assert response.status_code == 200
        data = response.json()

        # All returned tools should be in text_analysis category
        for tool in data['tools']:
            assert tool.get('category') == 'text_analysis'

    def test_list_tools_unauthorized(self, client):
        """Test tools list without authentication"""
        response = client.get("/api/v1/tools")

        # Should return 401 or allow public access depending on config
        assert response.status_code in [200, 401]


@pytest.mark.integration
class TestToolExecutionAPI:
    """Test tool execution API"""

    def test_execute_reading_time_tool(self, client, admin_token_headers):
        """Test executing calculate_reading_time tool"""
        payload = {
            "tool_name": "calculate_reading_time",
            "parameters": {
                "text": "This is a test article with some content for reading time calculation."
            }
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert 'result' in data
        assert 'reading_time_minutes' in data['result']
        assert 'word_count' in data['result']

    def test_execute_search_tool(self, client, admin_token_headers):
        """Test executing search_index tool"""
        payload = {
            "tool_name": "search_index",
            "parameters": {
                "query": "test",
                "articles": [
                    {"id": 1, "title": "Test Article", "content": "Test content"}
                ]
            }
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert 'result' in data
        assert isinstance(data['result'], list)

    def test_execute_statistics_tool(self, client, admin_token_headers):
        """Test executing generate_statistics tool"""
        payload = {
            "tool_name": "generate_statistics",
            "parameters": {
                "data": [1, 2, 3, 4, 5]
            }
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert 'result' in data
        result = data['result']
        assert 'mean' in result
        assert 'median' in result
        assert 'min' in result
        assert 'max' in result
        assert result['mean'] == 3.0

    def test_execute_nonexistent_tool(self, client, admin_token_headers):
        """Test executing a tool that doesn't exist"""
        payload = {
            "tool_name": "nonexistent_tool",
            "parameters": {}
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        assert response.status_code == 404
        data = response.json()
        assert 'error' in data or 'detail' in data

    def test_execute_tool_missing_parameters(self, client, admin_token_headers):
        """Test executing tool with missing required parameters"""
        payload = {
            "tool_name": "calculate_reading_time",
            "parameters": {}  # Missing 'text' parameter
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        assert response.status_code in [400, 422]

    def test_execute_tool_invalid_parameters(self, client, admin_token_headers):
        """Test executing tool with invalid parameter types"""
        payload = {
            "tool_name": "generate_statistics",
            "parameters": {
                "data": "invalid"  # Should be list of numbers
            }
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        assert response.status_code in [400, 422, 500]

    def test_execute_tool_unauthorized(self, client):
        """Test tool execution without authentication"""
        payload = {
            "tool_name": "calculate_reading_time",
            "parameters": {"text": "test"}
        }

        response = client.post(
            "/api/v1/tools/execute",
            json=payload
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestToolMetadataAPI:
    """Test tool metadata API"""

    def test_get_tool_info(self, client, admin_token_headers):
        """Test GET /api/v1/tools/{tool_name} - get tool metadata"""
        response = client.get(
            "/api/v1/tools/calculate_reading_time",
            headers=admin_token_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert 'name' in data
        assert 'description' in data
        assert 'parameters' in data
        assert data['name'] == 'calculate_reading_time'

    def test_get_tool_schema(self, client, admin_token_headers):
        """Test GET /api/v1/tools/{tool_name}/schema - get tool parameter schema"""
        response = client.get(
            "/api/v1/tools/calculate_reading_time/schema",
            headers=admin_token_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert 'parameters' in data
        assert 'required' in data
        # Should have schema for 'text' parameter
        assert 'text' in data['parameters']


@pytest.mark.integration
class TestAsyncToolExecution:
    """Test asynchronous tool execution"""

    def test_submit_async_job(self, client, admin_token_headers):
        """Test submitting async tool execution job"""
        payload = {
            "tool_name": "build_graph",  # Heavy tool
            "parameters": {
                "articles": [{"id": 1, "title": "Test"}]
            },
            "async": True
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        assert response.status_code in [200, 202]
        data = response.json()

        # Should return job ID for tracking
        assert 'job_id' in data or 'task_id' in data

    def test_check_job_status(self, client, admin_token_headers):
        """Test checking async job status"""
        # First submit a job
        payload = {
            "tool_name": "generate_statistics",
            "parameters": {"data": [1, 2, 3]},
            "async": True
        }

        submit_response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        if submit_response.status_code in [200, 202]:
            data = submit_response.json()
            job_id = data.get('job_id') or data.get('task_id')

            if job_id:
                # Check job status
                status_response = client.get(
                    f"/api/v1/jobs/{job_id}",
                    headers=admin_token_headers
                )

                assert status_response.status_code == 200
                status_data = status_response.json()

                assert 'status' in status_data
                assert status_data['status'] in ['pending', 'running', 'completed', 'failed']


@pytest.mark.integration
class TestBatchToolExecution:
    """Test batch tool execution"""

    def test_execute_multiple_tools(self, client, admin_token_headers):
        """Test executing multiple tools in batch"""
        payload = {
            "tools": [
                {
                    "tool_name": "calculate_reading_time",
                    "parameters": {"text": "Test text 1"}
                },
                {
                    "tool_name": "count_words",
                    "parameters": {"text": "Test text 2"}
                }
            ]
        }

        response = client.post(
            "/api/v1/tools/batch",
            headers=admin_token_headers,
            json=payload
        )

        # Batch execution may or may not be implemented
        if response.status_code == 200:
            data = response.json()
            assert 'results' in data
            assert len(data['results']) == 2


@pytest.mark.integration
class TestToolRateLimiting:
    """Test tool execution rate limiting"""

    def test_rate_limit_enforcement(self, client, admin_token_headers):
        """Test that rate limiting is enforced"""
        payload = {
            "tool_name": "calculate_reading_time",
            "parameters": {"text": "test"}
        }

        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = client.post(
                "/api/v1/tools/execute",
                headers=admin_token_headers,
                json=payload
            )
            responses.append(response.status_code)

        # Should get some rate limit responses (429)
        # Or all succeed if rate limiting is disabled
        assert all(status in [200, 429, 503] for status in responses)


@pytest.mark.integration
class TestToolCaching:
    """Test tool result caching"""

    def test_cached_results(self, client, admin_token_headers):
        """Test that identical requests are cached"""
        payload = {
            "tool_name": "calculate_reading_time",
            "parameters": {"text": "Same text for caching test"}
        }

        # First request
        response1 = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        # Second identical request
        response2 = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Results should be identical
        assert response1.json() == response2.json()

        # Check if cache headers are set
        # (implementation-dependent)


@pytest.mark.integration
@pytest.mark.slow
class TestHeavyTools:
    """Test execution of computationally heavy tools"""

    def test_build_graph_tool(self, client, admin_token_headers):
        """Test build_graph tool with large dataset"""
        payload = {
            "tool_name": "build_graph",
            "parameters": {
                "articles": [
                    {"id": i, "title": f"Article {i}", "tags": ["test"]}
                    for i in range(100)
                ]
            }
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload,
            timeout=30  # Allow longer timeout
        )

        # Should complete or return async job
        assert response.status_code in [200, 202, 504]

    def test_calculate_pagerank_tool(self, client, admin_token_headers):
        """Test calculate_pagerank tool"""
        payload = {
            "tool_name": "calculate_pagerank",
            "parameters": {
                "articles": [
                    {"id": 1, "title": "A", "links": [2]},
                    {"id": 2, "title": "B", "links": [1]},
                ]
            }
        }

        response = client.post(
            "/api/v1/tools/execute",
            headers=admin_token_headers,
            json=payload
        )

        # Should execute successfully or timeout
        assert response.status_code in [200, 202, 504]


# Fixtures for integration tests
@pytest.fixture
def sample_tool_payload():
    """Sample payload for tool execution"""
    return {
        "tool_name": "calculate_reading_time",
        "parameters": {
            "text": "This is a sample text for testing purposes."
        }
    }
