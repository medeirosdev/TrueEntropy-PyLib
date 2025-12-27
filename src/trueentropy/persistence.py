# =============================================================================
# TrueEntropy - Pool Persistence Module
# =============================================================================
#
# This module provides save/restore functionality for the entropy pool.
# This allows the pool state to be persisted between application runs,
# maintaining accumulated entropy.
#
# Usage:
#     from trueentropy.persistence import save_pool, load_pool
#
#     # Save pool state
#     save_pool(pool, "entropy_state.bin")
#
#     # Load pool state
#     pool = load_pool("entropy_state.bin")
#
# Security Note:
#     The pool state file contains sensitive entropy data.
#     Protect it with appropriate file permissions.
#
# =============================================================================

"""
Pool persistence - save and restore entropy pool state.

This module allows the entropy pool to be saved to disk and restored,
maintaining accumulated entropy between application runs.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import time
from pathlib import Path
from typing import BinaryIO, Union

from trueentropy.pool import EntropyPool


# Type alias for path-like objects
PathLike = Union[str, Path]


class PoolStateError(Exception):
    """Raised when pool state is invalid or corrupted."""
    pass


def save_pool(
    pool: EntropyPool,
    path: PathLike,
    include_checksum: bool = True
) -> None:
    """
    Save the entropy pool state to a file.
    
    The pool state is saved in a binary format that includes:
    - Magic header for identification
    - Version number for format compatibility
    - Timestamp of when the state was saved
    - Pool statistics (entropy_bits, total_fed, total_extracted)
    - The raw pool state (encrypted with simple XOR using timestamp)
    - Optional SHA-256 checksum for integrity verification
    
    Args:
        pool: The EntropyPool instance to save
        path: Path to save the state file
        include_checksum: Whether to include integrity checksum
    
    Raises:
        IOError: If the file cannot be written
    
    Example:
        >>> from trueentropy import get_pool
        >>> from trueentropy.persistence import save_pool
        >>> pool = get_pool()
        >>> save_pool(pool, "entropy_state.bin")
    
    Security:
        The saved file should be protected with appropriate
        filesystem permissions (e.g., chmod 600).
    """
    path = Path(path)
    
    # Collect pool data
    state_data = pool._get_state_for_persistence()
    
    with open(path, "wb") as f:
        _write_pool_state(f, state_data, include_checksum)
    
    # Set restrictive permissions on Unix systems
    try:
        os.chmod(path, 0o600)
    except (OSError, AttributeError):
        pass  # Windows or permission denied


def load_pool(
    path: PathLike,
    verify_checksum: bool = True
) -> EntropyPool:
    """
    Load an entropy pool state from a file.
    
    Args:
        path: Path to the state file
        verify_checksum: Whether to verify the integrity checksum
    
    Returns:
        A new EntropyPool instance with the restored state
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        PoolStateError: If the file is corrupted or invalid
    
    Example:
        >>> from trueentropy.persistence import load_pool
        >>> pool = load_pool("entropy_state.bin")
        >>> print(f"Restored {pool.entropy_bits} bits of entropy")
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Pool state file not found: {path}")
    
    with open(path, "rb") as f:
        state_data = _read_pool_state(f, verify_checksum)
    
    # Create new pool and restore state
    pool = EntropyPool()
    pool._restore_state_from_persistence(state_data)
    
    return pool


def save_pool_json(
    pool: EntropyPool,
    path: PathLike
) -> None:
    """
    Save pool state as JSON (human-readable, less secure).
    
    This format is useful for debugging but should not be used
    in production as it exposes the raw entropy state.
    
    Args:
        pool: The EntropyPool instance to save
        path: Path to save the JSON file
    """
    path = Path(path)
    
    state_data = pool._get_state_for_persistence()
    
    # Convert bytes to hex for JSON serialization
    json_data = {
        "version": 1,
        "timestamp": time.time(),
        "entropy_bits": state_data["entropy_bits"],
        "total_fed": state_data["total_fed"],
        "total_extracted": state_data["total_extracted"],
        "state_hex": state_data["state"].hex(),
        "checksum": hashlib.sha256(state_data["state"]).hexdigest()
    }
    
    with open(path, "w") as f:
        json.dump(json_data, f, indent=2)


