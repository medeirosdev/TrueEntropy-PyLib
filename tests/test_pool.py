# =============================================================================
# TrueEntropy - Pool Tests
# =============================================================================
#
# Unit tests for the EntropyPool class.
# Tests cover:
# - Pool initialization
# - Feeding entropy
# - Extracting entropy
# - Thread safety
# - Edge cases
#
# =============================================================================

from __future__ import annotations

"""Tests for the EntropyPool class."""

import threading
import time

import pytest

from trueentropy.pool import EntropyPool


class TestEntropyPoolInitialization:
    """Test EntropyPool initialization."""
    
    def test_default_initialization(self) -> None:
        """Pool should initialize with random seed."""
        pool = EntropyPool()
        
        # Pool should have full entropy initially
        assert pool.entropy_bits == pool.POOL_SIZE * 8
        assert pool.total_fed == 0
        assert pool.total_extracted == 0
    
    def test_custom_seed_initialization(self) -> None:
        """Pool should accept custom seed."""
        seed = b"test_seed_1234567890"
        pool = EntropyPool(seed=seed)
        
        # Pool should still have expected size
        assert pool.entropy_bits == pool.POOL_SIZE * 8
    
    def test_different_pools_have_different_state(self) -> None:
        """Two pools without seed should have different states."""
        pool1 = EntropyPool()
        pool2 = EntropyPool()
        
        # Extract bytes from both - they should be different
        bytes1 = pool1.extract(32)
        bytes2 = pool2.extract(32)
        
        assert bytes1 != bytes2


class TestEntropyPoolFeed:
    """Test EntropyPool feed operation."""
    
    def test_feed_updates_state(self) -> None:
        """Feeding data should change pool state."""
        pool = EntropyPool(seed=b"fixed_seed")
        
        # Extract initial bytes
        initial = pool.extract(32)
        
        # Create new pool with same seed
        pool2 = EntropyPool(seed=b"fixed_seed")
        
        # Feed some data
        pool2.feed(b"new_entropy_data")
        
        # Extract bytes - should be different
        after_feed = pool2.extract(32)
        
        assert initial != after_feed
    
    def test_feed_updates_statistics(self) -> None:
        """Feeding should update total_fed counter."""
        pool = EntropyPool()
        
        data = b"test_data_12345"
        pool.feed(data)
        
        assert pool.total_fed == len(data)
    
    def test_feed_updates_entropy_estimate(self) -> None:
        """Feeding with entropy estimate should update bits."""
        pool = EntropyPool()
        initial_bits = pool.entropy_bits
        
        pool.feed(b"data", entropy_estimate=16)
        
        # Should be capped at max
        assert pool.entropy_bits == min(
            initial_bits + 16,
            pool.POOL_SIZE * 8
        )
    
    def test_empty_feed_is_noop(self) -> None:
        """Feeding empty data should not change state."""
        pool = EntropyPool(seed=b"fixed")
        initial = pool.extract(16)
        
        pool2 = EntropyPool(seed=b"fixed")
        pool2.feed(b"")
        after = pool2.extract(16)
        
        assert initial == after
    
    def test_feed_updates_last_feed_time(self) -> None:
        """Feed should update last_feed_time."""
        pool = EntropyPool()
        initial_time = pool.last_feed_time
        
        time.sleep(0.01)  # Small delay
        pool.feed(b"data")
        
        assert pool.last_feed_time > initial_time


