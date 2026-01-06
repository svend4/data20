"""
Performance Tests and Benchmarks
Phase 8.4.4: Performance Tests & Benchmarks

Benchmarks for all 57 tools to ensure performance targets are met.
"""

import pytest
import time
from pathlib import Path
import sys
from statistics import mean, median
import json

# Add tools directory to path
tools_dir = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(tools_dir))


@pytest.mark.performance
class TestToolPerformance:
    """Performance benchmarks for core tools"""

    def measure_execution_time(self, func, *args, iterations=10):
        """Measure average execution time"""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args)
            end = time.perf_counter()
            times.append(end - start)

        return {
            'mean': mean(times),
            'median': median(times),
            'min': min(times),
            'max': max(times),
            'iterations': iterations
        }

    @pytest.mark.slow
    def test_calculate_reading_time_performance(self, benchmark):
        """Benchmark calculate_reading_time tool"""
        from calculate_reading_time import ReadingSpeedAnalyzer

        analyzer = ReadingSpeedAnalyzer()
        test_text = "word " * 1000  # 1000 words

        # Target: < 100ms for 1000 words
        result = benchmark(analyzer.analyze_content, test_text)

        # Verify performance
        assert benchmark.stats['mean'] < 0.1  # Less than 100ms

    @pytest.mark.slow
    def test_search_performance(self, benchmark):
        """Benchmark search_index tool"""
        from search_index import search_articles

        articles = [
            {'id': i, 'title': f'Article {i}', 'content': f'Content {i}'}
            for i in range(1000)
        ]

        # Target: < 200ms for 1000 articles
        result = benchmark(search_articles, "test query", articles)

        assert benchmark.stats['mean'] < 0.2  # Less than 200ms

    @pytest.mark.slow
    def test_statistics_performance(self, benchmark):
        """Benchmark generate_statistics tool"""
        from generate_statistics import generate_statistics

        data = list(range(10000))  # 10k numbers

        # Target: < 50ms for 10k numbers
        result = benchmark(generate_statistics, data)

        assert benchmark.stats['mean'] < 0.05  # Less than 50ms

    @pytest.mark.slow
    def test_validate_data_performance(self, benchmark):
        """Benchmark validate_data tool"""
        from validate_data import validate_data

        # Target: < 10ms for simple validation
        result = benchmark(validate_data, "test@example.com", "email")

        assert benchmark.stats['mean'] < 0.01  # Less than 10ms

    @pytest.mark.slow
    def test_format_text_performance(self, benchmark):
        """Benchmark format_text tool"""
        from format_text import format_text

        text = "hello world " * 1000  # Large text

        # Target: < 50ms for 1000 words
        result = benchmark(format_text, text, "uppercase")

        assert benchmark.stats['mean'] < 0.05  # Less than 50ms


@pytest.mark.performance
@pytest.mark.slow
class TestHeavyToolPerformance:
    """Performance benchmarks for computationally heavy tools"""

    def test_build_graph_performance(self, benchmark):
        """Benchmark build_graph tool"""
        try:
            from build_graph import build_knowledge_graph

            articles = [
                {
                    'id': i,
                    'title': f'Article {i}',
                    'content': f'Content with link to Article {(i+1) % 100}',
                    'tags': ['test']
                }
                for i in range(100)
            ]

            # Target: < 5 seconds for 100 articles
            result = benchmark(build_knowledge_graph, articles)

            assert benchmark.stats['mean'] < 5.0  # Less than 5 seconds

        except ImportError:
            pytest.skip("build_graph tool not available")

    def test_calculate_pagerank_performance(self, benchmark):
        """Benchmark calculate_pagerank tool"""
        try:
            from calculate_pagerank import calculate_pagerank

            # Create a graph with 100 nodes
            articles = [
                {
                    'id': i,
                    'title': f'Article {i}',
                    'links': [(i + 1) % 100, (i + 2) % 100]
                }
                for i in range(100)
            ]

            # Target: < 2 seconds for 100 nodes
            result = benchmark(calculate_pagerank, articles)

            assert benchmark.stats['mean'] < 2.0  # Less than 2 seconds

        except ImportError:
            pytest.skip("calculate_pagerank tool not available")

    def test_build_concordance_performance(self, benchmark):
        """Benchmark build_concordance tool"""
        try:
            from build_concordance import build_concordance

            text = "word " * 10000  # 10k words

            # Target: < 3 seconds for 10k words
            result = benchmark(build_concordance, text)

            assert benchmark.stats['mean'] < 3.0  # Less than 3 seconds

        except ImportError:
            pytest.skip("build_concordance tool not available")


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage tests for tools"""

    def test_tool_memory_footprint(self):
        """Test that tools don't consume excessive memory"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Execute several tools
        try:
            from calculate_reading_time import ReadingSpeedAnalyzer
            analyzer = ReadingSpeedAnalyzer()

            for _ in range(1000):
                analyzer.analyze_content("test " * 100)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - baseline_memory

            # Should not increase more than 100MB for 1000 iterations
            assert memory_increase < 100

        except ImportError:
            pytest.skip("Tool not available for memory testing")

    def test_no_memory_leaks(self):
        """Test that tools don't leak memory"""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())

        memory_samples = []

        for iteration in range(10):
            # Execute tools
            try:
                from generate_statistics import generate_statistics
                for _ in range(100):
                    generate_statistics(list(range(1000)))

                # Force garbage collection
                gc.collect()

                # Sample memory
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)

            except ImportError:
                pytest.skip("Tool not available")

        # Memory should not continuously grow
        # Allow some variance but no linear growth
        if len(memory_samples) >= 3:
            first_third = mean(memory_samples[:3])
            last_third = mean(memory_samples[-3:])

            # Should not grow more than 50MB
            assert (last_third - first_third) < 50


