# =============================================================================
# TrueEntropy - Weather Harvester
# =============================================================================
#
# This harvester collects entropy from weather data via OpenWeatherMap API.
# Weather conditions are inherently chaotic and provide excellent entropy.
#
# Data Sources:
# - Temperature (with decimal precision)
# - Humidity percentage
# - Atmospheric pressure
# - Wind speed and direction
# - Cloud coverage
# - Visibility
#
# Why Weather Data is Random:
# - Atmospheric conditions are chaotic systems
# - Measurements vary constantly
# - Multiple independent variables
# - Physical phenomena outside computer control
#
# Note: Requires free OpenWeatherMap API key for full functionality.
# Without API key, uses fallback public endpoints.
#
# =============================================================================

"""
Weather-based entropy harvester.

Collects entropy from real-time weather data including temperature,
humidity, pressure, wind, and other atmospheric conditions.
"""

from __future__ import annotations

import hashlib
import struct
import time
from typing import Any

from trueentropy.harvesters.base import BaseHarvester, HarvestResult


class WeatherHarvester(BaseHarvester):
    """
    Harvests entropy from weather data via OpenWeatherMap API.

    Weather conditions are determined by chaotic atmospheric systems,
    making them an excellent source of real-world entropy. This harvester
    collects multiple weather metrics and combines them.

    Metrics collected:
    - Temperature (Kelvin, with decimals)
    - Feels-like temperature
    - Humidity percentage
    - Atmospheric pressure (hPa)
    - Wind speed and direction
    - Cloud coverage percentage
    - Visibility distance

    Attributes:
        api_key: OpenWeatherMap API key (optional, uses fallback if not set)
        cities: List of city IDs to query
        timeout: Request timeout in seconds

    Example:
        >>> # With API key (recommended)
        >>> harvester = WeatherHarvester(api_key="your_api_key")
        >>> result = harvester.collect()
        >>>
        >>> # Without API key (uses fallback cities)
        >>> harvester = WeatherHarvester()
        >>> result = harvester.collect()
    """

    # -------------------------------------------------------------------------
    # API Configuration
    # -------------------------------------------------------------------------

    # OpenWeatherMap API endpoint
    OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

    # Default cities to query (major world cities with different climates)
    # Using city IDs for reliability
    DEFAULT_CITIES: list[dict[str, Any]] = [
        {"name": "London", "lat": 51.5074, "lon": -0.1278},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
        {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333},
    ]

    # Fallback: wttr.in provides weather without API key
    WTTR_URL = "https://wttr.in/{city}?format=j1"

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def __init__(
        self,
        api_key: str | None = None,
        cities: list[dict[str, Any]] | None = None,
        timeout: float = 5.0,
    ) -> None:
        """
        Initialize the weather harvester.

        Args:
            api_key: OpenWeatherMap API key. If not provided, uses wttr.in
                    fallback which doesn't require authentication.
            cities: List of cities to query. Each city should have 'lat' and
                   'lon' keys for coordinates. If not provided, uses defaults.
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key
        self._cities = cities or self.DEFAULT_CITIES.copy()
        self._timeout = timeout

    # -------------------------------------------------------------------------
    # BaseHarvester Implementation
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return harvester name."""
        return "weather"

    def collect(self) -> HarvestResult:
        """
        Collect entropy from weather data.

        Process:
        1. Query weather data for multiple cities
        2. Extract numeric values from responses
        3. Pack values into bytes
        4. Hash for uniform distribution

        Returns:
            HarvestResult containing weather entropy
        """
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

        collected_values: list[float] = []

        if self._api_key:
            # Use OpenWeatherMap API
            collected_values = self._fetch_openweather(requests)
        else:
            # Use wttr.in fallback (no API key needed)
            collected_values = self._fetch_wttr(requests)

        if not collected_values:
            return HarvestResult(
                data=b"",
                entropy_bits=0,
                source=self.name,
                success=False,
                error="No weather data available",
            )

        # Add timestamp for freshness
        collected_values.append(float(time.time_ns()))

        # Pack as double-precision floats
        data = struct.pack(f"!{len(collected_values)}d", *collected_values)

        # Hash for uniform distribution
        hashed = hashlib.sha256(data).digest()

        # Estimate entropy: ~4 bits per weather metric
        entropy_bits = len(collected_values) * 4

        return HarvestResult(
            data=data + hashed, entropy_bits=entropy_bits, source=self.name, success=True
        )

    # -------------------------------------------------------------------------
    # OpenWeatherMap API
    # -------------------------------------------------------------------------

    def _fetch_openweather(self, requests: Any) -> list[float]:
        """
        Fetch weather data from OpenWeatherMap API.

        Args:
            requests: The imported requests module

        Returns:
            List of weather values as floats
        """
        values: list[float] = []

        for city in self._cities[:3]:  # Limit to 3 cities to avoid rate limits
            try:
                params = {
                    "lat": city["lat"],
                    "lon": city["lon"],
                    "appid": self._api_key,
                    "units": "metric",
                }

                response = requests.get(
                    self.OPENWEATHER_API_URL, params=params, timeout=self._timeout
                )
                response.raise_for_status()
                data = response.json()

                # Extract weather metrics
                main = data.get("main", {})
                wind = data.get("wind", {})
                clouds = data.get("clouds", {})

                # Temperature values (highly variable)
                values.append(float(main.get("temp", 0)))
                values.append(float(main.get("feels_like", 0)))
                values.append(float(main.get("temp_min", 0)))
                values.append(float(main.get("temp_max", 0)))

                # Atmospheric values
                values.append(float(main.get("pressure", 0)))
                values.append(float(main.get("humidity", 0)))
                values.append(float(main.get("sea_level", 0)))

                # Wind values
                values.append(float(wind.get("speed", 0)))
                values.append(float(wind.get("deg", 0)))
                values.append(float(wind.get("gust", 0)))

                # Cloud coverage
                values.append(float(clouds.get("all", 0)))

                # Visibility
                values.append(float(data.get("visibility", 0)))

                # Coordinates (add precision noise)
                coord = data.get("coord", {})
                values.append(float(coord.get("lat", 0)))
                values.append(float(coord.get("lon", 0)))

            except Exception:
                continue

        return values

    # -------------------------------------------------------------------------
    # wttr.in Fallback (No API Key Required)
    # -------------------------------------------------------------------------

    def _fetch_wttr(self, requests: Any) -> list[float]:
        """
        Fetch weather data from wttr.in (no API key required).

        Args:
            requests: The imported requests module

        Returns:
            List of weather values as floats
        """
        values: list[float] = []

        # Cities for wttr.in
        fallback_cities = ["London", "Tokyo", "Sydney"]

        for city in fallback_cities:
            try:
                url = self.WTTR_URL.format(city=city)

                response = requests.get(
                    url, timeout=self._timeout, headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                data = response.json()

                # Current condition
                current = data.get("current_condition", [{}])[0]

                # Temperature
                values.append(float(current.get("temp_C", 0)))
                values.append(float(current.get("temp_F", 0)))
                values.append(float(current.get("FeelsLikeC", 0)))
                values.append(float(current.get("FeelsLikeF", 0)))

                # Atmospheric
                values.append(float(current.get("humidity", 0)))
                values.append(float(current.get("pressure", 0)))
                values.append(float(current.get("pressureInches", 0)))

                # Wind
                values.append(float(current.get("windspeedKmph", 0)))
                values.append(float(current.get("windspeedMiles", 0)))
                values.append(float(current.get("winddirDegree", 0)))

                # Visibility and clouds
                values.append(float(current.get("visibility", 0)))
                values.append(float(current.get("visibilityMiles", 0)))
                values.append(float(current.get("cloudcover", 0)))

                # UV and precipitation
                values.append(float(current.get("uvIndex", 0)))
                values.append(float(current.get("precipMM", 0)))
                values.append(float(current.get("precipInches", 0)))

            except Exception:
                continue

        return values

    # -------------------------------------------------------------------------
    # Configuration Properties
    # -------------------------------------------------------------------------

    @property
    def api_key(self) -> str | None:
        """Get the API key (masked for security)."""
        if self._api_key:
            return self._api_key[:4] + "..." + self._api_key[-4:]
        return None

    @api_key.setter
    def api_key(self, value: str | None) -> None:
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
