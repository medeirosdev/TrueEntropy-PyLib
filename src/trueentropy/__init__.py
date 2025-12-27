# =============================================================================
# TrueEntropy - True Randomness from Real-World Entropy Sources
# =============================================================================
#
# This is the main public API for the TrueEntropy library.
# It provides a simple interface for generating random numbers using
# entropy collected from various real-world sources.
#
# The library works by:
# 1. Collecting entropy from multiple sources (timing, network, system, APIs)
# 2. Mixing the entropy using SHA-256 cryptographic hashing
# 3. Storing the mixed entropy in a secure pool
# 4. Extracting random values from the pool on demand
#
# Example usage:
#     import trueentropy
#
#     # Generate random values
#     value = trueentropy.random()        # float [0.0, 1.0)
#     number = trueentropy.randint(1, 10) # integer [1, 10]
#     coin = trueentropy.randbool()       # True or False
#
#     # Check entropy health
#     health = trueentropy.health()
#     print(f"Entropy score: {health['score']}/100")
#
# =============================================================================

"""
TrueEntropy - True randomness from real-world entropy sources.

This library harvests chaos from the physical world to generate truly random
numbers. Unlike pseudo-random number generators (PRNGs) that use deterministic
algorithms, TrueEntropy collects entropy from CPU timing jitter, network
latency, system state, and external APIs.
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# Version Information
# -----------------------------------------------------------------------------
__version__ = "0.1.0"
__author__ = "TrueEntropy Contributors"
__license__ = "MIT"

# -----------------------------------------------------------------------------
# Type Imports (for type hints)
# -----------------------------------------------------------------------------
from typing import TYPE_CHECKING, Any, MutableSequence, Sequence, TypeVar

if TYPE_CHECKING:
    pass

# -----------------------------------------------------------------------------
# Internal Module Imports
# -----------------------------------------------------------------------------
from trueentropy.pool import EntropyPool
from trueentropy.tap import EntropyTap
from trueentropy.health import entropy_health, HealthStatus

# -----------------------------------------------------------------------------
# Type Variables for Generic Functions
# -----------------------------------------------------------------------------
T = TypeVar("T")

# -----------------------------------------------------------------------------
# Global Singleton Instances
# -----------------------------------------------------------------------------
# We maintain a single global entropy pool and tap for convenience.
# Users can also create their own instances if needed.

_pool: EntropyPool = EntropyPool()
_tap: EntropyTap = EntropyTap(_pool)

# Flag to track if background collector is running
_collector_running: bool = False


# =============================================================================
# PUBLIC API - Random Value Generation
# =============================================================================


def random() -> float:
    """
    Generate a random floating-point number in the range [0.0, 1.0).
    
    This function extracts entropy from the pool and converts it to a
    uniformly distributed float. The distribution is uniform, meaning
    all values in the range are equally likely.
    
    Returns:
        A float value where 0.0 <= value < 1.0
    
    Example:
        >>> import trueentropy
        >>> value = trueentropy.random()
        >>> print(f"Random value: {value}")
        Random value: 0.7234891623...
    """
    return _tap.random()


def randint(a: int, b: int) -> int:
    """
    Generate a random integer N such that a <= N <= b.
    
    Both endpoints are inclusive. The distribution is uniform.
    
    Args:
        a: The lower bound (inclusive)
        b: The upper bound (inclusive)
    
    Returns:
        A random integer in the range [a, b]
    
    Raises:
        ValueError: If a > b
    
    Example:
        >>> import trueentropy
        >>> dice = trueentropy.randint(1, 6)
        >>> print(f"Dice roll: {dice}")
        Dice roll: 4
    """
    return _tap.randint(a, b)


def randbool() -> bool:
    """
    Generate a random boolean value (True or False).
    
    This is equivalent to a fair coin flip. Each outcome has
    exactly 50% probability.
    
    Returns:
        True or False with equal probability
    
    Example:
        >>> import trueentropy
        >>> coin = trueentropy.randbool()
        >>> print("Heads" if coin else "Tails")
        Heads
    """
    return _tap.randbool()


def choice(seq: Sequence[T]) -> T:
    """
    Return a random element from a non-empty sequence.
    
    Each element has an equal probability of being selected.
    
    Args:
        seq: A non-empty sequence (list, tuple, string, etc.)
    
    Returns:
        A randomly selected element from the sequence
    
    Raises:
        IndexError: If the sequence is empty
    
    Example:
        >>> import trueentropy
        >>> colors = ["red", "green", "blue"]
        >>> color = trueentropy.choice(colors)
        >>> print(f"Selected: {color}")
        Selected: green
    """
    return _tap.choice(seq)


def randbytes(n: int) -> bytes:
    """
    Generate n random bytes.
    
    This function extracts raw entropy from the pool and returns it
    as a bytes object. Useful for generating cryptographic keys,
    tokens, or other binary data.
    
    Args:
        n: The number of bytes to generate (must be positive)
    
    Returns:
        A bytes object of length n
    
    Raises:
        ValueError: If n is not positive
    
    Example:
        >>> import trueentropy
        >>> secret = trueentropy.randbytes(32)
        >>> print(f"Secret: {secret.hex()}")
        Secret: a1b2c3d4e5f6...
    """
    return _tap.randbytes(n)


def shuffle(seq: MutableSequence[Any]) -> None:
    """
    Shuffle a mutable sequence in-place.
    
    Uses the Fisher-Yates shuffle algorithm with true random numbers
    to ensure a uniform distribution of permutations.
    
    Args:
        seq: A mutable sequence (list) to shuffle in-place
    
    Example:
        >>> import trueentropy
        >>> cards = list(range(1, 53))
        >>> trueentropy.shuffle(cards)
        >>> print(cards[:5])
        [32, 7, 45, 12, 28]
    """
    _tap.shuffle(seq)


def sample(seq: Sequence[T], k: int) -> list[T]:
    """
    Return a k-length list of unique elements from the sequence.
    
    Used for random sampling without replacement.
    
    Args:
        seq: A sequence to sample from
        k: Number of unique elements to select
    
    Returns:
        A list of k unique elements from the sequence
    
    Raises:
        ValueError: If k is larger than the sequence length
    
    Example:
        >>> import trueentropy
        >>> lottery = trueentropy.sample(range(1, 61), 6)
        >>> print(f"Winning numbers: {lottery}")
        Winning numbers: [42, 7, 23, 56, 11, 39]
    """
    return _tap.sample(seq, k)


# =============================================================================
# PUBLIC API - Entropy Management
# =============================================================================


def health() -> HealthStatus:
    """
    Get the current health status of the entropy pool.
    
    Returns a dictionary containing:
    - score: 0-100 indicating entropy quality
    - status: "healthy", "degraded", or "critical"
    - entropy_bits: Estimated bits of entropy in the pool
    - recommendation: Suggested action if health is low
    
    Returns:
        A HealthStatus TypedDict with pool health information
    
    Example:
        >>> import trueentropy
        >>> status = trueentropy.health()
        >>> print(f"Health: {status['score']}/100 ({status['status']})")
        Health: 85/100 (healthy)
    """
    return entropy_health(_pool)


def feed(data: bytes) -> None:
    """
    Manually feed entropy into the pool.
    
    This allows you to add your own entropy sources to the pool.
    The data will be mixed using SHA-256 hashing to ensure it
    properly contributes to the pool state.
    
    Args:
        data: Raw bytes to add to the entropy pool
    
    Example:
        >>> import trueentropy
        >>> # Add some external entropy (e.g., from a hardware RNG)
        >>> external_entropy = b'\\x12\\x34\\x56\\x78'
        >>> trueentropy.feed(external_entropy)
    """
    _pool.feed(data)


def start_collector(interval: float = 1.0) -> None:
    """
    Start the background entropy collector thread.
    
    When running, the collector periodically harvests entropy from
    all available sources and feeds it into the pool. This ensures
    the pool stays full even during heavy random number generation.
    
    Args:
        interval: Seconds between collection cycles (default: 1.0)
    
    Example:
        >>> import trueentropy
        >>> trueentropy.start_collector(interval=2.0)
        >>> # ... application runs ...
        >>> trueentropy.stop_collector()
    """
    global _collector_running
    
    if _collector_running:
        return  # Already running
    
    from trueentropy.collector import start_background_collector
    start_background_collector(_pool, interval)
    _collector_running = True


def stop_collector() -> None:
    """
    Stop the background entropy collector thread.
    
    Call this before your application exits to cleanly shut down
    the collector thread.
    
    Example:
        >>> import trueentropy
        >>> trueentropy.stop_collector()
    """
    global _collector_running
    
    if not _collector_running:
        return  # Not running
    
    from trueentropy.collector import stop_background_collector
    stop_background_collector()
    _collector_running = False


# =============================================================================
# PUBLIC API - Advanced Usage
# =============================================================================


def get_pool() -> EntropyPool:
    """
    Get the global entropy pool instance.
    
    This is useful for advanced users who want to inspect or
    manipulate the pool directly.
    
    Returns:
        The global EntropyPool instance
    """
    return _pool


def get_tap() -> EntropyTap:
    """
    Get the global entropy tap instance.
    
    This is useful for advanced users who want to use the tap
    directly or create their own tap with custom settings.
    
    Returns:
        The global EntropyTap instance
    """
    return _tap


# =============================================================================
# Module Exports
# =============================================================================
# Define what gets exported when using "from trueentropy import *"

__all__ = [
    # Version info
    "__version__",
    # Random value generation
    "random",
    "randint",
    "randbool",
    "choice",
    "randbytes",
    "shuffle",
    "sample",
    # Entropy management
    "health",
    "feed",
    "start_collector",
    "stop_collector",
    # Advanced usage
    "get_pool",
    "get_tap",
    # Classes (for type hints and advanced usage)
    "EntropyPool",
    "EntropyTap",
    "HealthStatus",
]
