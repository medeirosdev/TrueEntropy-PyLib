# =============================================================================
# TrueEntropy - Timing Harvester
# =============================================================================
#
# This harvester collects entropy from CPU timing jitter - the unpredictable
# variations in how long code takes to execute.
#
# Why Timing is Random:
# - The OS scheduler interrupts processes unpredictably
# - Cache hits/misses vary based on system state
# - CPU frequency may fluctuate (power management)
# - Other processes compete for resources
#
# Collection Method:
# 1. Run a simple operation multiple times
# 2. Measure the time for each iteration using high-precision counter
# 3. The nanosecond-level variations are our entropy
#
# Entropy Estimate:
# - Conservative: ~2-4 bits per timing sample
# - We collect many samples and use the least significant bits
#
# =============================================================================

"""
Timing-based entropy harvester.

Collects entropy from CPU timing jitter by measuring the execution
time of simple operations at nanosecond precision.
"""

from __future__ import annotations

import struct
import time

from trueentropy.harvesters.base import BaseHarvester, HarvestResult


class TimingHarvester(BaseHarvester):
    """
    Harvests entropy from CPU timing jitter.

    This harvester measures the execution time of simple operations
    using a high-precision timer. The nanosecond-level variations
    come from:

    - OS scheduler interrupts
    - Cache effects
    - CPU frequency scaling
    - Other system activity

    Attributes:
        num_samples: Number of timing samples to collect (default: 64)
        operation_size: Size of list operation for each sample (default: 10)

    Example:
        >>> harvester = TimingHarvester()
        >>> result = harvester.collect()
        >>> print(f"Collected {len(result.data)} bytes, "
        ...       f"estimated {result.entropy_bits} bits")
    """

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    def __init__(self, num_samples: int = 64, operation_size: int = 10) -> None:
        """
        Initialize the timing harvester.

        Args:
            num_samples: Number of timing measurements to collect.
                        More samples = more entropy but slower.
            operation_size: Size of the list created in each timing operation.
                           Affects timing variability.
        """
        self._num_samples = num_samples
        self._operation_size = operation_size

    # -------------------------------------------------------------------------
    # BaseHarvester Implementation
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return harvester name."""
        return "timing"

    def collect(self) -> HarvestResult:
        """
        Collect entropy from timing jitter.

        Process:
        1. Run self._num_samples timing measurements
        2. Each measurement times a simple list creation operation
        3. Collect the nanosecond-precision timestamps
        4. Pack the timing deltas into bytes
        5. Extract the most variable bits for entropy

        Returns:
            HarvestResult containing timing entropy
        """
        # Collect timing samples
        timing_samples = self._collect_timing_samples()

        # Convert samples to bytes
        # We use the full nanosecond values for maximum entropy
        data = self._samples_to_bytes(timing_samples)

        # Estimate entropy
        # Conservative: 2 bits per sample (the jitter is in least sig bits)
        entropy_bits = self._num_samples * 2

        return HarvestResult(data=data, entropy_bits=entropy_bits, source=self.name, success=True)

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _collect_timing_samples(self) -> list[int]:
        """
        Collect timing samples using high-precision counter.

        We measure the time to perform a simple operation (creating a list)
        at nanosecond precision. The variations come from:
        - CPU scheduling
        - Memory allocation
        - Cache behavior
        - System load

        Returns:
            List of timing deltas in nanoseconds
        """
        samples: list[int] = []

        for _ in range(self._num_samples):
            # Record start time with nanosecond precision
            # time.perf_counter_ns() is the highest resolution timer available
            start = time.perf_counter_ns()

            # Perform a simple operation
            # Creating a list involves memory allocation which varies
            _ = [None] * self._operation_size

            # Record end time
            end = time.perf_counter_ns()

            # Store the delta (execution time)
            samples.append(end - start)

        return samples

    def _samples_to_bytes(self, samples: list[int]) -> bytes:
        """
        Convert timing samples to a bytes object.

        We pack each timing value as an unsigned 64-bit integer.
        This preserves all the information in the samples.

        Args:
            samples: List of timing values in nanoseconds

        Returns:
            Bytes representation of the samples
        """
        # Pack as unsigned 64-bit integers (big-endian)
        # Each sample is 8 bytes, so total is num_samples * 8 bytes
        return struct.pack(f"!{len(samples)}Q", *samples)

    # -------------------------------------------------------------------------
    # Configuration Properties
    # -------------------------------------------------------------------------

    @property
    def num_samples(self) -> int:
        """Get the number of samples collected per harvest."""
        return self._num_samples

    @num_samples.setter
    def num_samples(self, value: int) -> None:
        """Set the number of samples."""
        if value < 1:
            raise ValueError("num_samples must be at least 1")
        self._num_samples = value
