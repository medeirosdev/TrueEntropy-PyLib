import time
from unittest.mock import patch

import trueentropy
from trueentropy.config import configure, reset_config
from trueentropy.hybrid import HybridTap
from trueentropy.pool import EntropyPool
from trueentropy.tap import EntropyTap


class TestHybridTap:

    def test_initial_reseed(self):
        """Test that HybridTap reseeds on initialization."""
        pool = EntropyPool()
        # Mock extract to verifying it's called
        with patch.object(pool, "extract", wraps=pool.extract) as mock_extract:
            tap = HybridTap(pool, reseed_on_init=True)
            mock_extract.assert_called_with(32)

            # Verify tap works
            assert 0.0 <= tap.random() < 1.0

    def test_manual_reseed(self):
        """Test manual reseeding."""
        pool = EntropyPool()
        tap = HybridTap(pool)

        with patch.object(pool, "extract", wraps=pool.extract) as mock_extract:
            tap.reseed()
            mock_extract.assert_called_with(32)

    def test_auto_reseed_on_time(self):
        """Test that tap reseeds after interval calls."""
        pool = EntropyPool()
        interval = 0.1
        tap = HybridTap(pool, reseed_interval=interval)

        # Initial access
        tap.random()
        last_reseed = tap._last_reseed_time

        # Access immediately - should NOT reseed
        tap.random()
        assert tap._last_reseed_time == last_reseed

        # Wait for interval
        time.sleep(interval + 0.05)

        # Access again - SHOULD reseed
        tap.random()
        assert tap._last_reseed_time > last_reseed

    def test_random_methods(self):
        """Test that all random methods work and delegate to internal PRNG."""
        pool = EntropyPool()
        tap = HybridTap(pool)

        assert isinstance(tap.random(), float)
        assert isinstance(tap.randint(1, 10), int)
        assert len(tap.randbytes(10)) == 10
        assert tap.choice([1, 2, 3]) in [1, 2, 3]

        seq = [1, 2, 3]
        tap.shuffle(seq)
        assert len(seq) == 3

        sample = tap.sample([1, 2, 3, 4], 2)
        assert len(sample) == 2
        assert len(set(sample)) == 2  # Unique

    def test_performance_comparison(self):
        """Verify that HybridTap is faster than EntropyTap (sanity check)."""
        pool = EntropyPool()
        direct_tap = EntropyTap(pool)
        hybrid_tap = HybridTap(pool)

        # Measure 1000 calls
        start = time.perf_counter()
        for _ in range(1000):
            direct_tap.random()
        direct_duration = time.perf_counter() - start

        start = time.perf_counter()
        for _ in range(1000):
            hybrid_tap.random()
        hybrid_duration = time.perf_counter() - start

        # Hybrid should be significantly faster
        # (Though with 1000 calls it might be noise, but typically it's 10x-100x faster)
        # We assert simple faster, if it fails due to noise, we might need more samples
        # but let's be conservative.
        assert (
            hybrid_duration < direct_duration
        ), f"Hybrid ({hybrid_duration:.5f}s) should be faster than Direct ({direct_duration:.5f}s)"


class TestHybridConfig:

    def setup_method(self):
        """Reset config before each test."""
        reset_config()
        # Reset global tap to default
        configure(mode="DIRECT")

    def teardown_method(self):
        reset_config()
        configure(mode="DIRECT")

    def test_switch_modes(self):
        """Test switching between DIRECT and HYBRID modes."""
        # Default is DIRECT
        assert isinstance(trueentropy.get_tap(), EntropyTap)

        # Switch to HYBRID
        trueentropy.configure(mode="HYBRID")
        tap = trueentropy.get_tap()
        assert isinstance(tap, HybridTap)
        # Verify default interval
        assert tap._reseed_interval == 60.0

        # Switch back to DIRECT
        trueentropy.configure(mode="DIRECT")
        assert isinstance(trueentropy.get_tap(), EntropyTap)

    def test_hybrid_config_params(self):
        """Test configuring hybrid params."""
        trueentropy.configure(mode="HYBRID", hybrid_reseed_interval=123.4)
        tap = trueentropy.get_tap()
        assert isinstance(tap, HybridTap)
        assert tap._reseed_interval == 123.4

        # Test update interval only
        trueentropy.configure(hybrid_reseed_interval=456.7)
        tap = trueentropy.get_tap()
        assert tap._reseed_interval == 456.7
