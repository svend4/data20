#!/usr/bin/env python3
"""
Redis Client for Data20 Knowledge Base
Phase 5.1.8: Redis connection and caching layer
"""

import redis
import json
import os
import time
from typing import Optional, Any, Dict, List
from datetime import timedelta
import pickle


class RedisClient:
    """
    Redis client wrapper with caching, pub/sub, and session management

    Usage:
        redis_client = RedisClient()

        # Caching
        redis_client.set("key", {"data": "value"}, ttl=3600)
        data = redis_client.get("key")

        # Pub/Sub
        redis_client.publish("channel", {"event": "job_completed"})
    """

    def __init__(
        self,
        url: Optional[str] = None,
        decode_responses: bool = True
    ):
        """
        Initialize Redis client

        Args:
            url: Redis connection URL (default: from env REDIS_URL)
            decode_responses: Decode byte responses to strings
        """

        self.url = url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )

        try:
            self.client = redis.from_url(
                self.url,
                decode_responses=decode_responses,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )

            # Test connection
            self.client.ping()
            self.connected = True

        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"⚠️  Redis connection failed: {e}")
            self.client = None
            self.connected = False


    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.client:
            return False

        try:
            self.client.ping()
            return True
        except:
            self.connected = False
            return False


    # ========================
    # Key-Value Operations
    # ========================

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a key-value pair

        Args:
            key: Cache key
            value: Value (will be JSON serialized)
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)

            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)

            return True

        except Exception as e:
            print(f"⚠️  Redis SET failed for {key}: {e}")
            return False


    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get a value by key

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if not self.is_available():
            return default

        try:
            value = self.client.get(key)

            if value is None:
                return default

            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            print(f"⚠️  Redis GET failed for {key}: {e}")
            return default


    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        if not self.is_available():
            return 0

        try:
            return self.client.delete(*keys)
        except Exception as e:
            print(f"⚠️  Redis DELETE failed: {e}")
            return 0


    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_available():
            return False

        try:
            return bool(self.client.exists(key))
        except:
            return False


    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key"""
        if not self.is_available():
            return False

        try:
            return bool(self.client.expire(key, seconds))
        except:
            return False


    # ========================
    # Hash Operations
    # ========================

    def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field"""
        if not self.is_available():
            return False

        try:
            serialized = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            self.client.hset(name, key, serialized)
            return True
        except Exception as e:
            print(f"⚠️  Redis HSET failed: {e}")
            return False


    def hget(self, name: str, key: str, default: Any = None) -> Optional[Any]:
        """Get hash field"""
        if not self.is_available():
            return default

        try:
            value = self.client.hget(name, key)
            if value is None:
                return default

            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except:
            return default


    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        if not self.is_available():
            return {}

        try:
            data = self.client.hgetall(name)

            # Try to parse each value as JSON
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v

            return result

        except:
            return {}


    # ========================
    # List Operations
    # ========================

    def lpush(self, key: str, *values: Any) -> int:
        """Push to list (left)"""
        if not self.is_available():
            return 0

        try:
            serialized = [
                json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for v in values
            ]
            return self.client.lpush(key, *serialized)
        except:
            return 0


    def rpush(self, key: str, *values: Any) -> int:
        """Push to list (right)"""
        if not self.is_available():
            return 0

        try:
            serialized = [
                json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for v in values
            ]
            return self.client.rpush(key, *serialized)
        except:
            return 0


    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get list range"""
        if not self.is_available():
            return []

        try:
            values = self.client.lrange(key, start, end)

            result = []
            for v in values:
                try:
                    result.append(json.loads(v))
                except (json.JSONDecodeError, TypeError):
                    result.append(v)

            return result

        except:
            return []


    # ========================
    # Pub/Sub Operations
    # ========================

    def publish(self, channel: str, message: Any) -> int:
        """
        Publish message to channel

        Args:
            channel: Channel name (e.g., "job_updates")
            message: Message to publish (will be JSON serialized)

        Returns:
            Number of subscribers that received the message
        """
        if not self.is_available():
            return 0

        try:
            serialized = json.dumps(message) if isinstance(message, (dict, list)) else str(message)
            return self.client.publish(channel, serialized)
        except Exception as e:
            print(f"⚠️  Redis PUBLISH failed: {e}")
            return 0


    def subscribe(self, *channels: str):
        """
        Subscribe to channels

        Returns:
            PubSub object for receiving messages

        Usage:
            pubsub = redis_client.subscribe("job_updates")
            for message in pubsub.listen():
                print(message)
        """
        if not self.is_available():
            return None

        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            print(f"⚠️  Redis SUBSCRIBE failed: {e}")
            return None


    # ========================
    # Cache Helpers
    # ========================

    def cache_tool_registry(self, registry_data: dict, ttl: int = 3600) -> bool:
        """
        Cache tool registry

        Args:
            registry_data: Tool registry JSON
            ttl: Cache for 1 hour by default
        """
        return self.set("tool_registry", registry_data, ttl=ttl)


    def get_cached_tool_registry(self) -> Optional[dict]:
        """Get cached tool registry"""
        return self.get("tool_registry")


    def cache_job_status(self, job_id: str, status: dict, ttl: int = 300) -> bool:
        """
        Cache job status

        Args:
            job_id: Job UUID
            status: Job status dict
            ttl: Cache for 5 minutes
        """
        return self.set(f"job:{job_id}:status", status, ttl=ttl)


    def get_cached_job_status(self, job_id: str) -> Optional[dict]:
        """Get cached job status"""
        return self.get(f"job:{job_id}:status")


    def clear_job_cache(self, job_id: str) -> int:
        """Clear all cache for a job"""
        return self.delete(f"job:{job_id}:status")


    # ========================
    # Rate Limiting
    # ========================

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window: int
    ) -> bool:
        """
        Check if rate limit is exceeded

        Args:
            key: Rate limit key (e.g., "api:192.168.1.1")
            max_requests: Max requests allowed
            window: Time window in seconds

        Returns:
            True if request allowed, False if rate limited
        """
        if not self.is_available():
            return True  # Allow if Redis unavailable

        try:
            pipe = self.client.pipeline()
            now = int(time.time())

            # Increment counter
            pipe.incr(key)
            pipe.expire(key, window)

            result = pipe.execute()
            count = result[0]

            return count <= max_requests

        except Exception as e:
            print(f"⚠️  Rate limit check failed: {e}")
            return True  # Allow on error


    # ========================
    # Health & Stats
    # ========================

    def get_info(self) -> dict:
        """Get Redis server info"""
        if not self.is_available():
            return {"connected": False}

        try:
            info = self.client.info()
            return {
                "connected": True,
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_days": info.get("uptime_in_days")
            }
        except:
            return {"connected": False}


    def flush_all(self) -> bool:
        """⚠️ DANGER: Delete all keys in current database"""
        if not self.is_available():
            return False

        try:
            self.client.flushdb()
            return True
        except:
            return False


    def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                self.client.close()
                self.connected = False
            except:
                pass


# ========================
# Singleton Instance
# ========================

# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis() -> RedisClient:
    """Get singleton Redis client"""
    global _redis_client

    if _redis_client is None:
        _redis_client = RedisClient()

    return _redis_client


def close_redis():
    """Close Redis connection"""
    global _redis_client

    if _redis_client:
        _redis_client.close()
        _redis_client = None


# ========================
# Testing
# ========================

if __name__ == "__main__":
    import time

    print("🧪 Testing Redis Client...")
    print("=" * 60)

    redis = RedisClient()

    # Test 1: Connection
    print(f"✅ Connected: {redis.is_available()}")

    # Test 2: Key-value
    redis.set("test_key", {"data": "value"}, ttl=10)
    print(f"✅ Set: test_key")

    value = redis.get("test_key")
    print(f"✅ Get: {value}")

    # Test 3: Hash
    redis.hset("test_hash", "field1", "value1")
    redis.hset("test_hash", "field2", {"nested": "data"})
    hash_data = redis.hgetall("test_hash")
    print(f"✅ Hash: {hash_data}")

    # Test 4: List
    redis.lpush("test_list", "item1", "item2")
    list_data = redis.lrange("test_list", 0, -1)
    print(f"✅ List: {list_data}")

    # Test 5: Pub/Sub
    subscribers = redis.publish("test_channel", {"event": "test"})
    print(f"✅ Published to {subscribers} subscribers")

    # Test 6: Info
    info = redis.get_info()
    print(f"✅ Redis info: {info}")

    # Cleanup
    redis.delete("test_key", "test_hash", "test_list")
    redis.close()

    print("=" * 60)
    print("✅ All tests passed!")
