# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""
TrueEntropy - Cython Accelerated Core Functions

This module provides Cython-accelerated versions of performance-critical
functions in TrueEntropy. The speedup comes from:

1. Static typing - No Python object overhead
2. Direct C memory access - No bounds checking
3. Native C operations - No Python interpreter overhead

To build:
    pip install cython
    python setup.py build_ext --inplace

Or with pip:
    pip install -e ".[cython]"
"""

from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from cpython.bytes cimport PyBytes_FromStringAndSize

import struct


# =============================================================================
# Fast Byte Operations
# =============================================================================

def xor_bytes_fast(bytes data, bytes key):
    """
    Fast XOR of two byte strings using C-level operations.
    
    This is ~10-50x faster than the pure Python version for large inputs.
    
    Args:
        data: The data to XOR
        key: The key (will be repeated if shorter than data)
    
    Returns:
        XOR'd bytes
    """
    cdef:
        Py_ssize_t data_len = len(data)
        Py_ssize_t key_len = len(key)
        unsigned char* result
        const unsigned char* d = data
        const unsigned char* k = key
        Py_ssize_t i
    
    if data_len == 0:
        return b""
    
    if key_len == 0:
        return data
    
    result = <unsigned char*>malloc(data_len)
    if result == NULL:
        raise MemoryError("Failed to allocate memory")
    
    try:
        for i in range(data_len):
            result[i] = d[i] ^ k[i % key_len]
        
        return PyBytes_FromStringAndSize(<char*>result, data_len)
    finally:
        free(result)


def bytes_to_int_fast(bytes data):
    """
    Convert bytes to integer using C-level operations.
    
    Args:
        data: Bytes to convert (big-endian)
    
    Returns:
        Integer value
    """
    cdef:
        Py_ssize_t n = len(data)
        const unsigned char* d = data
        unsigned long long result = 0
        Py_ssize_t i
    
    # Handle up to 8 bytes (64 bits)
    if n > 8:
        n = 8
    
    for i in range(n):
        result = (result << 8) | d[i]
    
    return result


def int_to_bytes_fast(unsigned long long value, int length):
    """
    Convert integer to bytes using C-level operations.
    
    Args:
        value: Integer to convert
        length: Number of bytes in output
    
    Returns:
        Big-endian bytes
    """
    cdef:
        unsigned char* result
        int i
    
    result = <unsigned char*>malloc(length)
    if result == NULL:
        raise MemoryError("Failed to allocate memory")
    
    try:
        for i in range(length - 1, -1, -1):
            result[i] = value & 0xFF
            value >>= 8
        
        return PyBytes_FromStringAndSize(<char*>result, length)
    finally:
        free(result)


# =============================================================================
# Fast Random Number Scaling
# =============================================================================

def scale_to_range_fast(unsigned long long value, int a, int b):
    """
    Scale a random value to a range [a, b] with rejection sampling.
    
    This avoids modulo bias by rejecting values outside the valid range.
    
    Args:
        value: Random value (0 to 2^64-1)
        a: Lower bound (inclusive)
        b: Upper bound (inclusive)
    
    Returns:
        Tuple of (scaled_value, needs_retry)
    """
    cdef:
        unsigned long long range_size
        unsigned long long threshold
        int bits_needed
        unsigned long long mask
        unsigned long long scaled
    
    if a > b:
        raise ValueError("a must be <= b")
    
    if a == b:
        return (a, False)
    
    range_size = <unsigned long long>(b - a + 1)
    
    # Calculate bits needed
    bits_needed = 0
    temp = range_size - 1
    while temp > 0:
        bits_needed += 1
        temp >>= 1
    
    # Create mask
    mask = (1ULL << bits_needed) - 1
    
    # Apply mask
    scaled = value & mask
    
    # Check if in range
    if scaled < range_size:
        return (a + <int>scaled, False)
    else:
        return (0, True)  # Needs retry


def uniform_float_fast(unsigned long long value):
    """
    Convert 64-bit integer to float in [0.0, 1.0).
    
    Args:
        value: 64-bit random value
    
    Returns:
        Float in [0.0, 1.0)
    """
    # 2^64 = 18446744073709551616
    return <double>value / 18446744073709551616.0


# =============================================================================
# Fast Fisher-Yates Shuffle (indices only)
# =============================================================================

def fisher_yates_indices(int n, random_func):
    """
    Generate Fisher-Yates shuffle indices.
    
    Args:
        n: Length of sequence to shuffle
        random_func: Function that returns random int in range [0, i]
    
    Returns:
        List of swap pairs [(i, j), ...]
    """
    cdef:
        int i, j
        list swaps = []
    
    for i in range(n - 1, 0, -1):
        j = random_func(0, i)
        if i != j:
            swaps.append((i, j))
    
    return swaps


# =============================================================================
# Module Info
# =============================================================================

def is_accelerated():
    """Check if Cython acceleration is available."""
    return True


def get_version():
    """Get Cython module version."""
    return "1.0.0"
