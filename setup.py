"""
TrueEntropy - Setup Script for Cython Extension

This script builds the Cython-accelerated extension module.

Usage:
    # Build in-place for development
    python setup.py build_ext --inplace
    
    # Or install with Cython support
    pip install -e ".[cython]"
"""

import os
import sys
from pathlib import Path

# Try to import Cython and setuptools
try:
    from Cython.Build import cythonize
    from setuptools import setup, Extension
    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False
    from setuptools import setup


def get_extensions():
    """Get the list of Cython extensions to build."""
    if not CYTHON_AVAILABLE:
        print("Cython not available. Skipping extension build.")
        return []
    
    # Find the .pyx file
    src_dir = Path(__file__).parent / "src" / "trueentropy"
    pyx_file = src_dir / "_accel.pyx"
    
    if not pyx_file.exists():
        print(f"Warning: {pyx_file} not found. Skipping extension build.")
        return []
    
    extensions = [
        Extension(
            "trueentropy._accel",
            sources=[str(pyx_file)],
            extra_compile_args=["-O3"] if sys.platform != "win32" else ["/O2"],
        )
    ]
    
    return cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        }
    )


if __name__ == "__main__":
    # This script is only for building extensions
    # Full package installation is handled by pyproject.toml
    setup(
        name="trueentropy-accel",
        ext_modules=get_extensions(),
    )
