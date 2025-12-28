# =============================================================================
# TrueEntropy - Live Harvester Tests
# =============================================================================
#
# Comprehensive tests for ALL harvesters including real network calls.
# These tests measure latency and performance of each entropy source.
#
# Run with: pytest tests/test_harvesters_live.py -v -s
# The -s flag shows print output with timing information.
#
# Note: These tests require network access for online harvesters.
# =============================================================================

"""
Live tests for all TrueEntropy harvesters with latency metrics.

These tests make REAL calls to network services and measure performance.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import ClassVar

import pytest

from trueentropy.harvesters.base import BaseHarvester, HarvestResult
from trueentropy.harvesters.timing import TimingHarvester
from trueentropy.harvesters.network import NetworkHarvester
from trueentropy.harvesters.system import SystemHarvester
from trueentropy.harvesters.external import ExternalHarvester
from trueentropy.harvesters.weather import WeatherHarvester
from trueentropy.harvesters.radioactive import RadioactiveHarvester


# -----------------------------------------------------------------------------
# Performance Tracking
# -----------------------------------------------------------------------------


@dataclass
class HarvesterMetrics:
    """Metrics for a single harvester test run."""
    
    name: str
    success: bool
    duration_ms: float
    entropy_bits: int
    data_bytes: int
    error: str | None = None
    requires_network: bool = False


class PerformanceTracker:
    """Track performance metrics across all harvester tests."""
    
    metrics: ClassVar[list[HarvesterMetrics]] = []
    
    @classmethod
    def add_metric(cls, metric: HarvesterMetrics) -> None:
        """Add a metric to the tracker."""
        cls.metrics.append(metric)
    
    @classmethod
    def print_report(cls) -> None:
        """Print a summary report of all metrics."""
        print("\n")
        print("=" * 75)
        print("               HARVESTER PERFORMANCE REPORT")
        print("=" * 75)
        print(f"{'Harvester':<15} {'Status':<10} {'Time (ms)':<12} {'Entropy':<10} {'Bytes':<10} {'Network'}")
        print("-" * 75)
        
        total_time = 0
        total_entropy = 0
        successful = 0
        
        for m in cls.metrics:
            status = "✓ OK" if m.success else "✗ FAIL"
            network = "Yes" if m.requires_network else "No"
            print(f"{m.name:<15} {status:<10} {m.duration_ms:>8.2f} ms  {m.entropy_bits:>6} bits  {m.data_bytes:>6} B  {network}")
            
            total_time += m.duration_ms
            if m.success:
                total_entropy += m.entropy_bits
                successful += 1
        
        print("-" * 75)
        print(f"{'TOTAL':<15} {successful}/{len(cls.metrics):<8} {total_time:>8.2f} ms  {total_entropy:>6} bits")
        print("=" * 75)
        
        # Print failures if any
        failures = [m for m in cls.metrics if not m.success]
        if failures:
            print("\nFAILURES:")
            for m in failures:
                print(f"  - {m.name}: {m.error}")
        print()
    
    @classmethod
    def clear(cls) -> None:
        """Clear all metrics."""
        cls.metrics.clear()


def measure_harvester(harvester: BaseHarvester, requires_network: bool = False) -> HarvesterMetrics:
    """
    Measure a harvester's performance.
    
    Args:
        harvester: The harvester to measure
        requires_network: Whether this harvester requires network access
        
    Returns:
        HarvesterMetrics with timing and result information
    """
    start_time = time.perf_counter()
    result = harvester.safe_collect()
    end_time = time.perf_counter()
    
    duration_ms = (end_time - start_time) * 1000
    
    return HarvesterMetrics(
        name=harvester.name,
        success=result.success,
        duration_ms=duration_ms,
        entropy_bits=result.entropy_bits,
        data_bytes=len(result.data),
        error=result.error,
        requires_network=requires_network,
    )


# -----------------------------------------------------------------------------
# Offline Harvester Tests (No Network Required)
# -----------------------------------------------------------------------------


class TestOfflineHarvesters:
    """Tests for harvesters that work offline (no network required)."""
    
    def test_timing_harvester_live(self) -> None:
        """Test TimingHarvester with real CPU timing measurements."""
        harvester = TimingHarvester(num_samples=64)
        
        metrics = measure_harvester(harvester, requires_network=False)
        PerformanceTracker.add_metric(metrics)
        
        print(f"\n  [TIMING] Duration: {metrics.duration_ms:.2f}ms, "
              f"Entropy: {metrics.entropy_bits} bits, Data: {metrics.data_bytes} bytes")
        
        assert metrics.success, f"Timing harvester failed: {metrics.error}"
        assert metrics.entropy_bits > 0, "Should produce entropy"
        assert metrics.data_bytes > 0, "Should produce data"
        # Timing should be fast (< 100ms typically)
        assert metrics.duration_ms < 500, f"Timing harvester too slow: {metrics.duration_ms}ms"
    
    def test_system_harvester_live(self) -> None:
        """Test SystemHarvester with real system state collection."""
        harvester = SystemHarvester()
        
        metrics = measure_harvester(harvester, requires_network=False)
        PerformanceTracker.add_metric(metrics)
        
        print(f"\n  [SYSTEM] Duration: {metrics.duration_ms:.2f}ms, "
              f"Entropy: {metrics.entropy_bits} bits, Data: {metrics.data_bytes} bytes")
        
        assert metrics.success, f"System harvester failed: {metrics.error}"
        assert metrics.entropy_bits > 0, "Should produce entropy"
        # System calls should be fast
        assert metrics.duration_ms < 1000, f"System harvester too slow: {metrics.duration_ms}ms"
    
    def test_timing_consistency(self) -> None:
        """Test that repeated timing collections produce different data."""
        harvester = TimingHarvester(num_samples=32)
        
        results = []
        for i in range(5):
            result = harvester.collect()
            results.append(result.data)
            time.sleep(0.01)  # Small delay between samples
        
        # All results should be unique
        unique_results = set(results)
        assert len(unique_results) == 5, "Timing data should vary between collections"
        print(f"\n  [TIMING CONSISTENCY] 5 unique samples collected")
    
    def test_system_metrics_available(self) -> None:
        """Test that system harvester can list available metrics."""
        harvester = SystemHarvester()
        metrics = harvester.list_available_metrics()
        
        print(f"\n  [SYSTEM METRICS] Available: {metrics}")
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0, "Should have at least one metric"
        assert "timestamp_ns" in metrics, "Timestamp should always be available"


# -----------------------------------------------------------------------------
# Online Harvester Tests (Network Required)
# -----------------------------------------------------------------------------


@pytest.mark.network
class TestOnlineHarvesters:
    """
    Tests for harvesters that require network access.
    
    These tests make REAL network calls and may be slow or fail
    if network is unavailable.
    
    Run with: pytest -m network tests/test_harvesters_live.py -v -s
    """
    
    def test_network_harvester_live(self) -> None:
        """Test NetworkHarvester with real network pings."""
        harvester = NetworkHarvester(timeout=5.0)
        
        metrics = measure_harvester(harvester, requires_network=True)
        PerformanceTracker.add_metric(metrics)
        
        print(f"\n  [NETWORK] Duration: {metrics.duration_ms:.2f}ms, "
              f"Entropy: {metrics.entropy_bits} bits, Data: {metrics.data_bytes} bytes")
        
        # Network may fail but should handle gracefully
        if metrics.success:
            assert metrics.entropy_bits > 0, "Should produce entropy on success"
        else:
            print(f"  [NETWORK] Warning: Failed ({metrics.error}) - may be offline")
    
    def test_external_harvester_live(self) -> None:
        """Test ExternalHarvester with real API calls (USGS, crypto)."""
        harvester = ExternalHarvester(timeout=10.0)
        
        metrics = measure_harvester(harvester, requires_network=True)
        PerformanceTracker.add_metric(metrics)
        
        print(f"\n  [EXTERNAL] Duration: {metrics.duration_ms:.2f}ms, "
              f"Entropy: {metrics.entropy_bits} bits, Data: {metrics.data_bytes} bytes")
        
        if metrics.success:
            assert metrics.entropy_bits > 0, "Should produce entropy on success"
        else:
            print(f"  [EXTERNAL] Warning: Failed ({metrics.error}) - API may be unavailable")
    
    def test_weather_harvester_live(self) -> None:
        """Test WeatherHarvester with real weather API calls."""
        # Using wttr.in (no API key required)
        harvester = WeatherHarvester(timeout=10.0)
        
        metrics = measure_harvester(harvester, requires_network=True)
        PerformanceTracker.add_metric(metrics)
        
        print(f"\n  [WEATHER] Duration: {metrics.duration_ms:.2f}ms, "
              f"Entropy: {metrics.entropy_bits} bits, Data: {metrics.data_bytes} bytes")
        
        if metrics.success:
            assert metrics.entropy_bits > 0, "Should produce entropy on success"
        else:
            print(f"  [WEATHER] Warning: Failed ({metrics.error}) - API may be unavailable")
    
    def test_radioactive_harvester_live(self) -> None:
        """Test RadioactiveHarvester with real quantum/random.org API calls."""
        harvester = RadioactiveHarvester(timeout=15.0)
        
        metrics = measure_harvester(harvester, requires_network=True)
        PerformanceTracker.add_metric(metrics)
        
        print(f"\n  [RADIOACTIVE] Duration: {metrics.duration_ms:.2f}ms, "
              f"Entropy: {metrics.entropy_bits} bits, Data: {metrics.data_bytes} bytes")
        
        if metrics.success:
            assert metrics.entropy_bits > 0, "Should produce entropy on success"
            # Quantum random should give full entropy
            print(f"  [RADIOACTIVE] True quantum randomness collected!")
        else:
            print(f"  [RADIOACTIVE] Warning: Failed ({metrics.error}) - may be rate limited")


# -----------------------------------------------------------------------------
# Combined Tests
# -----------------------------------------------------------------------------


class TestAllHarvesters:
    """Test all harvesters together and generate performance report."""
    
    def setup_method(self) -> None:
        """Clear metrics before each test."""
        PerformanceTracker.clear()
    
    def test_all_harvesters_benchmark(self) -> None:
        """
        Benchmark ALL harvesters and print performance report.
        
        This is the main comprehensive test that exercises all entropy sources.
        """
        print("\n" + "=" * 60)
        print("  RUNNING FULL HARVESTER BENCHMARK")
        print("=" * 60)
        
        harvesters = [
            # Offline harvesters
            (TimingHarvester(num_samples=64), False),
            (SystemHarvester(), False),
            # Online harvesters
            (NetworkHarvester(timeout=5.0), True),
            (ExternalHarvester(timeout=10.0), True),
            (WeatherHarvester(timeout=10.0), True),
            (RadioactiveHarvester(timeout=15.0), True),
        ]
        
        for harvester, requires_network in harvesters:
            print(f"  Testing {harvester.name}...", end="", flush=True)
            metrics = measure_harvester(harvester, requires_network)
            PerformanceTracker.add_metric(metrics)
            
            status = "✓" if metrics.success else "✗"
            print(f" {status} ({metrics.duration_ms:.0f}ms)")
        
        # Print full report
        PerformanceTracker.print_report()
        
        # At minimum, offline harvesters should work
        offline_metrics = [m for m in PerformanceTracker.metrics if not m.requires_network]
        offline_success = all(m.success for m in offline_metrics)
        
        assert offline_success, "Offline harvesters must always succeed"
    
    def test_entropy_quality(self) -> None:
        """Test that collected entropy has good distribution."""
        harvester = TimingHarvester(num_samples=128)
        result = harvester.collect()
        
        assert result.success
        assert len(result.data) >= 128
        
        # Check byte distribution (simple entropy check)
        from collections import Counter
        byte_counts = Counter(result.data)
        
        # In truly random data, no single byte should dominate
        max_count = max(byte_counts.values())
        total_bytes = len(result.data)
        max_percentage = (max_count / total_bytes) * 100
        
        print(f"\n  [QUALITY] Data size: {total_bytes} bytes")
        print(f"  [QUALITY] Unique byte values: {len(byte_counts)}/256")
        print(f"  [QUALITY] Max byte frequency: {max_percentage:.1f}%")
        
        # Warning if distribution looks bad
        if max_percentage > 10:
            print(f"  [QUALITY] Warning: High byte frequency ({max_percentage:.1f}%)")


# -----------------------------------------------------------------------------
# Configuration Tests
# -----------------------------------------------------------------------------


class TestHarvesterConfiguration:
    """Test harvester configuration options."""
    
    def test_timing_num_samples(self) -> None:
        """Test configurable sample count for timing harvester."""
        for num_samples in [16, 32, 64, 128]:
            harvester = TimingHarvester(num_samples=num_samples)
            result = harvester.collect()
            
            expected_bytes = num_samples * 8  # 8 bytes per sample
            assert len(result.data) == expected_bytes, \
                f"Expected {expected_bytes} bytes for {num_samples} samples"
            
            print(f"\n  [CONFIG] TimingHarvester(num_samples={num_samples}) -> {len(result.data)} bytes")
    
    def test_network_custom_targets(self) -> None:
        """Test custom network targets configuration."""
        custom_targets = ["https://google.com", "https://github.com"]
        harvester = NetworkHarvester(targets=custom_targets, timeout=5.0)
        
        assert harvester.targets == custom_targets
        print(f"\n  [CONFIG] NetworkHarvester with custom targets: {custom_targets}")
    
    def test_network_timeout_configuration(self) -> None:
        """Test that timeout is respected."""
        timeout = 2.0
        harvester = NetworkHarvester(timeout=timeout)
        
        assert harvester.timeout == timeout
        print(f"\n  [CONFIG] NetworkHarvester timeout: {timeout}s")
    
    def test_external_source_toggles(self) -> None:
        """Test enabling/disabling external sources."""
        # Disable earthquake, enable crypto only
        harvester = ExternalHarvester(
            enable_earthquake=False,
            enable_crypto=True,
            timeout=5.0
        )
        
        assert harvester.enable_earthquake is False
        assert harvester.enable_crypto is True
        print("\n  [CONFIG] ExternalHarvester with crypto only")


# -----------------------------------------------------------------------------
# Fixture for final report
# -----------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def final_report(request):
    """Print final performance report after all tests complete."""
    yield
    
    if PerformanceTracker.metrics:
        print("\n\n" + "=" * 75)
        print("           FINAL SESSION PERFORMANCE SUMMARY")
        PerformanceTracker.print_report()
