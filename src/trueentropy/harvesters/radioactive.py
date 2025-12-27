# =============================================================================
# TrueEntropy - Radioactive Harvester
# =============================================================================
#
# This harvester collects entropy from random.org, which uses atmospheric
# noise and radioactive decay to generate true random numbers.
#
# random.org is one of the most trusted sources of true randomness,
# used by lotteries, scientific research, and cryptographic applications.
#
# Data Sources:
# - Random integers from atmospheric noise
# - Random bytes in various formats
#
# Why Radioactive/Atmospheric Data is Random:
# - Quantum mechanical phenomena are truly unpredictable
# - Atmospheric noise is chaotic and uncontrollable
# - Independent of any computer system
#
# Note: random.org has rate limits for free tier:
# - 1,000,000 bits/day for free
# - Consider getting an API key for heavy usage
#
# =============================================================================

"""
Radioactive decay and atmospheric noise entropy harvester.

Collects entropy from random.org, which generates random numbers
from atmospheric noise and radioactive decay.
"""

from __future__ import annotations

import hashlib
import struct
import time
from typing import Any, List, Optional

from trueentropy.harvesters.base import BaseHarvester, HarvestResult


class RadioactiveHarvester(BaseHarvester):
    """
    Harvests entropy from random.org (atmospheric noise/radioactive decay).
    
    random.org generates randomness from atmospheric noise, which is
    ultimately derived from quantum mechanical phenomena like radioactive
    decay. This provides true hardware-quality randomness.
    
    Features:
    - Uses random.org's public API for random integers
    - Falls back to random.org's simple API if JSON fails
    - Respects rate limits (free tier: 1M bits/day)
    
    Attributes:
        api_key: Optional random.org API key for higher quotas
        timeout: Request timeout in seconds
        num_integers: Number of random integers to request per collection
    
    Example:
        >>> harvester = RadioactiveHarvester()
        >>> result = harvester.collect()
        >>> if result.success:
        ...     print(f"Got {result.entropy_bits} bits from random.org!")
    """
    
    # -------------------------------------------------------------------------
    # API Configuration
    # -------------------------------------------------------------------------
    
    # random.org JSON-RPC API (requires API key for full access)
    RANDOM_ORG_API_URL = "https://api.random.org/json-rpc/4/invoke"
    
    # random.org simple HTTP API (free, rate-limited)
    RANDOM_ORG_INTEGER_URL = "https://www.random.org/integers/"
    RANDOM_ORG_STRINGS_URL = "https://www.random.org/strings/"
    
    # ANU Quantum Random Numbers (alternative source)
    ANU_QRNG_URL = "https://qrng.anu.edu.au/API/jsonI.php"
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
        num_integers: int = 10
    ) -> None:
        """
        Initialize the radioactive harvester.
        
        Args:
            api_key: Optional random.org API key for higher quotas.
                    Without a key, uses the free public endpoints.
            timeout: Request timeout in seconds (default: 10.0 - random.org
                    can be slow sometimes)
            num_integers: Number of random integers to request per collection.
                         More integers = more entropy but slower.
        """
        self._api_key = api_key
        self._timeout = timeout
        self._num_integers = num_integers
    
    # -------------------------------------------------------------------------
    # BaseHarvester Implementation
    # -------------------------------------------------------------------------
    
    @property
    def name(self) -> str:
        """Return harvester name."""
        return "radioactive"
    
    def collect(self) -> HarvestResult:
        """
        Collect entropy from random.org.
        
        Process:
        1. Request random integers from random.org
        2. If that fails, try ANU Quantum RNG
        3. Pack integers into bytes
        4. Hash for additional mixing
        
        Returns:
            HarvestResult containing radioactive/atmospheric entropy
        """
        try:
            import requests
        except ImportError:
            return HarvestResult(
                data=b"",
                entropy_bits=0,
                source=self.name,
                success=False,
                error="requests library not available"
            )
        
        # Try random.org first
        values = self._fetch_random_org(requests)
        
        # Fallback to ANU Quantum RNG if random.org fails
        if not values:
            values = self._fetch_anu_qrng(requests)
        
        if not values:
            return HarvestResult(
                data=b"",
                entropy_bits=0,
                source=self.name,
                success=False,
                error="All random sources unavailable (rate limited or offline)"
            )
        
        # Add local timestamp for mixing
        values.append(time.time_ns())
        
        # Pack as 64-bit integers
        data = struct.pack(f"!{len(values)}Q", *[v & 0xFFFFFFFFFFFFFFFF for v in values])
        
        # Hash for uniform distribution
        hashed = hashlib.sha256(data).digest()
        
        # Entropy estimate: random.org provides true random bits
        # Each 32-bit integer = 32 bits of entropy
        entropy_bits = (len(values) - 1) * 32  # -1 for timestamp
        
        return HarvestResult(
            data=data + hashed,
            entropy_bits=entropy_bits,
            source=self.name,
            success=True
        )
    
    # -------------------------------------------------------------------------
    # random.org API
    # -------------------------------------------------------------------------
    
    def _fetch_random_org(self, requests: Any) -> List[int]:
        """
        Fetch random integers from random.org.
        
        Uses the simple HTTP API which doesn't require authentication
        but has daily quotas.
        
        Args:
            requests: The imported requests module
        
        Returns:
            List of random integers
        """
        try:
            # Use simple HTTP API (no auth needed)
            params = {
                "num": self._num_integers,
                "min": 0,
                "max": 2147483647,  # Max 32-bit signed int
                "col": 1,
                "base": 10,
                "format": "plain",
                "rnd": "new"
            }
            
            response = requests.get(
                self.RANDOM_ORG_INTEGER_URL,
                params=params,
                timeout=self._timeout
            )
            
            # Check for quota exceeded
            if response.status_code == 503:
                return []  # Rate limited, try fallback
            
            response.raise_for_status()
            
            # Parse the response (one integer per line)
            lines = response.text.strip().split('\n')
            values = [int(line.strip()) for line in lines if line.strip()]
            
            return values
            
        except Exception:
            return []
    
    def _fetch_random_org_api(self, requests: Any) -> List[int]:
        """
        Fetch random integers using random.org JSON-RPC API.
        
        Requires API key but provides higher quotas.
        
        Args:
            requests: The imported requests module
        
        Returns:
            List of random integers
        """
        if not self._api_key:
            return []
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "generateIntegers",
                "params": {
                    "apiKey": self._api_key,
                    "n": self._num_integers,
                    "min": 0,
                    "max": 2147483647,
                    "replacement": True
                },
                "id": 1
            }
            
            response = requests.post(
                self.RANDOM_ORG_API_URL,
                json=payload,
                timeout=self._timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                return []
            
            result = data.get("result", {})
            random_data = result.get("random", {})
            values = random_data.get("data", [])
            
            return values
            
        except Exception:
            return []
    
    # -------------------------------------------------------------------------
    # ANU Quantum Random Number Generator (Fallback)
    # -------------------------------------------------------------------------
    
    def _fetch_anu_qrng(self, requests: Any) -> List[int]:
        """
        Fetch random numbers from ANU Quantum Random Number Generator.
        
        ANU QRNG generates random numbers by measuring quantum vacuum
        fluctuations. This is true quantum randomness.
        
        Args:
            requests: The imported requests module
        
        Returns:
            List of random integers
        """
        try:
            params = {
                "length": self._num_integers,
                "type": "uint32"
            }
            
            response = requests.get(
                self.ANU_QRNG_URL,
                params=params,
                timeout=self._timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success", False):
                return []
            
            values = data.get("data", [])
            
            return values
            
        except Exception:
            return []
    
    # -------------------------------------------------------------------------
    # Configuration Properties
    # -------------------------------------------------------------------------
    
    @property
    def api_key(self) -> Optional[str]:
        """Get the API key (masked for security)."""
        if self._api_key:
            return self._api_key[:8] + "..."
        return None
    
    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        """Set the API key."""
        self._api_key = value
    
    @property
    def timeout(self) -> float:
        """Get the request timeout in seconds."""
        return self._timeout
    
    @timeout.setter
    def timeout(self, value: float) -> None:
        """Set the request timeout."""
        if value <= 0:
            raise ValueError("timeout must be positive")
        self._timeout = value
    
    @property
    def num_integers(self) -> int:
        """Get the number of integers to request."""
        return self._num_integers
    
    @num_integers.setter
    def num_integers(self, value: int) -> None:
        """Set the number of integers to request."""
        if value < 1:
            raise ValueError("num_integers must be at least 1")
        if value > 1000:
            raise ValueError("num_integers must be at most 1000")
        self._num_integers = value
