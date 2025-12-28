# =============================================================================
# TrueEntropy - Tap Tests
# =============================================================================
#
# Unit tests for the EntropyTap class.
# Tests cover:
# - Random float generation
# - Random integer generation
# - Random boolean generation
# - Choice and sample operations
# - Shuffle operation
# - Distribution uniformity
#
# =============================================================================
"""Tests for the EntropyTap class."""

from __future__ import annotations

import math
from collections import Counter

import pytest

from trueentropy.pool import EntropyPool
from trueentropy.tap import EntropyTap


class TestEntropyTapRandom:
    """Test EntropyTap.random() method."""

    def test_random_returns_float(self) -> None:
        """random() should return a float."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        value = tap.random()

        assert isinstance(value, float)

    def test_random_in_range(self) -> None:
        """random() should return values in [0.0, 1.0)."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        for _ in range(1000):
            value = tap.random()
            assert 0.0 <= value < 1.0

    def test_random_distribution(self) -> None:
        """random() should be approximately uniform."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        # Generate samples
        samples = [tap.random() for _ in range(10000)]

        # Check mean is close to 0.5
        mean = sum(samples) / len(samples)
        assert 0.45 < mean < 0.55

        # Check variance is close to 1/12 (uniform distribution)
        variance = sum((x - mean) ** 2 for x in samples) / len(samples)
        expected_variance = 1 / 12
        assert abs(variance - expected_variance) < 0.02


class TestEntropyTapRandint:
    """Test EntropyTap.randint() method."""

    def test_randint_returns_int(self) -> None:
        """randint() should return an integer."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        value = tap.randint(1, 10)

        assert isinstance(value, int)

    def test_randint_in_range(self) -> None:
        """randint(a, b) should return values in [a, b]."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        for _ in range(1000):
            value = tap.randint(5, 15)
            assert 5 <= value <= 15

    def test_randint_single_value(self) -> None:
        """randint(a, a) should always return a."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        for _ in range(100):
            assert tap.randint(42, 42) == 42

    def test_randint_negative_range(self) -> None:
        """randint() should work with negative numbers."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        for _ in range(100):
            value = tap.randint(-10, -5)
            assert -10 <= value <= -5

    def test_randint_invalid_range_raises(self) -> None:
        """randint(a, b) where a > b should raise ValueError."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        with pytest.raises(ValueError):
            tap.randint(10, 5)

    def test_randint_distribution(self) -> None:
        """randint() should produce uniform distribution."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        # Roll a die 6000 times
        counts = Counter(tap.randint(1, 6) for _ in range(6000))

        # Each face should appear roughly 1000 times
        for face in range(1, 7):
            assert 800 < counts[face] < 1200


class TestEntropyTapRandbool:
    """Test EntropyTap.randbool() method."""

    def test_randbool_returns_bool(self) -> None:
        """randbool() should return a boolean."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        value = tap.randbool()

        assert isinstance(value, bool)

    def test_randbool_distribution(self) -> None:
        """randbool() should be approximately 50/50."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        results = [tap.randbool() for _ in range(10000)]

        true_count = sum(results)
        false_count = len(results) - true_count

        # Should be close to 50% each
        assert 4500 < true_count < 5500
        assert 4500 < false_count < 5500


class TestEntropyTapRandbytes:
    """Test EntropyTap.randbytes() method."""

    def test_randbytes_returns_bytes(self) -> None:
        """randbytes() should return bytes."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        value = tap.randbytes(16)

        assert isinstance(value, bytes)

    def test_randbytes_correct_length(self) -> None:
        """randbytes(n) should return exactly n bytes."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        for n in [1, 8, 16, 32, 64, 100, 256]:
            result = tap.randbytes(n)
            assert len(result) == n

    def test_randbytes_invalid_size_raises(self) -> None:
        """randbytes() with invalid size should raise."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        with pytest.raises(ValueError):
            tap.randbytes(0)

        with pytest.raises(ValueError):
            tap.randbytes(-1)


