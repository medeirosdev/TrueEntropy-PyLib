# =============================================================================
# TrueEntropy - Hybrid Entopy Tap
# =============================================================================
#
# The Hybrid Tap provides a high-performance Pseudo-Random Number Generator (PRNG)
# that is regularly re-seeded with true entropy from the pool.
#
# This architecture combines the best of both worlds:
# 1. Performance: Uses Python's optimized Mersenne Twister (via random.Random)
# 2. Resiliency: Even if sources fail, the PRNG continues to function
# 3. Security: Regular re-seeding prevents long-term predictability
#
# =============================================================================

"""
Hybrid Tap - PRNG seeded by TrueEntropy pool.
"""

from __future__ import annotations

import random
import time
from typing import Any

from trueentropy.pool import EntropyPool
from trueentropy.tap import BaseTap


class HybridTap(BaseTap):
    """
    High-performance PRNG seeded by true entropy.

    This tap uses Python's standard `random.Random` for generation,
    but re-seeds it periodically using entropy extracted from the
    TrueEntropy pool.

    Ideally used for:
    - High-volume simulations
    - Games and UI effects
    - Scenarios where performance < 1ms is critical
    - Resilience against temporary entropy source failures
    """

    def __init__(
        self,
        pool: EntropyPool,
        reseed_interval: float = 60.0,
        reseed_on_init: bool = True,
    ) -> None:
        """
        Initialize the hybrid tap.

        Args:
            pool: The EntropyPool to use for seeding
            reseed_interval: Seconds between automatic re-seeds (default: 60)
            reseed_on_init: Whether to pull seed immediately (default: True)
        """
        self._pool = pool
        self._reseed_interval = reseed_interval
        self._last_reseed_time = 0.0

        # Dedicated PRNG instance to avoid sharing state with global random
        self._prng = random.Random()

        if reseed_on_init:
            self.reseed()

    def reseed(self) -> None:
        """
        Force a re-seed of the internal PRNG from the entropy pool.

        Extracts 32 bytes (256 bits) from the pool to seed the PRNG.
        This operation blocks briefly while extracting from the pool.
        """
        # Extract 32 bytes of high-quality entropy
        seed_data = self._pool.extract(32)

        # Seed the PRNG
        self._prng.seed(seed_data)

        # Update timestamp
        self._last_reseed_time = time.time()

    def _check_reseed(self) -> None:
        """Check if re-seed is needed and perform it if so."""
        if time.time() - self._last_reseed_time > self._reseed_interval:
            self.reseed()

    # -------------------------------------------------------------------------
    # BaseTap Implementation
    # -------------------------------------------------------------------------

    def random(self) -> float:
        """Generate a random float in [0.0, 1.0)."""
        self._check_reseed()
        return self._prng.random()

    def randint(self, a: int, b: int) -> int:
        """Generate a random integer N such that a <= N <= b."""
        self._check_reseed()
        return self._prng.randint(a, b)

    def randbytes(self, n: int) -> bytes:
        """Generate n random bytes."""
        self._check_reseed()
        # random.randbytes was added in Python 3.9
        # For compatibility, we use getrandbits if randbytes is missing (older python 3)
        if hasattr(self._prng, "randbytes"):
            return self._prng.randbytes(n)
        else:
            # Fallback for older python versions
            return self._prng.getrandbits(n * 8).to_bytes(n, "little")

    # -------------------------------------------------------------------------
    # Optimized Overrides
    # -------------------------------------------------------------------------
    # We override these methods because random.Random usually implements them
    # in C for better performance than our generic BaseTap implementation.

    def choice(self, seq: Any) -> Any:
        self._check_reseed()
        return self._prng.choice(seq)

    def shuffle(self, x: Any) -> None:
        self._check_reseed()
        return self._prng.shuffle(x)

    def sample(self, population: Any, k: int, **kwargs) -> list[Any]:
        self._check_reseed()
        # Support 'counts' keyword arg in newer python versions
        return self._prng.sample(population, k, **kwargs)

    def uniform(self, a: float, b: float) -> float:
        self._check_reseed()
        return self._prng.uniform(a, b)

    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        self._check_reseed()
        return self._prng.gauss(mu, sigma)

    def triangular(self, low: float = 0.0, high: float = 1.0, mode: float | None = None) -> float:
        self._check_reseed()
        return self._prng.triangular(low, high, mode)

    def exponential(self, lambd: float = 1.0) -> float:
        self._check_reseed()
        return self._prng.expovariate(lambd)
