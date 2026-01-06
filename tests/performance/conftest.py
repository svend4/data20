"""
Fixtures for performance tests
"""

import pytest


# Pytest benchmark configuration
@pytest.fixture(scope='session')
def benchmark_config():
    """Configuration for pytest-benchmark"""
    return {
        'min_rounds': 5,
        'max_time': 1.0,
        'calibration_precision': 10,
        'warmup': True,
        'warmup_iterations': 100000,
    }