class TestEntropyTapChoice:
    """Test EntropyTap.choice() method."""

    def test_choice_returns_element(self) -> None:
        """choice() should return an element from the sequence."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        items = ["apple", "banana", "cherry"]

        for _ in range(100):
            result = tap.choice(items)
            assert result in items

    def test_choice_single_element(self) -> None:
        """choice() with single element should always return it."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        for _ in range(100):
            assert tap.choice([42]) == 42

    def test_choice_empty_raises(self) -> None:
        """choice() with empty sequence should raise IndexError."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        with pytest.raises(IndexError):
            tap.choice([])

    def test_choice_distribution(self) -> None:
        """choice() should select uniformly."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        items = ["a", "b", "c", "d"]
        counts = Counter(tap.choice(items) for _ in range(4000))

        # Each should be selected ~1000 times
        for item in items:
            assert 800 < counts[item] < 1200


class TestEntropyTapShuffle:
    """Test EntropyTap.shuffle() method."""

    def test_shuffle_modifies_in_place(self) -> None:
        """shuffle() should modify the list in place."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        items = [1, 2, 3, 4, 5]
        original = items.copy()

        tap.shuffle(items)

        # Should be same elements
        assert sorted(items) == sorted(original)

    def test_shuffle_changes_order(self) -> None:
        """shuffle() should change the order (usually)."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        items = list(range(10))
        original = items.copy()

        tap.shuffle(items)

        # Very unlikely to be the same order
        assert items != original

    def test_shuffle_preserves_elements(self) -> None:
        """shuffle() should not add or remove elements."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        items = ["a", "b", "c", "d", "e"]
        tap.shuffle(items)

        assert len(items) == 5
        assert set(items) == {"a", "b", "c", "d", "e"}


class TestEntropyTapSample:
    """Test EntropyTap.sample() method."""

    def test_sample_returns_list(self) -> None:
        """sample() should return a list."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        result = tap.sample([1, 2, 3, 4, 5], 3)

        assert isinstance(result, list)

    def test_sample_correct_length(self) -> None:
        """sample() should return k elements."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        result = tap.sample(range(10), 5)

        assert len(result) == 5

    def test_sample_unique_elements(self) -> None:
        """sample() should return unique elements."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        result = tap.sample(range(100), 50)

        assert len(set(result)) == 50

    def test_sample_from_sequence(self) -> None:
        """sample() elements should be from the sequence."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        items = ["a", "b", "c", "d", "e"]
        result = tap.sample(items, 3)

        for item in result:
            assert item in items

    def test_sample_invalid_k_raises(self) -> None:
        """sample() with invalid k should raise."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        with pytest.raises(ValueError):
            tap.sample([1, 2, 3], 5)  # k > len

        with pytest.raises(ValueError):
            tap.sample([1, 2, 3], -1)  # k < 0

    def test_sample_zero(self) -> None:
        """sample(seq, 0) should return empty list."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        result = tap.sample([1, 2, 3], 0)

        assert result == []


class TestEntropyTapUniform:
    """Test EntropyTap.uniform() method."""

    def test_uniform_in_range(self) -> None:
        """uniform(a, b) should return values in [a, b]."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        for _ in range(1000):
            value = tap.uniform(5.0, 10.0)
            assert 5.0 <= value <= 10.0

    def test_uniform_negative_range(self) -> None:
        """uniform() should work with negative numbers."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        for _ in range(100):
            value = tap.uniform(-10.0, -5.0)
            assert -10.0 <= value <= -5.0


class TestEntropyTapGauss:
    """Test EntropyTap.gauss() method."""

    def test_gauss_returns_float(self) -> None:
        """gauss() should return a float."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        value = tap.gauss()

        assert isinstance(value, float)

    def test_gauss_mean(self) -> None:
        """gauss() should have correct mean."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        samples = [tap.gauss(mu=5.0, sigma=1.0) for _ in range(10000)]
        mean = sum(samples) / len(samples)

        assert 4.8 < mean < 5.2

    def test_gauss_standard_deviation(self) -> None:
        """gauss() should have correct standard deviation."""
        pool = EntropyPool()
        tap = EntropyTap(pool)

        samples = [tap.gauss(mu=0.0, sigma=2.0) for _ in range(10000)]
        mean = sum(samples) / len(samples)
        std = math.sqrt(sum((x - mean) ** 2 for x in samples) / len(samples))

        assert 1.8 < std < 2.2
