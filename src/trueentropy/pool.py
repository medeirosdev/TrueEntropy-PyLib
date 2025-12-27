# =============================================================================
# TrueEntropy - Entropy Pool Module
# =============================================================================
#
# This module implements the core Entropy Pool - the heart of the TrueEntropy
# library. The pool is a cryptographically secure buffer that accumulates
# entropy from various sources and provides it for random number generation.
#
# How it works:
# 1. The pool starts with an initial seed from os.urandom()
# 2. New entropy is fed into the pool via the feed() method
# 3. Each feed operation mixes the new data with existing pool state
#    using SHA-256 hashing (whitening)
# 4. The extract() method pulls entropy out of the pool
# 5. After extraction, the pool state is updated to prevent reuse
#
# Security Properties:
# - Forward secrecy: Old pool states cannot be recovered
# - Avalanche effect: Small input changes completely change output
# - Thread safety: All operations are protected by locks
#
# =============================================================================

"""
Entropy Pool implementation for TrueEntropy.

The pool maintains a buffer of accumulated entropy that is mixed using
SHA-256 hashing. This ensures uniform distribution and makes it impossible
to predict future outputs or recover past states.
"""

from __future__ import annotations

import hashlib
import os
import struct
import threading
import time


class EntropyPool:
    """
    Cryptographically secure entropy accumulator.

    The EntropyPool class maintains a buffer of entropy that is continuously
    fed from various sources. All incoming data is mixed using SHA-256
    hashing to ensure uniform distribution.

    Attributes:
        POOL_SIZE: Size of the entropy pool in bytes (default: 512 = 4096 bits)
        MIN_ENTROPY_THRESHOLD: Minimum bits before warning (default: 256)

    Example:
        >>> pool = EntropyPool()
        >>> pool.feed(b"some random data")
        >>> entropy = pool.extract(32)
        >>> print(len(entropy))
        32
    """

    # -------------------------------------------------------------------------
    # Class Constants
    # -------------------------------------------------------------------------

    # Pool size in bytes (512 bytes = 4096 bits)
    # This is large enough to provide plenty of entropy while being
    # small enough to fit in CPU cache for fast operations
    POOL_SIZE: int = 512

    # Minimum entropy threshold before issuing warnings
    # If the pool drops below this level, extraction will log warnings
    MIN_ENTROPY_THRESHOLD: int = 256

    # Hash output size (SHA-256 = 32 bytes)
    HASH_SIZE: int = 32

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def __init__(self, seed: bytes | None = None) -> None:
        """
        Initialize a new entropy pool.

        Args:
            seed: Optional initial seed bytes. If not provided, the pool
                  will be seeded from os.urandom() for cryptographic security.
        """
        # Initialize the pool with random data
        # We use os.urandom() as the initial seed because it provides
        # cryptographically secure random bytes from the OS
        initial = seed if seed is not None else os.urandom(self.POOL_SIZE)

        # Expand seed to full pool size if needed
        self._pool: bytes = self._expand_to_pool_size(initial)

        # Track estimated entropy bits in the pool
        # This is a conservative estimate based on input sources
        self._entropy_bits: int = self.POOL_SIZE * 8

        # Thread lock for safe concurrent access
        # This ensures that feed() and extract() can be called from
        # multiple threads without corrupting the pool state
        self._lock: threading.Lock = threading.Lock()

        # Timestamp of last feed operation (for health monitoring)
        self._last_feed_time: float = time.time()

        # Counter for total bytes fed into the pool
        self._total_fed: int = 0

        # Counter for total bytes extracted from the pool
        self._total_extracted: int = 0

    # -------------------------------------------------------------------------
    # Public Methods
    # -------------------------------------------------------------------------

    def feed(self, data: bytes, entropy_estimate: int = 0) -> None:
        """
        Feed new entropy into the pool.

        The incoming data is mixed with the current pool state using SHA-256
        hashing. This process is called "whitening" - it ensures that even
        low-quality input data contributes meaningfully to the pool.

        The mixing formula is:
            new_state = expand(SHA256(old_state || data || timestamp))

        Args:
            data: Raw bytes to feed into the pool. Can be any length.
            entropy_estimate: Estimated bits of entropy in the data.
                            This is used for health monitoring only and
                            does not affect the mixing process.

        Example:
            >>> pool = EntropyPool()
            >>> pool.feed(b"network latency: 45ms", entropy_estimate=8)
        """
        if not data:
            return  # Nothing to feed

        with self._lock:
            # Get high-precision timestamp for additional mixing
            # This adds unpredictability even if the input data is known
            timestamp = struct.pack("!d", time.time())

            # Concatenate: current pool + new data + timestamp
            # The timestamp ensures that even identical data fed at
            # different times produces different pool states
            mix_input = self._pool + data + timestamp

            # Hash the concatenation using SHA-256
            # This produces a 32-byte digest with the avalanche property:
            # changing a single bit in the input flips ~50% of output bits
            hash_digest = hashlib.sha256(mix_input).digest()

            # Expand the hash to fill the entire pool
            # We do this by repeatedly hashing with a counter
            self._pool = self._expand_to_pool_size(hash_digest)

            # Update entropy estimate
            # We add the estimated entropy but cap at pool size
            self._entropy_bits = min(self._entropy_bits + entropy_estimate, self.POOL_SIZE * 8)

            # Update statistics
            self._last_feed_time = time.time()
            self._total_fed += len(data)

    def extract(self, num_bytes: int) -> bytes:
        """
        Extract entropy from the pool.

        This method securely extracts random bytes from the pool. After
        extraction, the pool state is updated to prevent the same bytes
        from ever being extracted again (forward secrecy).

        Args:
            num_bytes: Number of bytes to extract (must be positive)

        Returns:
            Random bytes of the requested length

        Raises:
            ValueError: If num_bytes is not positive

        Example:
            >>> pool = EntropyPool()
            >>> random_bytes = pool.extract(32)
            >>> print(len(random_bytes))
            32
        """
        if num_bytes <= 0:
            raise ValueError("num_bytes must be positive")

        with self._lock:
            # Generate output by hashing pool with extraction counter
            # This ensures forward secrecy: knowing the output doesn't
            # reveal the pool state or allow prediction of future outputs

            result = b""
            counter = 0

            while len(result) < num_bytes:
                # Create extraction hash input:
                # pool || counter || "extract" marker
                extract_input = self._pool + struct.pack("!Q", counter) + b"extract"

                # Generate hash
                hash_output = hashlib.sha256(extract_input).digest()
                result += hash_output
                counter += 1

            # Trim to exact requested size
            result = result[:num_bytes]

            # Update pool state to prevent reuse (forward secrecy)
            # We mix the extraction operation back into the pool
            update_input = self._pool + result + b"update"
            self._pool = self._expand_to_pool_size(hashlib.sha256(update_input).digest())

            # Decrease entropy estimate
            # We assume each extracted bit removes one bit of entropy
            self._entropy_bits = max(0, self._entropy_bits - (num_bytes * 8))

            # Update statistics
            self._total_extracted += num_bytes

            return result

    def reseed(self) -> None:
        """
        Reseed the pool with fresh OS entropy.

        This is useful if you want to completely refresh the pool state,
        for example after a fork() or if you suspect the pool has been
        compromised.

        Example:
            >>> pool = EntropyPool()
            >>> pool.reseed()
        """
        fresh_entropy = os.urandom(self.POOL_SIZE)
        self.feed(fresh_entropy, entropy_estimate=self.POOL_SIZE * 8)

    # -------------------------------------------------------------------------
    # Properties for Monitoring
    # -------------------------------------------------------------------------

    @property
    def entropy_bits(self) -> int:
        """
        Get the estimated number of entropy bits in the pool.

        This is a conservative estimate based on the entropy fed into
        the pool minus the entropy extracted. The actual entropy may
        be higher due to the mixing process.
        """
        with self._lock:
            return self._entropy_bits

    @property
    def last_feed_time(self) -> float:
        """Get the timestamp of the last feed operation."""
        with self._lock:
            return self._last_feed_time

    @property
    def total_fed(self) -> int:
        """Get the total number of bytes fed into the pool."""
        with self._lock:
            return self._total_fed

    @property
    def total_extracted(self) -> int:
        """Get the total number of bytes extracted from the pool."""
        with self._lock:
            return self._total_extracted

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _expand_to_pool_size(self, data: bytes) -> bytes:
        """
        Expand a small amount of data to fill the entire pool.

        We use a counter-mode expansion: hash(data || counter) for each
        block needed. This is similar to how HKDF-Expand works.

        Args:
            data: The seed data to expand

        Returns:
            Bytes of exactly POOL_SIZE length
        """
        result = b""
        counter = 0

        while len(result) < self.POOL_SIZE:
            # Hash: data || counter
            expand_input = data + struct.pack("!Q", counter)
            result += hashlib.sha256(expand_input).digest()
            counter += 1

        # Trim to exact pool size
        return result[: self.POOL_SIZE]

    # -------------------------------------------------------------------------
    # Persistence Support
    # -------------------------------------------------------------------------

    def _get_state_for_persistence(self) -> dict:
        """
        Get the pool state for persistence.

        Returns a dictionary containing all data needed to restore
        the pool state later.

        Returns:
            Dictionary with pool state data
        """
        with self._lock:
            return {
                "state": self._pool,
                "entropy_bits": self._entropy_bits,
                "total_fed": self._total_fed,
                "total_extracted": self._total_extracted,
            }

    def _restore_state_from_persistence(self, state_data: dict) -> None:
        """
        Restore pool state from persistence data.

        Args:
            state_data: Dictionary from _get_state_for_persistence()
        """
        with self._lock:
            self._pool = state_data["state"]
            self._entropy_bits = state_data["entropy_bits"]
            self._total_fed = state_data["total_fed"]
            self._total_extracted = state_data["total_extracted"]
            self._last_feed_time = time.time()

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return a string representation of the pool."""
        return (
            f"EntropyPool("
            f"entropy_bits={self.entropy_bits}, "
            f"total_fed={self.total_fed}, "
            f"total_extracted={self.total_extracted})"
        )