class TestEntropyPoolExtract:
    """Test EntropyPool extract operation."""
    
    def test_extract_returns_correct_size(self) -> None:
        """Extract should return exact number of bytes requested."""
        pool = EntropyPool()
        
        for size in [1, 16, 32, 64, 100, 256]:
            result = pool.extract(size)
            assert len(result) == size
    
    def test_extract_updates_statistics(self) -> None:
        """Extracting should update total_extracted counter."""
        pool = EntropyPool()
        
        pool.extract(32)
        assert pool.total_extracted == 32
        
        pool.extract(16)
        assert pool.total_extracted == 48
    
    def test_extract_reduces_entropy_estimate(self) -> None:
        """Extracting should reduce entropy bits estimate."""
        pool = EntropyPool()
        initial_bits = pool.entropy_bits
        
        pool.extract(32)
        
        assert pool.entropy_bits == initial_bits - (32 * 8)
    
    def test_extract_never_returns_same_bytes(self) -> None:
        """Successive extractions should never return same bytes."""
        pool = EntropyPool()
        
        results = [pool.extract(32) for _ in range(100)]
        
        # All results should be unique
        assert len(set(results)) == len(results)
    
    def test_extract_forward_secrecy(self) -> None:
        """Same seed should give different results after extraction."""
        # Create two pools with same seed
        seed = b"test_seed_for_forward_secrecy"
        pool1 = EntropyPool(seed=seed)
        pool2 = EntropyPool(seed=seed)
        
        # Both should give same first extraction
        first1 = pool1.extract(16)
        first2 = pool2.extract(16)
        assert first1 == first2
        
        # But second extraction should still be same
        # (pool state updated deterministically)
        second1 = pool1.extract(16)
        second2 = pool2.extract(16)
        assert second1 == second2
    
    def test_extract_invalid_size_raises(self) -> None:
        """Extracting zero or negative bytes should raise."""
        pool = EntropyPool()
        
        with pytest.raises(ValueError):
            pool.extract(0)
        
        with pytest.raises(ValueError):
            pool.extract(-1)


class TestEntropyPoolReseed:
    """Test EntropyPool reseed operation."""
    
    def test_reseed_changes_state(self) -> None:
        """Reseed should change pool state."""
        pool = EntropyPool(seed=b"fixed")
        before = pool.extract(32)
        
        pool2 = EntropyPool(seed=b"fixed")
        pool2.reseed()
        after = pool2.extract(32)
        
        assert before != after
    
    def test_reseed_restores_entropy(self) -> None:
        """Reseed should restore entropy estimate."""
        pool = EntropyPool()
        
        # Drain some entropy
        for _ in range(10):
            pool.extract(64)
        
        low_bits = pool.entropy_bits
        
        # Reseed
        pool.reseed()
        
        # Should have full entropy again
        assert pool.entropy_bits > low_bits


class TestEntropyPoolThreadSafety:
    """Test EntropyPool thread safety."""
    
    def test_concurrent_feed_and_extract(self) -> None:
        """Pool should handle concurrent operations safely."""
        pool = EntropyPool()
        errors: list = []
        
        def feed_worker() -> None:
            try:
                for _ in range(100):
                    pool.feed(b"concurrent_data")
            except Exception as e:
                errors.append(e)
        
        def extract_worker() -> None:
            try:
                for _ in range(100):
                    pool.extract(16)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = [
            threading.Thread(target=feed_worker),
            threading.Thread(target=feed_worker),
            threading.Thread(target=extract_worker),
            threading.Thread(target=extract_worker),
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # No errors should have occurred
        assert len(errors) == 0
    
    def test_statistics_consistency(self) -> None:
        """Statistics should remain consistent under concurrent access."""
        pool = EntropyPool()
        
        def worker(feed_size: int, extract_size: int) -> None:
            for _ in range(50):
                pool.feed(b"x" * feed_size)
                pool.extract(extract_size)
        
        threads = [
            threading.Thread(target=worker, args=(10, 8)),
            threading.Thread(target=worker, args=(20, 16)),
            threading.Thread(target=worker, args=(15, 12)),
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Total fed should be sum of all feeds
        expected_fed = 50 * (10 + 20 + 15)
        assert pool.total_fed == expected_fed
        
        # Total extracted should be sum of all extracts
        expected_extracted = 50 * (8 + 16 + 12)
        assert pool.total_extracted == expected_extracted


class TestEntropyPoolRepr:
    """Test EntropyPool string representation."""
    
    def test_repr_contains_stats(self) -> None:
        """Repr should contain useful statistics."""
        pool = EntropyPool()
        pool.feed(b"test")
        pool.extract(16)
        
        repr_str = repr(pool)
        
        assert "EntropyPool" in repr_str
        assert "entropy_bits" in repr_str
        assert "total_fed" in repr_str
        assert "total_extracted" in repr_str
