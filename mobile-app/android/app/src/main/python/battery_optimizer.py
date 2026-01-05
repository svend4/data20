#!/usr/bin/env python3
"""
Battery Optimizer for Mobile Backend
Phase 8.2.4: Auto-stop, activity tracking, and power management
"""

import asyncio
import time
from typing import Optional, Callable, Dict
from datetime import datetime, timedelta
from enum import Enum
import threading
import signal
import sys


class BackendState(str, Enum):
    """Backend operational states"""
    ACTIVE = "active"
    IDLE = "idle"
    SLEEPING = "sleeping"
    STOPPED = "stopped"


class ActivityTracker:
    """Track backend activity and idle time"""

    def __init__(self, idle_timeout_seconds: int = 300):
        """
        Args:
            idle_timeout_seconds: Seconds of inactivity before considered idle (default 5 min)
        """
        self.idle_timeout_seconds = idle_timeout_seconds
        self.last_activity_time = datetime.now()
        self.total_requests = 0
        self.requests_per_minute: Dict[str, int] = {}
        self._lock = threading.Lock()

    def record_activity(self):
        """Record user activity"""
        with self._lock:
            self.last_activity_time = datetime.now()
            self.total_requests += 1

            # Track requests per minute
            minute_key = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.requests_per_minute[minute_key] = \
                self.requests_per_minute.get(minute_key, 0) + 1

    def get_idle_time(self) -> float:
        """Get seconds since last activity"""
        with self._lock:
            delta = datetime.now() - self.last_activity_time
            return delta.total_seconds()

    def is_idle(self) -> bool:
        """Check if backend is idle"""
        return self.get_idle_time() > self.idle_timeout_seconds

    def get_activity_rate(self, minutes: int = 5) -> float:
        """Get average requests per minute over last N minutes"""
        with self._lock:
            now = datetime.now()
            total_requests = 0
            count = 0

            for i in range(minutes):
                minute_key = (now - timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M")
                if minute_key in self.requests_per_minute:
                    total_requests += self.requests_per_minute[minute_key]
                    count += 1

            return total_requests / max(count, 1)

    def get_stats(self) -> Dict:
        """Get activity statistics"""
        return {
            "total_requests": self.total_requests,
            "idle_time": f"{self.get_idle_time():.1f}s",
            "is_idle": self.is_idle(),
            "activity_rate": f"{self.get_activity_rate():.2f} req/min",
            "last_activity": self.last_activity_time.isoformat(),
        }


class BackendPowerManager:
    """Manage backend power states and auto-stop"""

    def __init__(
        self,
        activity_tracker: ActivityTracker,
        idle_timeout_seconds: int = 300,
        auto_stop_enabled: bool = True,
    ):
        """
        Args:
            activity_tracker: Activity tracker instance
            idle_timeout_seconds: Seconds before auto-stop (default 5 min)
            auto_stop_enabled: Enable automatic stop on idle
        """
        self.activity_tracker = activity_tracker
        self.idle_timeout_seconds = idle_timeout_seconds
        self.auto_stop_enabled = auto_stop_enabled
        self.state = BackendState.ACTIVE
        self.state_changed_at = datetime.now()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_callback: Optional[Callable] = None
        self._lock = threading.Lock()

    def set_shutdown_callback(self, callback: Callable):
        """Set callback to call when auto-stop is triggered"""
        self._shutdown_callback = callback

    def change_state(self, new_state: BackendState):
        """Change backend state"""
        with self._lock:
            if self.state != new_state:
                old_state = self.state
                self.state = new_state
                self.state_changed_at = datetime.now()
                print(f"🔋 Backend state: {old_state.value} → {new_state.value}")

    async def start_monitoring(self):
        """Start monitoring for auto-stop"""
        if not self.auto_stop_enabled:
            print("🔋 Auto-stop disabled")
            return

        print(f"🔋 Auto-stop monitoring started (timeout: {self.idle_timeout_seconds}s)")

        while True:
            await asyncio.sleep(30)  # Check every 30 seconds

            idle_time = self.activity_tracker.get_idle_time()

            # State machine
            if idle_time < 60:
                # Active: < 1 minute idle
                if self.state != BackendState.ACTIVE:
                    self.change_state(BackendState.ACTIVE)

            elif idle_time < self.idle_timeout_seconds:
                # Idle: 1-5 minutes idle
                if self.state != BackendState.IDLE:
                    self.change_state(BackendState.IDLE)
                    print(f"💤 Backend idle ({idle_time:.0f}s)")

            else:
                # Sleeping/Stopped: > 5 minutes idle
                if self.state == BackendState.IDLE:
                    self.change_state(BackendState.SLEEPING)
                    print(f"😴 Backend sleeping (idle: {idle_time:.0f}s)")

                    # Auto-stop after additional grace period
                    if idle_time > self.idle_timeout_seconds + 60:
                        if self._shutdown_callback:
                            print("🛑 Triggering auto-stop")
                            self.change_state(BackendState.STOPPED)
                            await self._shutdown_callback()
                        break

    def get_power_stats(self) -> Dict:
        """Get power management statistics"""
        with self._lock:
            time_in_state = (datetime.now() - self.state_changed_at).total_seconds()

            return {
                "state": self.state.value,
                "time_in_state": f"{time_in_state:.1f}s",
                "auto_stop_enabled": self.auto_stop_enabled,
                "idle_timeout": f"{self.idle_timeout_seconds}s",
                "estimated_battery_impact": self._estimate_battery_impact(),
            }

    def _estimate_battery_impact(self) -> str:
        """Estimate battery impact based on state"""
        # Battery consumption estimates (% per hour)
        CONSUMPTION = {
            BackendState.ACTIVE: 4.5,      # Active processing
            BackendState.IDLE: 1.5,        # Idle but ready
            BackendState.SLEEPING: 0.5,    # Minimal activity
            BackendState.STOPPED: 0.0,     # No backend running
        }

        rate = CONSUMPTION.get(self.state, 0.0)
        return f"{rate:.1f}% per hour"


class BatteryMonitor:
    """Monitor overall battery usage"""

    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.cpu_time = 0.0
        self.network_bytes = 0

    def record_request(self, cpu_time: float, network_bytes: int = 0):
        """Record a request execution"""
        self.request_count += 1
        self.cpu_time += cpu_time
        self.network_bytes += network_bytes

    def get_battery_estimate(self) -> Dict:
        """Estimate battery consumption"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        runtime_hours = runtime / 3600.0

        # Rough estimates based on:
        # - CPU time → power consumption
        # - Network activity → radio power
        # - Idle time → baseline consumption

        # CPU: 5% battery per hour of active CPU
        cpu_hours = self.cpu_time / 3600.0
        cpu_drain = cpu_hours * 5.0

        # Network: 2% battery per 100MB
        network_mb = self.network_bytes / (1024 * 1024)
        network_drain = (network_mb / 100) * 2.0

        # Baseline: 1% per hour when idle
        baseline_drain = runtime_hours * 1.0

        total_drain = cpu_drain + network_drain + baseline_drain

        return {
            "runtime": f"{runtime:.0f}s",
            "runtime_hours": f"{runtime_hours:.2f}h",
            "total_requests": self.request_count,
            "cpu_time": f"{self.cpu_time:.2f}s",
            "network_mb": f"{network_mb:.2f} MB",
            "estimated_drain": {
                "cpu": f"{cpu_drain:.2f}%",
                "network": f"{network_drain:.2f}%",
                "baseline": f"{baseline_drain:.2f}%",
                "total": f"{total_drain:.2f}%",
                "per_hour": f"{(total_drain / max(runtime_hours, 0.01)):.2f}%/h",
            },
            "target": "< 5% per hour",
            "target_met": (total_drain / max(runtime_hours, 0.01)) < 5.0,
        }


# Global instances
activity_tracker = ActivityTracker(idle_timeout_seconds=300)  # 5 minutes
power_manager = BackendPowerManager(activity_tracker, idle_timeout_seconds=300)
battery_monitor = BatteryMonitor()


def get_battery_stats() -> Dict:
    """Get comprehensive battery statistics"""
    return {
        "activity": activity_tracker.get_stats(),
        "power_management": power_manager.get_power_stats(),
        "battery_estimate": battery_monitor.get_battery_estimate(),
    }


# Middleware for tracking activity
def track_request_activity():
    """Decorator/middleware to track request activity"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            activity_tracker.record_activity()
            start_time = time.time()

            result = await func(*args, **kwargs)

            cpu_time = time.time() - start_time
            battery_monitor.record_request(cpu_time)

            return result

        def sync_wrapper(*args, **kwargs):
            activity_tracker.record_activity()
            start_time = time.time()

            result = func(*args, **kwargs)

            cpu_time = time.time() - start_time
            battery_monitor.record_request(cpu_time)

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Configuration
class BatteryConfig:
    """Battery optimization configuration"""

    # Auto-stop configuration
    IDLE_TIMEOUT_SECONDS = 300  # 5 minutes
    AUTO_STOP_ENABLED = True

    # Doze mode compatibility
    DOZE_EXEMPT = False  # Request battery optimization exemption
    BACKGROUND_WORK_ENABLED = True

    # WorkManager configuration
    PERIODIC_SYNC_INTERVAL_MINUTES = 60
    CLEANUP_INTERVAL_MINUTES = 360  # 6 hours

    # Battery targets
    TARGET_DRAIN_PER_HOUR = 5.0  # 5% per hour
    WARNING_DRAIN_PER_HOUR = 7.0  # Warn if exceeds

    @classmethod
    def from_env(cls):
        """Load configuration from environment"""
        import os

        cls.IDLE_TIMEOUT_SECONDS = int(
            os.getenv("BATTERY_IDLE_TIMEOUT", "300")
        )
        cls.AUTO_STOP_ENABLED = (
            os.getenv("BATTERY_AUTO_STOP", "true").lower() == "true"
        )

        return cls


# CLI for testing
if __name__ == "__main__":
    print("=" * 70)
    print("🔋 Battery Optimizer Test")
    print("=" * 70)

    # Simulate activity
    print("\n1. Simulating active usage...")
    for i in range(10):
        activity_tracker.record_activity()
        battery_monitor.record_request(0.1)
        time.sleep(0.1)

    print(f"   Idle time: {activity_tracker.get_idle_time():.1f}s")
    print(f"   State: {power_manager.state.value}")

    # Simulate idle
    print("\n2. Simulating idle period (10s)...")
    time.sleep(10)
    print(f"   Idle time: {activity_tracker.get_idle_time():.1f}s")

    # Show stats
    print("\n" + "=" * 70)
    print("📊 Battery Statistics:")
    print("=" * 70)

    import json
    stats = get_battery_stats()
    print(json.dumps(stats, indent=2))

    print("\n" + "=" * 70)
    print("✅ Battery Optimizer Test Complete")
    print("=" * 70)
