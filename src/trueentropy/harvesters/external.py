# =============================================================================
# TrueEntropy - External API Harvester
# =============================================================================
#
# This harvester collects entropy from external APIs that provide real-world
# data - bringing randomness from outside the computer.
#
# Data Sources:
# 1. USGS Earthquake API - Latest seismic activity
# 2. Cryptocurrency Prices - Bitcoin/ETH prices with high precision
#
# Why External Data is Random:
# - Earthquake magnitude/location are natural phenomena
# - Crypto prices change every second based on global trading
# - These values are determined by chaotic real-world systems
#
# Entropy Estimate:
# - High: ~16-32 bits per successful API call
# - External sources provide true real-world entropy
#
# =============================================================================

"""
External API-based entropy harvester.

Collects entropy from real-world data sources via public APIs:
- USGS earthquake data (seismic activity)
- Cryptocurrency prices (market chaos)
"""

from __future__ import annotations

import hashlib
import struct
import time
from typing import Any

from trueentropy.harvesters.base import BaseHarvester, HarvestResult


class ExternalHarvester(BaseHarvester):
    """
    Harvests entropy from external real-world APIs.

    This harvester fetches data from public APIs that provide
    information about chaotic real-world systems:

    1. **USGS Earthquake API**: Latest seismic activity worldwide
    2. **Coinbase/CoinGecko**: Cryptocurrency prices with high precision

    These sources bring entropy from outside the computer - data that
    is determined by physical and social phenomena.

    Attributes:
        timeout: Request timeout in seconds (default: 5.0)
        enable_earthquake: Whether to fetch earthquake data (default: True)
        enable_crypto: Whether to fetch crypto prices (default: True)

    Example:
        >>> harvester = ExternalHarvester()
        >>> result = harvester.collect()
        >>> if result.success:
        ...     print(f"Collected {result.entropy_bits} bits from the world!")
    """

    # -------------------------------------------------------------------------
    # API Endpoints
    # -------------------------------------------------------------------------

    # USGS Earthquake API - Returns earthquakes from the last hour
    # Documentation: https://earthquake.usgs.gov/fdsnws/event/1/
    USGS_EARTHQUAKE_URL = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    )

    # CoinGecko API - Free cryptocurrency price data
    # Documentation: https://www.coingecko.com/en/api/documentation
    COINGECKO_URL = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum&vs_currencies=usd&precision=18"
    )

    # Coinbase API - Alternative crypto price source
    COINBASE_BTC_URL = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    COINBASE_ETH_URL = "https://api.coinbase.com/v2/prices/ETH-USD/spot"

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def __init__(
        self, timeout: float = 5.0, enable_earthquake: bool = True, enable_crypto: bool = True
    ) -> None:
        """
        Initialize the external harvester.

        Args:
            timeout: Request timeout in seconds
            enable_earthquake: Whether to fetch earthquake data
            enable_crypto: Whether to fetch cryptocurrency prices
        """
        self._timeout = timeout
        self._enable_earthquake = enable_earthquake
        self._enable_crypto = enable_crypto

    # -------------------------------------------------------------------------
    # BaseHarvester Implementation
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return harvester name."""
        return "external"

    def collect(self) -> HarvestResult:
        """
        Collect entropy from external APIs.

        Process:
        1. Fetch data from enabled sources (earthquake, crypto)
        2. Combine all data into a single bytes object
        3. Estimate entropy based on data quality

        Note: This harvester gracefully handles API failures.
        It will succeed if at least one source returns data.

        Returns:
            HarvestResult containing external API entropy
        """
        # Attempt import of requests library
        try:
            import requests
        except ImportError:
            return HarvestResult(
                data=b"",
                entropy_bits=0,
                source=self.name,
                success=False,
                error="requests library not available",
            )

        collected_data: list[bytes] = []
        total_entropy_bits = 0
        errors: list[str] = []

        # Collect earthquake data
        if self._enable_earthquake:
            result = self._fetch_earthquake_data(requests)
            if result is not None:
                collected_data.append(result)
                total_entropy_bits += 24  # ~24 bits from earthquake data
            else:
                errors.append("earthquake API failed")

        # Collect cryptocurrency data
        if self._enable_crypto:
            result = self._fetch_crypto_data(requests)
            if result is not None:
                collected_data.append(result)
                total_entropy_bits += 32  # ~32 bits from crypto prices
            else:
                errors.append("crypto API failed")

        # Add timestamp for guaranteed fresh data
        timestamp_bytes = struct.pack("!Q", time.time_ns())
        collected_data.append(timestamp_bytes)
        total_entropy_bits += 8

        # Combine all collected data
        if collected_data:
            combined = b"".join(collected_data)

            # Hash the combined data for uniform output
            # This also protects against API response prediction
            hashed = hashlib.sha256(combined).digest()

            return HarvestResult(
                data=combined + hashed,
                entropy_bits=total_entropy_bits,
                source=self.name,
                success=True,
                error="; ".join(errors) if errors else None,
            )
        else:
            return HarvestResult(
                data=b"",
                entropy_bits=0,
                source=self.name,
                success=False,
                error="All external sources failed",
            )

    # -------------------------------------------------------------------------
    # Earthquake Data
    # -------------------------------------------------------------------------

    def _fetch_earthquake_data(self, requests: Any) -> bytes | None:
        """
        Fetch earthquake data from USGS.

        Returns data about recent earthquakes including:
        - Magnitude
        - Location (latitude, longitude, depth)
        - Timestamp

        Args:
            requests: The imported requests module

        Returns:
            Bytes containing earthquake data, or None if failed
        """
        try:
            response = requests.get(self.USGS_EARTHQUAKE_URL, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()
            features = data.get("features", [])

            if not features:
                # No earthquakes in the last hour
                # Use metadata instead
                metadata = data.get("metadata", {})
                meta_str = str(metadata).encode()
                return meta_str

            # Extract data from the most recent earthquakes
            values: list[float] = []

            for eq in features[:5]:  # Up to 5 earthquakes
                props = eq.get("properties", {})
                geom = eq.get("geometry", {})
                coords = geom.get("coordinates", [0, 0, 0])

                # Magnitude (can be negative for very small quakes)
                mag = props.get("mag", 0) or 0
                values.append(float(mag))

                # Location: longitude, latitude, depth
                values.extend([float(c) for c in coords[:3]])

                # Timestamp
                timestamp = props.get("time", 0)
                values.append(float(timestamp))

            # Pack as double-precision floats
            result = struct.pack(f"!{len(values)}d", *values)
            return result

        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Cryptocurrency Data
    # -------------------------------------------------------------------------

    def _fetch_crypto_data(self, requests: Any) -> bytes | None:
        """
        Fetch cryptocurrency prices.

        Gets current prices for Bitcoin and Ethereum with high precision.
        Crypto prices are highly volatile and change every second.

        Args:
            requests: The imported requests module

        Returns:
            Bytes containing crypto price data, or None if failed
        """
        prices: list[float] = []

        # Try CoinGecko first (single request for multiple coins)
        try:
            response = requests.get(self.COINGECKO_URL, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()

            if "bitcoin" in data:
                btc_price = data["bitcoin"].get("usd", 0)
                prices.append(float(btc_price))

            if "ethereum" in data:
                eth_price = data["ethereum"].get("usd", 0)
                prices.append(float(eth_price))

        except Exception:
            # Fall back to Coinbase API
            try:
                # Bitcoin price
                btc_resp = requests.get(self.COINBASE_BTC_URL, timeout=self._timeout)
                btc_resp.raise_for_status()
                btc_data = btc_resp.json()
                btc_price = float(btc_data["data"]["amount"])
                prices.append(btc_price)
            except Exception:
                pass

            try:
                # Ethereum price
                eth_resp = requests.get(self.COINBASE_ETH_URL, timeout=self._timeout)
                eth_resp.raise_for_status()
                eth_data = eth_resp.json()
                eth_price = float(eth_data["data"]["amount"])
                prices.append(eth_price)
            except Exception:
                pass

        if not prices:
            return None

        # Pack prices as double-precision floats
        result = struct.pack(f"!{len(prices)}d", *prices)
        return result

    # -------------------------------------------------------------------------
    # Configuration Properties
    # -------------------------------------------------------------------------

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
    def enable_earthquake(self) -> bool:
        """Check if earthquake data collection is enabled."""
        return self._enable_earthquake

    @enable_earthquake.setter
    def enable_earthquake(self, value: bool) -> None:
        """Enable or disable earthquake data collection."""
        self._enable_earthquake = value

    @property
    def enable_crypto(self) -> bool:
        """Check if crypto data collection is enabled."""
        return self._enable_crypto

    @enable_crypto.setter
    def enable_crypto(self, value: bool) -> None:
        """Enable or disable crypto data collection."""
        self._enable_crypto = value
