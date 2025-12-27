# =============================================================================
# TrueEntropy - Test Configuration
# =============================================================================

"""Pytest configuration and fixtures for TrueEntropy tests."""

import pytest

from trueentropy.pool import EntropyPool
from trueentropy.tap import EntropyTap


@pytest.fixture
def pool() -> EntropyPool:
    """Create a fresh EntropyPool for testing."""
    return EntropyPool()


@pytest.fixture
def seeded_pool() -> EntropyPool:
    """Create an EntropyPool with fixed seed for deterministic tests."""
    return EntropyPool(seed=b"test_seed_for_deterministic_tests")


@pytest.fixture
def tap(pool: EntropyPool) -> EntropyTap:
    """Create an EntropyTap with a fresh pool."""
    return EntropyTap(pool)


@pytest.fixture
def seeded_tap(seeded_pool: EntropyPool) -> EntropyTap:
    """Create an EntropyTap with seeded pool for deterministic tests."""
    return EntropyTap(seeded_pool)
