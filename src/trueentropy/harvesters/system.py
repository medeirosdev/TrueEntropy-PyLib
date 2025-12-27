# =============================================================================
# TrueEntropy - System Harvester
# =============================================================================
#
# This harvester collects entropy from the system state - volatile information
# about the computer's current condition.
#
# Why System State is Random:
# - RAM allocation changes constantly as programs run
# - CPU usage fluctuates with system activity
# - Process counts change as programs start/stop
# - Disk I/O varies with application behavior
#
# Collection Method:
# 1. Sample various system metrics using psutil
# 2. Pack the values into bytes
# 3. The exact values at any microsecond are unpredictable
#
# Entropy Estimate:
# - Conservative: ~4-8 bits per metric
# - The least significant bits of each value are the most random
#
# =============================================================================

"""
System state-based entropy harvester.

Collects entropy from volatile system metrics like RAM usage,
CPU load, process counts, and disk activity.
"""

from __future__ import annotations

import struct
import time

from trueentropy.harvesters.base import BaseHarvester, HarvestResult


class SystemHarvester(BaseHarvester):
    """
    Harvests entropy from system state metrics.

    This harvester samples volatile system information using the psutil
    library. The values change constantly due to:

    - Memory allocation/deallocation
    - CPU scheduling
    - Process creation/termination
    - I/O operations

    Metrics collected:
    - Available RAM (bytes)
    - CPU usage percentage (per-core)
    - Number of running processes
    - System boot time
    - Current timestamp (nanoseconds)

    Example:
        >>> harvester = SystemHarvester()
        >>> result = harvester.collect()
        >>> print(f"Collected {result.entropy_bits} bits from system state")
    """

    # -------------------------------------------------------------------------
    # BaseHarvester Implementation
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return harvester name."""
        return "system"

    def collect(self) -> HarvestResult:
        """
        Collect entropy from system state.

        Process:
        1. Import psutil (if available)
        2. Sample various system metrics
        3. Pack all values into bytes
        4. Estimate entropy based on metric variability

        Returns:
            HarvestResult containing system state entropy
        """
        # Attempt import of psutil
        try:
            import psutil
        except ImportError:
            return HarvestResult(
                data=b"",
                entropy_bits=0,
                source=self.name,
                success=False,
                error="psutil library not available",
            )

        # Collect system metrics
        metrics = self._collect_metrics(psutil)

        # Convert to bytes
        data = self._metrics_to_bytes(metrics)

        # Estimate entropy
        # Each metric contributes roughly 4-8 bits of entropy
        entropy_bits = len(metrics) * 6

        return HarvestResult(data=data, entropy_bits=entropy_bits, source=self.name, success=True)

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _collect_metrics(self, psutil: object) -> list[tuple[str, int | float]]:
        """
        Collect various system metrics.

        Args:
            psutil: The imported psutil module

        Returns:
            List of (metric_name, value) tuples
        """
        import psutil as ps  # For type hints

        metrics: list[tuple[str, int | float]] = []

        # =====================================================================
        # Memory Metrics
        # =====================================================================

        try:
            # Virtual memory statistics
            # available: bytes available for new allocations (very volatile)
            mem = ps.virtual_memory()
            metrics.append(("mem_available", mem.available))
            metrics.append(("mem_used", mem.used))
            metrics.append(("mem_percent", int(mem.percent * 1000)))
        except Exception:
            pass

        try:
            # Swap memory statistics
            swap = ps.swap_memory()
            metrics.append(("swap_used", swap.used))
        except Exception:
            pass

        # =====================================================================
        # CPU Metrics
        # =====================================================================

        try:
            # Per-CPU usage percentages
            # These fluctuate rapidly based on running processes
            cpu_percents = ps.cpu_percent(percpu=True)
            for i, pct in enumerate(cpu_percents):
                # Multiply by 10000 to preserve fractional precision
                metrics.append((f"cpu_{i}", int(pct * 10000)))
        except Exception:
            pass

        try:
            # CPU times (user, system, idle, etc.)
            cpu_times = ps.cpu_times()
            metrics.append(("cpu_user", int(cpu_times.user * 1000000)))
            metrics.append(("cpu_system", int(cpu_times.system * 1000000)))
        except Exception:
            pass

        # =====================================================================
        # Process Metrics
        # =====================================================================

        try:
            # Number of running processes
            # This changes as programs start and stop
            pids = ps.pids()
            metrics.append(("process_count", len(pids)))

            # Sum of first N PIDs as a volatile fingerprint
            # New processes get incrementing PIDs
            pid_sum = sum(pids[:20]) if len(pids) >= 20 else sum(pids)
            metrics.append(("pid_sum", pid_sum))
        except Exception:
            pass

        # =====================================================================
        # Disk Metrics
        # =====================================================================

        try:
            # Disk I/O counters
            # These change with every disk read/write
            disk_io = ps.disk_io_counters()
            if disk_io is not None:
                metrics.append(("disk_read_bytes", disk_io.read_bytes))
                metrics.append(("disk_write_bytes", disk_io.write_bytes))
                metrics.append(("disk_read_count", disk_io.read_count))
                metrics.append(("disk_write_count", disk_io.write_count))
        except Exception:
            pass

        # =====================================================================
        # Network I/O Metrics
        # =====================================================================

        try:
            # Network I/O counters
            net_io = ps.net_io_counters()
            if net_io is not None:
                metrics.append(("net_bytes_sent", net_io.bytes_sent))
                metrics.append(("net_bytes_recv", net_io.bytes_recv))
                metrics.append(("net_packets_sent", net_io.packets_sent))
                metrics.append(("net_packets_recv", net_io.packets_recv))
        except Exception:
            pass

        # =====================================================================
        # Time Metrics
        # =====================================================================

        try:
            # System boot time (constant but adds to mixing)
            boot_time = ps.boot_time()
            metrics.append(("boot_time", int(boot_time * 1000000)))
        except Exception:
            pass

        # Current timestamp with nanosecond precision
        # Always different, adds guaranteed entropy
        metrics.append(("timestamp_ns", time.perf_counter_ns()))
        metrics.append(("time_ns", time.time_ns()))

        return metrics

    def _metrics_to_bytes(self, metrics: list[tuple[str, int | float]]) -> bytes:
        """
        Convert system metrics to bytes.

        We pack each metric as a 64-bit value. Float values are
        first converted to integers by scaling.

        Args:
            metrics: List of (name, value) tuples

        Returns:
            Bytes representation of the metrics
        """
        result = b""

        for _name, value in metrics:
            # Convert to integer if needed
            int_value = int(value * 1000000) if isinstance(value, float) else value

            # Ensure value fits in 64 bits (handle negative values)
            int_value = int_value & 0xFFFFFFFFFFFFFFFF

            # Pack as unsigned 64-bit integer
            result += struct.pack("!Q", int_value)

        return result

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def list_available_metrics(self) -> list[str]:
        """
        List which metrics are available on this system.

        This is useful for debugging and understanding what
        entropy sources are being used.

        Returns:
            List of metric name strings
        """
        try:
            import psutil as ps

            available = []

            try:
                ps.virtual_memory()
                available.extend(["mem_available", "mem_used", "mem_percent"])
            except Exception:
                pass

            try:
                ps.cpu_percent(percpu=True)
                available.append("cpu_percpu")
            except Exception:
                pass

            try:
                ps.pids()
                available.extend(["process_count", "pid_sum"])
            except Exception:
                pass

            try:
                if ps.disk_io_counters() is not None:
                    available.extend(["disk_read", "disk_write"])
            except Exception:
                pass

            try:
                if ps.net_io_counters() is not None:
                    available.extend(["net_bytes", "net_packets"])
            except Exception:
                pass

            available.extend(["timestamp_ns", "time_ns"])

            return available

        except ImportError:
            return ["timestamp_ns", "time_ns"]  # Always available
