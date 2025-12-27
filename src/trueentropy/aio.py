# =============================================================================
# TrueEntropy - Async Support Module
# =============================================================================
#
# This module provides async/await support for TrueEntropy.
# All random generation functions have async versions that can be
# used in asyncio applications.
#
# Usage:
#     import asyncio
#     import trueentropy.aio as te_async
#
#     async def main():
#         value = await te_async.random()
#         number = await te_async.randint(1, 100)
#
#     asyncio.run(main())
#
# =============================================================================

"""
Async support for TrueEntropy.

Provides async versions of all random generation functions for use
in asyncio applications.
"""

from __future__ import annotations

import asyncio
from collections.abc import MutableSequence, Sequence
from typing import Any, TypeVar

from trueentropy.pool import EntropyPool
from trueentropy.tap import EntropyTap

T = TypeVar("T")

# Global async-safe pool and tap
_async_pool: EntropyPool = EntropyPool()
_async_tap: EntropyTap = EntropyTap(_async_pool)
_async_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    """Get or create the async lock."""
    global _async_lock
    if _async_lock is None:
        _async_lock = asyncio.Lock()
    return _async_lock


# =============================================================================
# Async Random Value Generation
# =============================================================================


async def random() -> float:
    """
    Async version of trueentropy.random().

    Returns:
        A float value where 0.0 <= value < 1.0

    Example:
        >>> import asyncio
        >>> import trueentropy.aio as te
        >>> asyncio.run(te.random())
        0.7234891623...
    """
    async with _get_lock():
        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.random)


async def randint(a: int, b: int) -> int:
    """
    Async version of trueentropy.randint().

    Args:
        a: Lower bound (inclusive)
        b: Upper bound (inclusive)

    Returns:
        Random integer in [a, b]
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.randint, a, b)


async def randbool() -> bool:
    """
    Async version of trueentropy.randbool().

    Returns:
        True or False with equal probability
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.randbool)


async def randbytes(n: int) -> bytes:
    """
    Async version of trueentropy.randbytes().

    Args:
        n: Number of bytes to generate

    Returns:
        A bytes object of length n
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.randbytes, n)


async def choice(seq: Sequence[T]) -> T:
    """
    Async version of trueentropy.choice().

    Args:
        seq: A non-empty sequence

    Returns:
        A randomly selected element
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.choice, seq)


async def shuffle(seq: MutableSequence[Any]) -> None:
    """
    Async version of trueentropy.shuffle().

    Args:
        seq: A mutable sequence to shuffle in-place
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _async_tap.shuffle, seq)


async def sample(seq: Sequence[T], k: int) -> list[T]:
    """
    Async version of trueentropy.sample().

    Args:
        seq: The sequence to sample from
        k: Number of unique elements to select

    Returns:
        A list of k unique elements
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.sample, seq, k)


async def random_uuid() -> str:
    """
    Async version of trueentropy.random_uuid().

    Returns:
        A UUID v4 string
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.random_uuid)


async def random_token(length: int = 32, encoding: str = "hex") -> str:
    """
    Async version of trueentropy.random_token().

    Args:
        length: Number of random bytes
        encoding: 'hex' or 'base64'

    Returns:
        A random token string
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.random_token, length, encoding)


async def random_password(
    length: int = 16,
    charset: str | None = None,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
) -> str:
    """
    Async version of trueentropy.random_password().

    Args:
        length: Password length
        charset: Custom character set
        include_*: Character type flags

    Returns:
        A random password string
    """
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: _async_tap.random_password(
                length,
                charset,
                include_uppercase,
                include_lowercase,
                include_digits,
                include_symbols,
            ),
        )


# =============================================================================
# Async Distributions
# =============================================================================


async def uniform(a: float, b: float) -> float:
    """Async version of trueentropy.uniform()."""
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.uniform, a, b)


async def gauss(mu: float = 0.0, sigma: float = 1.0) -> float:
    """Async version of trueentropy.gauss()."""
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.gauss, mu, sigma)


async def triangular(low: float = 0.0, high: float = 1.0, mode: float | None = None) -> float:
    """Async version of trueentropy.triangular()."""
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.triangular, low, high, mode)


async def exponential(lambd: float = 1.0) -> float:
    """Async version of trueentropy.exponential()."""
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.exponential, lambd)


async def weighted_choice(seq: Sequence[T], weights: Sequence[float]) -> T:
    """Async version of trueentropy.weighted_choice()."""
    async with _get_lock():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _async_tap.weighted_choice, seq, weights)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "random",
    "randint",
    "randbool",
    "randbytes",
    "choice",
    "shuffle",
    "sample",
    "random_uuid",
    "random_token",
    "random_password",
    "uniform",
    "gauss",
    "triangular",
    "exponential",
    "weighted_choice",
]
