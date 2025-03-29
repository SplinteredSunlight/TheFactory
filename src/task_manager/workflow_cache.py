"""
Workflow Cache Module

This module provides caching for workflow results.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class WorkflowCache:
    """Workflow Cache class for caching workflow results."""
    
    def __init__(self, cache_dir: str, ttl: int = 3600):
        """
        Initialize a WorkflowCache.
        
        Args:
            cache_dir: Directory for caching
            ttl: Time to live in seconds
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        os.makedirs(cache_dir, exist_ok=True)
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached value.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            if "timestamp" in cache_data:
                timestamp = datetime.fromisoformat(cache_data["timestamp"])
                if datetime.now() - timestamp > timedelta(seconds=self.ttl):
                    # Cache is expired
                    os.remove(cache_file)
                    return None
            
            return cache_data.get("value")
        except Exception as e:
            print(f"Error getting cached value: {e}")
            return None
    
    async def set(self, key: str, value: Dict[str, Any]) -> bool:
        """
        Set a cached value.
        
        Args:
            key: Cache key
            value: Value to cache
        
        Returns:
            True if value was cached, False otherwise
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "value": value
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error setting cached value: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a cached value.
        
        Args:
            key: Cache key
        
        Returns:
            True if value was deleted, False otherwise
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if not os.path.exists(cache_file):
            return False
        
        try:
            os.remove(cache_file)
            return True
        except Exception as e:
            print(f"Error deleting cached value: {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all cached values.
        
        Returns:
            True if cache was cleared, False otherwise
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, filename))
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    async def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all cached values.
        
        Returns:
            Dictionary of cached values
        """
        result = {}
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    key = filename[:-5]  # Remove .json extension
                    value = await self.get(key)
                    if value is not None:
                        result[key] = value
            return result
        except Exception as e:
            print(f"Error getting all cached values: {e}")
            return {}
    
    def generate_key(self, task_id: str, workflow_type: str, params: Dict[str, Any]) -> str:
        """
        Generate a cache key.
        
        Args:
            task_id: Task ID
            workflow_type: Workflow type
            params: Workflow parameters
        
        Returns:
            Cache key
        """
        # Create a string representation of the parameters
        params_str = json.dumps(params, sort_keys=True)
        
        # Create a hash of the parameters
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        # Create a key using the task ID, workflow type, and parameters hash
        return f"{task_id}_{workflow_type}_{params_hash}"


class WorkflowCacheManager:
    """Workflow Cache Manager class for managing workflow caches."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize a WorkflowCacheManager.
        
        Args:
            cache_dir: Directory for caching
        """
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache(self, ttl: int = 3600) -> WorkflowCache:
        """
        Get a WorkflowCache instance.
        
        Args:
            ttl: Time to live in seconds
        
        Returns:
            WorkflowCache instance
        """
        return WorkflowCache(self.cache_dir, ttl)


def get_workflow_cache_manager(cache_dir: Optional[str] = None) -> WorkflowCacheManager:
    """
    Get a WorkflowCacheManager instance.
    
    Args:
        cache_dir: Directory for caching
    
    Returns:
        WorkflowCacheManager instance
    """
    return WorkflowCacheManager(cache_dir)
