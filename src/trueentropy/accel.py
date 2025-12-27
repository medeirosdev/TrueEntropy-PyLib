# =============================================================================
# TrueEntropy - Accelerated Operations
# =============================================================================
#
# This module provides accelerated versions of performance-critical functions.
# It automatically uses Cython-compiled code if available, falling back to
# pure Python implementations otherwise.
#
# Usage:
#     from trueentropy.accel import xor_bytes, bytes_to_int, is_accelerated
#
#     if is_accelerated():
#         print("Using Cython acceleration!")
#
# =============================================================================

"""
Accelerated operations for TrueEntropy.

Provides fast implementations of core operations, using Cython
when available and falling back to pure Python otherwise.
"""

from __future__ import annotations

# Try to import Cython-accelerated functions
_USE_CYTHON = False

try:
    from trueentropy._accel import (
        bytes_to_int_fast,
        fisher_yates_indices,
        int_to_bytes_fast,
        scale_to_range_fast,
        uniform_float_fast,
        xor_bytes_fast,
    )

    _USE_CYTHON = True
except ImportError:
    _USE_CYTHON = False


# =============================================================================
# Pure Python Fallbacks
# =============================================================================


def _xor_bytes_python(data: bytes, key: bytes) -> bytes:
    """Pure Python XOR implementation."""
    if not data or not key:
        return data

    result = bytearray(len(data))
    key_len = len(key)

    for i, b in enumerate(data):
        result[i] = b ^ key[i % key_len]

    return bytes(result)


def _bytes_to_int_python(data: bytes) -> int:
    """Pure Python bytes to int."""
    return int.from_bytes(data[:8], "big")


def _int_to_bytes_python(value: int, length: int) -> bytes:
    """Pure Python int to bytes."""
    return value.to_bytes(length, "big")


def _scale_to_range_python(value: int, a: int, b: int) -> tuple:
    """Pure Python range scaling with rejection sampling."""
    if a > b:
        raise ValueError("a must be <= b")

    if a == b:
        return (a, False)

    range_size = b - a + 1
    bits_needed = (range_size - 1).bit_length()
    mask = (1 << bits_needed) - 1

    scaled = value & mask

    if scaled < range_size:
        return (a + scaled, False)
    else:
        return (0, True)


def _uniform_float_python(value: int) -> float:
    """Pure Python uniform float."""
    return value / 18446744073709551616.0


def _fisher_yates_indices_python(n: int, random_func) -> list:
    """Pure Python Fisher-Yates indices."""
    swaps = []
    for i in range(n - 1, 0, -1):
        j = random_func(0, i)
        if i != j:
            swaps.append((i, j))
    return swaps


# =============================================================================
# Public API - Auto-selects best implementation
# =============================================================================


def xor_bytes(data: bytes, key: bytes) -> bytes:
    """
    XOR two byte strings.

    Uses Cython acceleration if available (10-50x faster).

    Args:
        data: The data to XOR
        key: The key (repeated if shorter)

    Returns:
        XOR'd bytes
    """
    if _USE_CYTHON:
        return xor_bytes_fast(data, key)
    return _xor_bytes_python(data, key)


def bytes_to_int(data: bytes) -> int:
    """
    Convert bytes to integer (big-endian).

    Args:
        data: Bytes to convert (up to 8 bytes)

    Returns:
        Integer value
    """
    if _USE_CYTHON:
        return bytes_to_int_fast(data)
    return _bytes_to_int_python(data)


def int_to_bytes(value: int, length: int) -> bytes:
    """
    Convert integer to bytes (big-endian).

    Args:
        value: Integer to convert
        length: Output length

    Returns:
        Bytes representation
    """
    if _USE_CYTHON:
        return int_to_bytes_fast(value, length)
    return _int_to_bytes_python(value, length)


def scale_to_range(value: int, a: int, b: int) -> tuple:
    """
    Scale random value to range with rejection sampling.

    Args:
        value: Random value
        a: Lower bound
        b: Upper bound

    Returns:
        (scaled_value, needs_retry)
    """
    if _USE_CYTHON:
        return scale_to_range_fast(value, a, b)
    return _scale_to_range_python(value, a, b)


def uniform_float(value: int) -> float:
    """
    Convert 64-bit int to float in [0, 1).

    Args:
        value: 64-bit random value

    Returns:
        Float in [0.0, 1.0)
    """
    if _USE_CYTHON:
        return uniform_float_fast(value)
    return _uniform_float_python(value)


def get_fisher_yates_indices(n: int, random_func) -> list:
    """
    Generate Fisher-Yates shuffle swap indices.

    Args:
        n: Sequence length
        random_func: Function(a, b) -> random int in [a, b]

    Returns:
        List of (i, j) swap pairs
    """
    if _USE_CYTHON:
        return fisher_yates_indices(n, random_func)
    return _fisher_yates_indices_python(n, random_func)


def is_accelerated() -> bool:
    """
    Check if Cython acceleration is active.

    Returns:
        True if using Cython, False if pure Python
    """
    return _USE_CYTHON


def get_backend() -> str:
    """
    Get the current acceleration backend name.

    Returns:
        'cython' or 'python'
    """
    return "cython" if _USE_CYTHON else "python"


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "xor_bytes",
    "bytes_to_int",
    "int_to_bytes",
    "scale_to_range",
    "uniform_float",
    "get_fisher_yates_indices",
    "is_accelerated",
    "get_backend",
]