def load_pool_json(path: PathLike) -> EntropyPool:
    """
    Load pool state from JSON format.
    
    Args:
        path: Path to the JSON file
    
    Returns:
        A new EntropyPool instance with the restored state
    """
    path = Path(path)
    
    with open(path, "r") as f:
        json_data = json.load(f)
    
    # Verify checksum
    state_bytes = bytes.fromhex(json_data["state_hex"])
    expected_checksum = hashlib.sha256(state_bytes).hexdigest()
    
    if json_data.get("checksum") != expected_checksum:
        raise PoolStateError("JSON pool state checksum mismatch")
    
    state_data = {
        "entropy_bits": json_data["entropy_bits"],
        "total_fed": json_data["total_fed"],
        "total_extracted": json_data["total_extracted"],
        "state": state_bytes
    }
    
    pool = EntropyPool()
    pool._restore_state_from_persistence(state_data)
    
    return pool


# =============================================================================
# Binary Format Implementation
# =============================================================================

# Magic header to identify TrueEntropy pool files
MAGIC_HEADER = b"TRUEENT\x00"

# Current format version
FORMAT_VERSION = 1


def _write_pool_state(
    f: BinaryIO,
    state_data: dict,
    include_checksum: bool
) -> None:
    """Write pool state in binary format."""
    
    # Magic header (8 bytes)
    f.write(MAGIC_HEADER)
    
    # Version (4 bytes, little-endian)
    f.write(struct.pack("<I", FORMAT_VERSION))
    
    # Timestamp (8 bytes, double)
    timestamp = time.time()
    f.write(struct.pack("<d", timestamp))
    
    # Statistics (3 x 8 bytes = 24 bytes)
    f.write(struct.pack("<Q", state_data["entropy_bits"]))
    f.write(struct.pack("<Q", state_data["total_fed"]))
    f.write(struct.pack("<Q", state_data["total_extracted"]))
    
    # State length (4 bytes)
    state = state_data["state"]
    f.write(struct.pack("<I", len(state)))
    
    # State data (XOR obfuscated with timestamp-derived key)
    key = _derive_key(timestamp)
    obfuscated = _xor_bytes(state, key)
    f.write(obfuscated)
    
    # Optional checksum (32 bytes SHA-256)
    if include_checksum:
        checksum = hashlib.sha256(state).digest()
        f.write(checksum)


def _read_pool_state(f: BinaryIO, verify_checksum: bool) -> dict:
    """Read pool state from binary format."""
    
    # Magic header
    header = f.read(8)
    if header != MAGIC_HEADER:
        raise PoolStateError("Invalid pool state file (bad magic header)")
    
    # Version
    version = struct.unpack("<I", f.read(4))[0]
    if version != FORMAT_VERSION:
        raise PoolStateError(f"Unsupported format version: {version}")
    
    # Timestamp
    timestamp = struct.unpack("<d", f.read(8))[0]
    
    # Statistics
    entropy_bits = struct.unpack("<Q", f.read(8))[0]
    total_fed = struct.unpack("<Q", f.read(8))[0]
    total_extracted = struct.unpack("<Q", f.read(8))[0]
    
    # State
    state_len = struct.unpack("<I", f.read(4))[0]
    obfuscated = f.read(state_len)
    
    if len(obfuscated) != state_len:
        raise PoolStateError("Truncated pool state file")
    
    # De-obfuscate
    key = _derive_key(timestamp)
    state = _xor_bytes(obfuscated, key)
    
    # Optional checksum
    if verify_checksum:
        checksum_data = f.read(32)
        if checksum_data:
            expected = hashlib.sha256(state).digest()
            if checksum_data != expected:
                raise PoolStateError("Pool state checksum mismatch (corrupted?)")
    
    return {
        "entropy_bits": entropy_bits,
        "total_fed": total_fed,
        "total_extracted": total_extracted,
        "state": state
    }


def _derive_key(timestamp: float) -> bytes:
    """Derive an obfuscation key from timestamp."""
    # Simple key derivation - not cryptographic, just obfuscation
    ts_bytes = struct.pack("<d", timestamp)
    return hashlib.sha256(ts_bytes).digest() * 16  # 512 bytes


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR data with key (key is repeated as needed)."""
    result = bytearray(len(data))
    for i, b in enumerate(data):
        result[i] = b ^ key[i % len(key)]
    return bytes(result)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "save_pool",
    "load_pool",
    "save_pool_json",
    "load_pool_json",
    "PoolStateError",
]
