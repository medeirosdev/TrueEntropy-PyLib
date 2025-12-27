# =============================================================================
# TrueEntropy - Pool Manager Module
# =============================================================================
#
# This module provides support for multiple isolated entropy pools.
# Each pool operates independently and can be used for different purposes.
#
# Usage:
#     from trueentropy.pools import PoolManager
#
#     manager = PoolManager()
#
#     # Create named pools
#     manager.create("crypto")
#     manager.create("gaming")
#
#     # Use specific pools
#     crypto_random = manager.get("crypto").extract(32)
#     gaming_random = manager.get("gaming").extract(32)
#
# =============================================================================

"""
Pool Manager - manage multiple isolated entropy pools.

This module provides the PoolManager class for creating and managing
multiple EntropyPool instances, each operating independently.
"""

from __future__ import annotations

import threading
from typing import Dict, Iterator, Optional

from trueentropy.pool import EntropyPool
from trueentropy.tap import EntropyTap


class PoolManager:
    """
    Manages multiple isolated entropy pools.
    
    Each pool operates independently with its own state, making it
    suitable for applications that need separate entropy domains
    (e.g., crypto operations vs. gaming randomness).
    
    Attributes:
        pools: Dictionary of named pools
    
    Example:
        >>> manager = PoolManager()
        >>> manager.create("secure", seed=os.urandom(512))
        >>> manager.create("fast")
        >>> 
        >>> secure_bytes = manager.get("secure").extract(32)
        >>> fast_bytes = manager.get("fast").extract(32)
    """
    
    def __init__(self) -> None:
        """Initialize an empty pool manager."""
        self._pools: Dict[str, EntropyPool] = {}
        self._taps: Dict[str, EntropyTap] = {}
        self._lock = threading.Lock()
    
    def create(
        self,
        name: str,
        seed: Optional[bytes] = None,
        replace: bool = False
    ) -> EntropyPool:
        """
        Create a new named entropy pool.
        
        Args:
            name: Unique name for the pool
            seed: Optional initial seed bytes
            replace: If True, replace existing pool with same name
        
        Returns:
            The newly created EntropyPool
        
        Raises:
            ValueError: If pool with name already exists and replace=False
        """
        with self._lock:
            if name in self._pools and not replace:
                raise ValueError(f"Pool '{name}' already exists")
            
            pool = EntropyPool(seed=seed)
            tap = EntropyTap(pool)
            
            self._pools[name] = pool
            self._taps[name] = tap
            
            return pool
    
    def get(self, name: str) -> EntropyPool:
        """
        Get a pool by name.
        
        Args:
            name: Name of the pool
        
        Returns:
            The EntropyPool instance
        
        Raises:
            KeyError: If pool doesn't exist
        """
        with self._lock:
            if name not in self._pools:
                raise KeyError(f"Pool '{name}' not found")
            return self._pools[name]
    
    def get_tap(self, name: str) -> EntropyTap:
        """
        Get the EntropyTap for a named pool.
        
        Args:
            name: Name of the pool
        
        Returns:
            The EntropyTap instance for the pool
        
        Raises:
            KeyError: If pool doesn't exist
        """
        with self._lock:
            if name not in self._taps:
                raise KeyError(f"Pool '{name}' not found")
            return self._taps[name]
    
    def delete(self, name: str) -> None:
        """
        Delete a pool by name.
        
        Args:
            name: Name of the pool to delete
        
        Raises:
            KeyError: If pool doesn't exist
        """
        with self._lock:
            if name not in self._pools:
                raise KeyError(f"Pool '{name}' not found")
            del self._pools[name]
            del self._taps[name]
    
    def exists(self, name: str) -> bool:
        """Check if a pool with the given name exists."""
        with self._lock:
            return name in self._pools
    
    def list_pools(self) -> list[str]:
        """Get a list of all pool names."""
        with self._lock:
            return list(self._pools.keys())
    
    def __len__(self) -> int:
        """Get the number of managed pools."""
        with self._lock:
            return len(self._pools)
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over pool names."""
        with self._lock:
            return iter(list(self._pools.keys()))
    
    def __contains__(self, name: str) -> bool:
        """Check if a pool exists."""
        return self.exists(name)
    
    def __getitem__(self, name: str) -> EntropyPool:
        """Get a pool by name using indexing syntax."""
        return self.get(name)
    
    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------
    
    def random(self, pool_name: str) -> float:
        """Get a random float from a named pool."""
        return self.get_tap(pool_name).random()
    
    def randint(self, pool_name: str, a: int, b: int) -> int:
        """Get a random int from a named pool."""
        return self.get_tap(pool_name).randint(a, b)
    
    def randbytes(self, pool_name: str, n: int) -> bytes:
        """Get random bytes from a named pool."""
        return self.get_tap(pool_name).randbytes(n)


# =============================================================================
# Global Pool Manager Instance
# =============================================================================

_manager: Optional[PoolManager] = None


def get_manager() -> PoolManager:
    """
    Get the global PoolManager instance.
    
    Creates the manager on first call (lazy initialization).
    
    Returns:
        The global PoolManager instance
    """
    global _manager
    if _manager is None:
        _manager = PoolManager()
    return _manager


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "PoolManager",
    "get_manager",
]
