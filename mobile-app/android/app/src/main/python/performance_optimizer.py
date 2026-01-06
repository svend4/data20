#!/usr/bin/env python3
"""
Performance Optimizer for Mobile Backend
Phase 8.2.3: Lazy loading, caching, and preloading optimization
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from functools import lru_cache, wraps
from collections import OrderedDict
from datetime import datetime, timedelta
import json


class PerformanceMetrics:
    """Track performance metrics"""

    def __init__(self):
        self.startup_time: Optional[float] = None
        self.tool_load_times: Dict[str, float] = {}
        self.tool_execution_times: Dict[str, List[float]] = {}
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.tools_loaded: int = 0
        self.tools_preloaded: int = 0

    def record_startup(self, duration: float):
        """Record app startup time"""
        self.startup_time = duration

    def record_tool_load(self, tool_name: str, duration: float):
        """Record tool loading time"""
        self.tool_load_times[tool_name] = duration
        self.tools_loaded += 1

    def record_tool_execution(self, tool_name: str, duration: float):
        """Record tool execution time"""
        if tool_name not in self.tool_execution_times:
            self.tool_execution_times[tool_name] = []
        self.tool_execution_times[tool_name].append(duration)

    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses += 1

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100

    def get_average_execution_time(self, tool_name: str) -> Optional[float]:
        """Get average execution time for a tool"""
        if tool_name not in self.tool_execution_times:
            return None
        times = self.tool_execution_times[tool_name]
        return sum(times) / len(times) if times else None

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary"""
        return {
            "startup_time": self.startup_time,
            "tools_loaded": self.tools_loaded,
            "tools_preloaded": self.tools_preloaded,
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.get_cache_hit_rate(),
            },
            "average_load_time": (
                sum(self.tool_load_times.values()) / len(self.tool_load_times)
                if self.tool_load_times else 0
            ),
            "slowest_tools": sorted(
                self.tool_load_times.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
        }


# Global metrics instance
metrics = PerformanceMetrics()


class LRUCache:
    """Simple LRU cache implementation with expiration"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.expiry: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key not in self.cache:
            metrics.record_cache_miss()
            return None

        # Check expiration
        if key in self.expiry and datetime.now() > self.expiry[key]:
            del self.cache[key]
            del self.expiry[key]
            metrics.record_cache_miss()
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        metrics.record_cache_hit()
        return self.cache[key]

    def set(self, key: str, value: Any):
        """Set item in cache"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove oldest item
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                if oldest_key in self.expiry:
                    del self.expiry[oldest_key]

        self.cache[key] = value
        self.expiry[key] = datetime.now() + timedelta(seconds=self.ttl_seconds)

    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.expiry.clear()

    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)


# Global caches
tool_registry_cache = LRUCache(max_size=50, ttl_seconds=600)  # 10 minutes
tool_result_cache = LRUCache(max_size=100, ttl_seconds=300)   # 5 minutes


class LazyToolLoader:
    """Lazy loading for tool modules"""

    def __init__(self, tools_dir: Path):
        self.tools_dir = tools_dir
        self.loaded_tools: Dict[str, Any] = {}
        self.tool_modules: Dict[str, Path] = {}
        self._scan_available_tools()

    def _scan_available_tools(self):
        """Scan for available tool modules without loading them"""
        if not self.tools_dir.exists():
            return

        for tool_file in self.tools_dir.glob("*.py"):
            if not tool_file.name.startswith("_"):
                tool_name = tool_file.stem
                self.tool_modules[tool_name] = tool_file

    def is_available(self, tool_name: str) -> bool:
        """Check if tool is available"""
        return tool_name in self.tool_modules

    def load_tool(self, tool_name: str) -> Optional[Any]:
        """Load tool module on-demand"""
        # Check if already loaded
        if tool_name in self.loaded_tools:
            return self.loaded_tools[tool_name]

        # Check if tool exists
        if tool_name not in self.tool_modules:
            return None

        # Load module
        start_time = time.time()
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                tool_name,
                self.tool_modules[tool_name]
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_tools[tool_name] = module

                # Record metrics
                duration = time.time() - start_time
                metrics.record_tool_load(tool_name, duration)

                return module
        except Exception as e:
            print(f"⚠️ Failed to load tool {tool_name}: {e}")
            return None

        return None

    def preload_tools(self, tool_names: List[str]):
        """Preload a list of tools"""
        print(f"🚀 Preloading {len(tool_names)} tools...")
        for tool_name in tool_names:
            if tool_name not in self.loaded_tools:
                self.load_tool(tool_name)
                metrics.tools_preloaded += 1

    def unload_tool(self, tool_name: str):
        """Unload a tool to free memory"""
        if tool_name in self.loaded_tools:
            del self.loaded_tools[tool_name]

    def get_loaded_count(self) -> int:
        """Get number of loaded tools"""
        return len(self.loaded_tools)

    def get_available_count(self) -> int:
        """Get number of available tools"""
        return len(self.tool_modules)