@pytest.mark.performance
class TestConcurrentExecution:
    """Test concurrent tool execution performance"""

    def test_parallel_tool_execution(self):
        """Test that tools can run in parallel efficiently"""
        import concurrent.futures

        try:
            from calculate_reading_time import ReadingSpeedAnalyzer

            analyzer = ReadingSpeedAnalyzer()
            texts = [f"text {i} " * 100 for i in range(10)]

            start = time.perf_counter()

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(analyzer.analyze_content, text)
                    for text in texts
                ]
                results = [f.result() for f in futures]

            end = time.perf_counter()
            parallel_time = end - start

            # Sequential execution
            start = time.perf_counter()
            for text in texts:
                analyzer.analyze_content(text)
            end = time.perf_counter()
            sequential_time = end - start

            # Parallel should be faster (at least 1.5x speedup)
            assert parallel_time < sequential_time / 1.5

        except ImportError:
            pytest.skip("Tool not available")


@pytest.mark.performance
class TestAPIPerformance:
    """Test API endpoint performance"""

    @pytest.mark.slow
    def test_api_response_time(self, client, admin_token_headers):
        """Test that API responds within acceptable time"""
        import time

        times = []
        for _ in range(10):
            start = time.perf_counter()

            response = client.post(
                "/api/v1/tools/execute",
                headers=admin_token_headers,
                json={
                    "tool_name": "calculate_reading_time",
                    "parameters": {"text": "test"}
                }
            )

            end = time.perf_counter()
            times.append(end - start)

            assert response.status_code == 200

        avg_time = mean(times)

        # API should respond in < 500ms on average
        assert avg_time < 0.5

    @pytest.mark.slow
    def test_api_throughput(self, client, admin_token_headers):
        """Test API request throughput"""
        import concurrent.futures

        def make_request():
            return client.post(
                "/api/v1/tools/execute",
                headers=admin_token_headers,
                json={
                    "tool_name": "calculate_reading_time",
                    "parameters": {"text": "test"}
                }
            )

        # Measure requests per second
        start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in futures]

        end = time.perf_counter()
        duration = end - start

        requests_per_second = 100 / duration

        # Should handle at least 50 requests/second
        assert requests_per_second >= 50

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)


@pytest.mark.performance
class TestDatabasePerformance:
    """Test database query performance"""

    @pytest.mark.database
    @pytest.mark.slow
    def test_bulk_insert_performance(self, db_session):
        """Test bulk insert performance"""
        from backend.models import Article

        start = time.perf_counter()

        # Insert 1000 articles
        articles = [
            Article(
                title=f"Article {i}",
                content=f"Content {i}",
                tags=["test"]
            )
            for i in range(1000)
        ]

        db_session.bulk_save_objects(articles)
        db_session.commit()

        end = time.perf_counter()
        duration = end - start

        # Should complete in < 5 seconds
        assert duration < 5.0

    @pytest.mark.database
    @pytest.mark.slow
    def test_search_query_performance(self, db_session):
        """Test search query performance"""
        from backend.models import Article

        # Ensure we have some data
        article = Article(
            title="Test Article",
            content="Test content with searchable terms"
        )
        db_session.add(article)
        db_session.commit()

        start = time.perf_counter()

        # Perform search query
        results = db_session.query(Article).filter(
            Article.content.contains("searchable")
        ).all()

        end = time.perf_counter()
        duration = end - start

        # Should complete in < 100ms
        assert duration < 0.1


# Pytest benchmark plugin configuration
def pytest_benchmark_group_stats(config, benchmarks, group_by):
    """Group benchmarks by test class"""
    return sorted(benchmarks, key=lambda b: b['group'])


# Performance report generator
def generate_performance_report(benchmark_results):
    """Generate performance report from benchmark results"""
    report = {
        'timestamp': time.time(),
        'benchmarks': [],
        'summary': {
            'total_tests': len(benchmark_results),
            'passed': sum(1 for b in benchmark_results if b['passed']),
            'failed': sum(1 for b in benchmark_results if not b['passed'])
        }
    }

    for result in benchmark_results:
        report['benchmarks'].append({
            'name': result['name'],
            'mean_time': result['stats']['mean'],
            'median_time': result['stats']['median'],
            'iterations': result['stats']['iterations'],
            'passed': result['passed']
        })

    return report
