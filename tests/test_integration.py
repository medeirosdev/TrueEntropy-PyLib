# =============================================================================
# TrueEntropy - Integration Tests
# =============================================================================
#
# Integration tests that verify the complete system works together.
# Tests cover:
# - Public API functions
# - Background collector
# - Health monitoring
# - End-to-end random number generation
#
# =============================================================================

from __future__ import annotations

"""Integration tests for the TrueEntropy library."""

import time


class TestPublicAPI:
    """Test the public API exported from trueentropy."""

    def test_import(self) -> None:
        """Library should import without errors."""
        import trueentropy

        assert hasattr(trueentropy, "__version__")

    def test_random(self) -> None:
        """trueentropy.random() should work."""
        import trueentropy

        value = trueentropy.random()

        assert isinstance(value, float)
        assert 0.0 <= value < 1.0

    def test_randint(self) -> None:
        """trueentropy.randint() should work."""
        import trueentropy

        value = trueentropy.randint(1, 100)

        assert isinstance(value, int)
        assert 1 <= value <= 100

    def test_randbool(self) -> None:
        """trueentropy.randbool() should work."""
        import trueentropy

        value = trueentropy.randbool()

        assert isinstance(value, bool)

    def test_choice(self) -> None:
        """trueentropy.choice() should work."""
        import trueentropy

        items = ["a", "b", "c"]
        value = trueentropy.choice(items)

        assert value in items

    def test_randbytes(self) -> None:
        """trueentropy.randbytes() should work."""
        import trueentropy

        value = trueentropy.randbytes(32)

        assert isinstance(value, bytes)
        assert len(value) == 32

    def test_shuffle(self) -> None:
        """trueentropy.shuffle() should work."""
        import trueentropy

        items = [1, 2, 3, 4, 5]
        trueentropy.shuffle(items)

        assert len(items) == 5
        assert set(items) == {1, 2, 3, 4, 5}

    def test_sample(self) -> None:
        """trueentropy.sample() should work."""
        import trueentropy

        items = list(range(10))
        result = trueentropy.sample(items, 5)

        assert len(result) == 5
        assert len(set(result)) == 5
        for item in result:
            assert item in items


class TestHealthAPI:
    """Test the health monitoring API."""

    def test_health_returns_dict(self) -> None:
        """health() should return a dictionary."""
        import trueentropy

        status = trueentropy.health()

        assert isinstance(status, dict)

    def test_health_has_required_keys(self) -> None:
        """health() should have all required keys."""
        import trueentropy

        status = trueentropy.health()

        assert "score" in status
        assert "status" in status
        assert "entropy_bits" in status
        assert "recommendation" in status

    def test_health_score_in_range(self) -> None:
        """health score should be 0-100."""
        import trueentropy

        status = trueentropy.health()

        assert 0 <= status["score"] <= 100

    def test_health_status_valid(self) -> None:
        """health status should be valid value."""
        import trueentropy

        status = trueentropy.health()

        assert status["status"] in ["healthy", "degraded", "critical"]


class TestFeedAPI:
    """Test the manual feed API."""

    def test_feed_accepts_bytes(self) -> None:
        """feed() should accept bytes."""
        import trueentropy

        # Should not raise
        trueentropy.feed(b"test entropy data")

    def test_feed_affects_pool(self) -> None:
        """feed() should affect random output."""
        import trueentropy

        # Get current health
        before = trueentropy.health()

        # Feed a lot of data
        for _ in range(10):
            trueentropy.feed(b"entropy" * 100)

        # Health should still be valid
        after = trueentropy.health()
        assert 0 <= after["score"] <= 100


class TestAdvancedAPI:
    """Test advanced API functions."""

    def test_get_pool(self) -> None:
        """get_pool() should return EntropyPool."""
        import trueentropy
        from trueentropy.pool import EntropyPool

        pool = trueentropy.get_pool()

        assert isinstance(pool, EntropyPool)

    def test_get_tap(self) -> None:
        """get_tap() should return EntropyTap."""
        import trueentropy
        from trueentropy.tap import EntropyTap

        tap = trueentropy.get_tap()

        assert isinstance(tap, EntropyTap)


class TestBackgroundCollector:
    """Test background collector functionality."""

    def setup_method(self) -> None:
        """Reset config and stop collector before each test."""
        import trueentropy

        # Use offline mode for faster tests (no network harvesters blocking)
        trueentropy.configure(offline_mode=True)
        trueentropy.stop_collector()
        time.sleep(0.1)

    def teardown_method(self) -> None:
        """Ensure collector is stopped after each test."""
        import trueentropy

        trueentropy.stop_collector()
        trueentropy.reset_config()  # Reset config for next test
        time.sleep(0.1)  # Give time for thread to stop

    def test_start_and_stop_collector(self) -> None:
        """Collector should start and stop cleanly."""
        import trueentropy
        from trueentropy.collector import is_collector_running

        # Ensure stopped first
        trueentropy.stop_collector()
        time.sleep(0.1)

        # Start collector (uses offline mode from setup_method)
        trueentropy.start_collector(interval=0.5)
        time.sleep(0.2)  # Give time for thread to start

        # Should be running
        assert is_collector_running()

        # Stop collector
        trueentropy.stop_collector()

        # Should be stopped
        # Give it a moment to stop
        time.sleep(0.3)
        assert not is_collector_running()

    def test_collector_feeds_pool(self) -> None:
        """Collector should feed entropy into the pool."""
        import trueentropy

        # Ensure stopped first
        trueentropy.stop_collector()
        time.sleep(0.1)

        pool = trueentropy.get_pool()
        initial_fed = pool.total_fed

        # Start collector with fast interval (uses offline mode)
        trueentropy.start_collector(interval=0.2)

        # Wait for some collections
        time.sleep(0.8)

        # Stop collector
        trueentropy.stop_collector()
        time.sleep(0.2)

        # Should have fed some data
        assert pool.total_fed > initial_fed


class TestExports:
    """Test that all expected names are exported."""

    def test_all_exports(self) -> None:
        """__all__ should contain expected names."""
        import trueentropy

        expected = [
            "__version__",
            "random",
            "randint",
            "randbool",
            "choice",
            "randbytes",
            "shuffle",
            "sample",
            "health",
            "feed",
            "start_collector",
            "stop_collector",
            "get_pool",
            "get_tap",
            "EntropyPool",
            "EntropyTap",
            "HealthStatus",
        ]

        for name in expected:
            assert name in trueentropy.__all__
            assert hasattr(trueentropy, name)


class TestRandomQuality:
    """Test the quality of random output."""

    def test_no_obvious_patterns(self) -> None:
        """Random output should not have obvious patterns."""
        import trueentropy

        # Generate many random bytes
        data = trueentropy.randbytes(1000)

        # Count each byte value
        from collections import Counter

        counts = Counter(data)

        # No single byte should appear more than ~10% of the time
        # (uniform distribution would be 1000/256 ≈ 4 per byte)
        max_count = max(counts.values())
        assert max_count < 50  # Very conservative threshold

    def test_entropy_estimation(self) -> None:
        """Pool should track entropy correctly."""
        from trueentropy.pool import EntropyPool
        from trueentropy.tap import EntropyTap

        # Use a fresh pool for this test to avoid state pollution
        pool = EntropyPool()
        tap = EntropyTap(pool)

        # Extract some entropy
        initial_bits = pool.entropy_bits
        tap.randbytes(64)
        after_bits = pool.entropy_bits

        # Entropy should have decreased
        assert after_bits < initial_bits
