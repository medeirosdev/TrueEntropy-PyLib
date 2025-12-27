# =============================================================================
# TrueEntropy - Network Harvester
# =============================================================================
#
# This harvester collects entropy from network latency - the time it takes
# to communicate with remote servers.
#
# Why Network Latency is Random:
# - Physical distance adds baseline delay
# - Network congestion varies constantly
# - Routing changes dynamically
# - Server load fluctuates
# - Packet collisions and retransmissions
#
# Collection Method:
# 1. Send HEAD requests to multiple reliable servers
# 2. Measure round-trip time with high precision
# 3. The variations in timing are our entropy
#
# Entropy Estimate:
# - Conservative: ~8 bits per successful request
# - Latency varies by milliseconds, with microsecond precision
#
# =============================================================================

"""
Network latency-based entropy harvester.

Collects entropy from the timing variations in network requests
to multiple servers.
"""

from __future__ import annotations

import struct
import time

from trueentropy.harvesters.base import BaseHarvester, HarvestResult


class NetworkHarvester(BaseHarvester):
    """
    Harvests entropy from network latency measurements.

    This harvester makes lightweight HTTP HEAD requests to reliable
    servers and measures the round-trip time. The variations come from:

    - Network congestion
    - Routing changes
    - Server load
    - Physical infrastructure conditions

    Attributes:
        targets: List of URLs to measure latency against
        timeout: Request timeout in seconds

    Example:
        >>> harvester = NetworkHarvester()
        >>> result = harvester.collect()
        >>> print(f"Collected from network: {result.entropy_bits} bits")
    """

    # -------------------------------------------------------------------------
    # Default Target Servers
    # -------------------------------------------------------------------------

    # We use major, reliable services that have high uptime
    # These are chosen for:
    # - Global distribution (geographic diversity)
    # - High reliability (always available)
    # - Fast response times (low baseline latency)

    DEFAULT_TARGETS: list[str] = [
        "https://1.1.1.1",  # Cloudflare DNS
        "https://8.8.8.8",  # Google DNS
        "https://www.google.com",  # Google
        "https://www.cloudflare.com",  # Cloudflare
        "https://www.microsoft.com",  # Microsoft
    ]

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def __init__(self, targets: list[str] | None = None, timeout: float = 2.0) -> None:
        """
        Initialize the network harvester.

        Args:
            targets: List of URLs to measure latency against.
                    If None, uses DEFAULT_TARGETS.
            timeout: Request timeout in seconds (default: 2.0)
        """
        self._targets = targets or self.DEFAULT_TARGETS.copy()
        self._timeout = timeout

    # -------------------------------------------------------------------------
    # BaseHarvester Implementation
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return harvester name."""
        return "network"

    def collect(self) -> HarvestResult:
        """
        Collect entropy from network latency.

        Process:
        1. Make HEAD requests to each target server
        2. Measure round-trip time for each request
        3. Pack timing data into bytes
        4. Return results with entropy estimate

        Note: Failed requests are silently skipped. This harvester
        will still succeed if at least one request completes.

        Returns:
            HarvestResult containing network timing entropy
        """
        # Attempt import of requests library
        try:
            import requests
        except ImportError:
            return HarvestResult(
                data=b"",
                entropy_bits=0,
                source=self.name,
                success=False,
                error="requests library not available",
            )

        # Collect latency measurements
        measurements = self._measure_latencies(requests)

        if not measurements:
            return HarvestResult(
                data=b"",
                entropy_bits=0,
                source=self.name,
                success=False,
                error="No network targets reachable",
            )

        # Convert to bytes
        data = self._measurements_to_bytes(measurements)

        # Estimate entropy: ~8 bits per successful measurement
        # Network latency varies by milliseconds at microsecond precision
        entropy_bits = len(measurements) * 8

        return HarvestResult(data=data, entropy_bits=entropy_bits, source=self.name, success=True)

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _measure_latencies(self, requests_module: object) -> list[tuple[str, int]]:
        """
        Measure latency to each target server.

        Args:
            requests_module: The imported requests module

        Returns:
            List of (target, latency_ns) tuples for successful requests
        """
        import requests  # Type ignore for the module passed in

        measurements: list[tuple[str, int]] = []

        for target in self._targets:
            try:
                # Record start time with nanosecond precision
                start = time.perf_counter_ns()

                # Make a lightweight HEAD request
                # HEAD is faster than GET because it doesn't download the body
                requests.head(target, timeout=self._timeout, allow_redirects=False)

                # Record end time
                end = time.perf_counter_ns()

                # Store the latency
                latency_ns = end - start
                measurements.append((target, latency_ns))

            except requests.RequestException:
                # Skip failed requests silently
                # This is expected for unreachable networks
                pass
            except Exception:
                # Skip any other errors
                pass

        return measurements

    def _measurements_to_bytes(self, measurements: list[tuple[str, int]]) -> bytes:
        """
        Convert latency measurements to bytes.

        We include both the latency values and a hash of the target URLs
        to add diversity to the entropy.

        Args:
            measurements: List of (target, latency_ns) tuples

        Returns:
            Bytes representation of the measurements
        """
        import hashlib

        # Pack latency values as 64-bit integers
        latencies = [m[1] for m in measurements]
        latency_bytes = struct.pack(f"!{len(latencies)}Q", *latencies)

        # Add hash of target URLs for additional entropy
        # This includes which servers responded (order matters)
        targets_str = "|".join(m[0] for m in measurements)
        target_hash = hashlib.sha256(targets_str.encode()).digest()[:8]

        return latency_bytes + target_hash

    # -------------------------------------------------------------------------
    # Configuration Properties
    # -------------------------------------------------------------------------

    @property
    def targets(self) -> list[str]:
        """Get the list of target URLs."""
        return self._targets.copy()

    @targets.setter
    def targets(self, value: list[str]) -> None:
        """Set the list of target URLs."""
        if not value:
            raise ValueError("targets must not be empty")
        self._targets = value.copy()

    @property
    def timeout(self) -> float:
        """Get the request timeout in seconds."""
        return self._timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        """Set the request timeout in seconds."""
        if value <= 0:
            raise ValueError("timeout must be positive")
        self._timeout = value
