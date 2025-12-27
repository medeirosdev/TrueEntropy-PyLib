# =============================================================================
# TrueEntropy - Entropy Tap Module
# =============================================================================
#
# The Tap is the "faucet" that extracts entropy from the pool and converts it
# into usable random values. It provides the interface between the raw pool
# bytes and the friendly random number API.
#
# Key Features:
# - Uniform distribution: All random values are uniformly distributed
# - Bias elimination: Uses rejection sampling for unbiased integer ranges
# - Type conversion: Converts raw bytes to floats, ints, bools, etc.
#
# =============================================================================

"""
Entropy Tap - extracts and formats random values from the pool.

This module provides the EntropyTap class that converts raw pool entropy
into various random value types (float, int, bool, bytes, etc.).
"""

from __future__ import annotations

import struct
from typing import Any, MutableSequence, Sequence, TypeVar

from trueentropy.pool import EntropyPool


# Type variable for generic sequence operations
T = TypeVar("T")


class EntropyTap:
    """
    Extracts and formats random values from an entropy pool.
    
    The tap is responsible for converting raw entropy bytes into
    various formats like floats, integers, and booleans. It ensures
    that all generated values are uniformly distributed.
    
    Example:
        >>> pool = EntropyPool()
        >>> tap = EntropyTap(pool)
        >>> value = tap.random()
        >>> print(f"Random: {value}")
    """
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def __init__(self, pool: EntropyPool) -> None:
        """
        Initialize the tap with an entropy pool.
        
        Args:
            pool: The EntropyPool instance to extract entropy from
        """
        self._pool = pool
    
    # -------------------------------------------------------------------------
    # Random Value Generation
    # -------------------------------------------------------------------------
    
    def random(self) -> float:
        """
        Generate a random float in the range [0.0, 1.0).
        
        Uses 64 bits of entropy to generate a uniformly distributed
        floating-point number. The result is always less than 1.0.
        
        Returns:
            A float value where 0.0 <= value < 1.0
        
        How it works:
            1. Extract 8 bytes (64 bits) from the pool
            2. Interpret as unsigned 64-bit integer
            3. Divide by 2^64 to get value in [0, 1)
        """
        # Extract 8 bytes of entropy
        raw_bytes = self._pool.extract(8)
        
        # Unpack as unsigned 64-bit integer (big-endian)
        # We use big-endian for consistency across platforms
        value = struct.unpack("!Q", raw_bytes)[0]
        
        # Convert to float in range [0.0, 1.0)
        # 2^64 = 18446744073709551616
        return value / 18446744073709551616.0
    
    def randint(self, a: int, b: int) -> int:
        """
        Generate a random integer N such that a <= N <= b.
        
        Uses rejection sampling to ensure uniform distribution.
        This avoids modulo bias that would occur with simple modulo.
        
        Args:
            a: Lower bound (inclusive)
            b: Upper bound (inclusive)
        
        Returns:
            Random integer in [a, b]
        
        Raises:
            ValueError: If a > b
        
        How it works:
            1. Calculate the range size (b - a + 1)
            2. Find the smallest number of bits needed to represent range
            3. Generate random bits and check if value < range
            4. If not, reject and try again (rejection sampling)
            5. This ensures perfectly uniform distribution
        """
        if a > b:
            raise ValueError(f"randint: a ({a}) must be <= b ({b})")
        
        if a == b:
            return a  # Only one possible value
        
        # Calculate range size
        range_size = b - a + 1
        
        # Find number of bits needed to represent range_size
        # We need ceil(log2(range_size)) bits
        bits_needed = (range_size - 1).bit_length()
        bytes_needed = (bits_needed + 7) // 8  # Round up to bytes
        
        # Mask to extract only the bits we need
        # e.g., for range_size=100, bits_needed=7, mask=0x7F (127)
        mask = (1 << bits_needed) - 1
        
        # Rejection sampling loop
        # We keep generating random values until we get one in range
        # Expected number of iterations is < 2 on average
        while True:
            # Extract random bytes
            raw_bytes = self._pool.extract(bytes_needed)
            
            # Pad to 8 bytes for unpacking (big-endian)
            padded = raw_bytes.rjust(8, b"\x00")
            
            # Unpack as unsigned 64-bit integer
            value = struct.unpack("!Q", padded)[0]
            
            # Apply mask to get only needed bits
            value = value & mask
            
            # Check if value is in valid range
            if value < range_size:
                return a + value
    
    def randbool(self) -> bool:
        """
        Generate a random boolean (True or False).
        
        Each value has exactly 50% probability - a fair coin flip.
        
        Returns:
            True or False with equal probability
        
        How it works:
            1. Extract 1 byte from the pool
            2. Check the least significant bit
            3. Return True if bit is 1, False if 0
        """
        # Extract 1 byte of entropy
        raw_byte = self._pool.extract(1)
        
        # Check least significant bit
        return (raw_byte[0] & 1) == 1
    
    def randbytes(self, n: int) -> bytes:
        """
        Generate n random bytes.
        
        Args:
            n: Number of bytes to generate (must be positive)
        
        Returns:
            A bytes object of length n
        
        Raises:
            ValueError: If n is not positive
        """
        if n <= 0:
            raise ValueError(f"randbytes: n ({n}) must be positive")
        
        return self._pool.extract(n)
    
    def choice(self, seq: Sequence[T]) -> T:
        """
        Return a random element from a non-empty sequence.
        
        Each element has equal probability of being selected.
        
        Args:
            seq: A non-empty sequence (list, tuple, string, etc.)
        
        Returns:
            A randomly selected element
        
        Raises:
            IndexError: If the sequence is empty
        """
        if not seq:
            raise IndexError("Cannot choose from an empty sequence")
        
        # Generate random index in valid range
        index = self.randint(0, len(seq) - 1)
        
        return seq[index]
    
    def shuffle(self, seq: MutableSequence[Any]) -> None:
        """
        Shuffle a mutable sequence in-place.
        
        Uses the Fisher-Yates (Knuth) shuffle algorithm, which produces
        a uniformly random permutation.
        
        Args:
            seq: A mutable sequence to shuffle in-place
        
        How it works:
            The Fisher-Yates algorithm:
            1. Start from the last element
            2. Swap it with a random element from index 0 to current
            3. Move to the previous element and repeat
            4. This produces every permutation with equal probability
        """
        n = len(seq)
        
        # Fisher-Yates shuffle
        # We iterate from the end to the beginning
        for i in range(n - 1, 0, -1):
            # Pick random index from [0, i]
            j = self.randint(0, i)
            
            # Swap elements at i and j
            seq[i], seq[j] = seq[j], seq[i]
    
    def sample(self, seq: Sequence[T], k: int) -> list[T]:
        """
        Return a k-length list of unique elements from the sequence.
        
        This implements random sampling without replacement - each
        element can only be selected once.
        
        Args:
            seq: The sequence to sample from
            k: Number of unique elements to select
        
        Returns:
            A list of k unique elements
        
        Raises:
            ValueError: If k > len(seq) or k < 0
        
        How it works:
            We use a modified Fisher-Yates algorithm that only
            shuffles the first k elements, then returns them.
            This is more efficient than shuffling the entire sequence.
        """
        n = len(seq)
        
        if k < 0:
            raise ValueError(f"sample: k ({k}) must be non-negative")
        
        if k > n:
            raise ValueError(
                f"sample: k ({k}) is larger than sequence length ({n})"
            )
        
        if k == 0:
            return []
        
        # Create a copy of the sequence as a list
        # We only need to work with indices, so we create a pool
        pool = list(range(n))
        
        # Partial Fisher-Yates: shuffle only k elements
        result: list[T] = []
        
        for i in range(k):
            # Pick random index from remaining pool
            j = self.randint(i, n - 1)
            
            # Swap to bring selected index to current position
            pool[i], pool[j] = pool[j], pool[i]
            
            # Add the selected element to result
            result.append(seq[pool[i]])
        
        return result
    
    def uniform(self, a: float, b: float) -> float:
        """
        Generate a random float N such that a <= N <= b.
        
        Args:
            a: Lower bound
            b: Upper bound
        
        Returns:
            Random float in [a, b]
        """
        return a + self.random() * (b - a)
    
    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """
        Generate a random float from the Gaussian (normal) distribution.
        
        Uses the Box-Muller transform to convert uniform random numbers
        to normally distributed values.
        
        Args:
            mu: Mean of the distribution (default: 0.0)
            sigma: Standard deviation (default: 1.0)
        
        Returns:
            Random float from N(mu, sigma^2)
        """
        import math
        
        # Box-Muller transform
        # Generate two uniform random values in (0, 1)
        # We need them to be strictly > 0 to avoid log(0)
        u1 = self.random()
        while u1 == 0:
            u1 = self.random()
        
        u2 = self.random()
        
        # Transform to standard normal
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        
        # Scale and shift to desired mean and standard deviation
        return mu + sigma * z0
    
    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    
    def __repr__(self) -> str:
        """Return string representation of the tap."""
        return f"EntropyTap(pool={self._pool!r})"