# Top 10 most used tools (based on usage statistics)
TOP_10_TOOLS = [
    "calculate_reading_time",
    "search_index",
    "advanced_search",
    "find_related",
    "backlinks_generator",
    "generate_statistics",
    "export_manager",
    "validate",
    "metadata_validator",
    "tags_cloud",
]


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time

        # Try to get tool name from args
        tool_name = kwargs.get('tool_name') or (args[0] if args else 'unknown')
        if isinstance(tool_name, str):
            metrics.record_tool_execution(tool_name, duration)

        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        # Try to get tool name from args
        tool_name = kwargs.get('tool_name') or (args[0] if args else 'unknown')
        if isinstance(tool_name, str):
            metrics.record_tool_execution(tool_name, duration)

        return result

    # Return appropriate wrapper based on whether function is async
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class ToolPreloader:
    """Intelligent tool preloader based on usage patterns"""

    def __init__(self, loader: LazyToolLoader, stats_file: Optional[Path] = None):
        self.loader = loader
        self.stats_file = stats_file or Path("/tmp/tool_usage_stats.json")
        self.usage_stats: Dict[str, int] = {}
        self._load_stats()

    def _load_stats(self):
        """Load usage statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    self.usage_stats = json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load usage stats: {e}")
                self.usage_stats = {}

    def _save_stats(self):
        """Save usage statistics to file"""
        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save usage stats: {e}")

    def record_usage(self, tool_name: str):
        """Record tool usage"""
        self.usage_stats[tool_name] = self.usage_stats.get(tool_name, 0) + 1
        self._save_stats()

    def get_top_tools(self, count: int = 10) -> List[str]:
        """Get most used tools"""
        if not self.usage_stats:
            # Return default top tools if no stats
            return TOP_10_TOOLS[:count]

        sorted_tools = sorted(
            self.usage_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [tool for tool, _ in sorted_tools[:count]]

    def preload_top_tools(self, count: int = 10):
        """Preload most used tools"""
        top_tools = self.get_top_tools(count)
        self.loader.preload_tools(top_tools)


def create_cache_key(tool_name: str, parameters: Dict[str, Any]) -> str:
    """Create cache key from tool name and parameters"""
    import hashlib
    param_str = json.dumps(parameters, sort_keys=True)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    return f"{tool_name}:{param_hash}"


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report"""
    return {
        "metrics": metrics.to_dict(),
        "cache_stats": {
            "registry_cache_size": tool_registry_cache.size(),
            "result_cache_size": tool_result_cache.size(),
        },
        "recommendations": _generate_recommendations(),
    }


def _generate_recommendations() -> List[str]:
    """Generate performance recommendations"""
    recommendations = []

    # Startup time
    if metrics.startup_time and metrics.startup_time > 3.0:
        recommendations.append(
            f"⚠️ Startup time ({metrics.startup_time:.2f}s) exceeds target (3s). "
            "Consider preloading fewer tools."
        )

    # Cache hit rate
    hit_rate = metrics.get_cache_hit_rate()
    if hit_rate < 50:
        recommendations.append(
            f"⚠️ Low cache hit rate ({hit_rate:.1f}%). "
            "Consider increasing cache TTL or size."
        )

    # Slow tools
    slow_tools = [
        name for name, duration in metrics.tool_load_times.items()
        if duration > 1.0
    ]
    if slow_tools:
        recommendations.append(
            f"⚠️ Slow loading tools: {', '.join(slow_tools)}. "
            "Consider optimization or lazy loading."
        )

    if not recommendations:
        recommendations.append("✅ Performance is good!")

    return recommendations


# CLI for testing
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Performance Optimizer Test")
    print("=" * 70)

    # Test lazy loader
    tools_dir = Path(__file__).parent / "tools"
    loader = LazyToolLoader(tools_dir)

    print(f"\n📊 Available tools: {loader.get_available_count()}")
    print(f"📊 Loaded tools: {loader.get_loaded_count()}")

    # Test preloader
    preloader = ToolPreloader(loader)
    print(f"\n🔝 Top 10 tools: {preloader.get_top_tools()}")

    # Preload top tools
    start_time = time.time()
    metrics.startup_time = 0  # Reset
    preloader.preload_top_tools(10)
    metrics.record_startup(time.time() - start_time)

    print(f"\n📊 Loaded tools: {loader.get_loaded_count()}")
    print(f"⏱️ Preload time: {metrics.startup_time:.3f}s")

    # Show metrics
    print("\n" + "=" * 70)
    print("📈 Performance Metrics:")
    print("=" * 70)
    report = get_performance_report()
    print(json.dumps(report, indent=2))
