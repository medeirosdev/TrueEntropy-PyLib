# =============================================================================
# TrueEntropy - Lazy Harvester Loading Module
# =============================================================================
#
# This module provides lazy loading for harvesters.
# Harvesters are only instantiated when first accessed, reducing startup
# time and memory usage for applications that don't need all harvesters.
#
# Usage:
#     from trueentropy.lazy import LazyHarvesters
#
#     harvesters = LazyHarvesters()
#
#     # Harvester is only created when accessed
#     timing = harvesters.timing  # Creates TimingHarvester
#     result = timing.collect()
#
# =============================================================================

"""
Lazy harvester loading - load harvesters only when needed.

This module provides lazy initialization of harvesters to reduce
startup time and memory usage.
"""

from __future__ import annotations

from trueentropy.harvesters.base import BaseHarvester


class LazyHarvesters:
    """
    Lazy-loading container for entropy harvesters.

    Harvesters are only instantiated when first accessed, reducing
    startup time and memory usage. This is especially useful for
    harvesters that require heavy imports (like psutil for system
    metrics or requests for network calls).

    Example:
        >>> harvesters = LazyHarvesters()
        >>>
        >>> # Nothing loaded yet
        >>> print(harvesters.loaded)  # []
        >>>
        >>> # Timing harvester loaded on first access
        >>> timing = harvesters.timing
        >>> print(harvesters.loaded)  # ['timing']
    """

    # Registry of available harvesters
    _REGISTRY: dict[str, str] = {
        "timing": "trueentropy.harvesters.timing.TimingHarvester",
        "system": "trueentropy.harvesters.system.SystemHarvester",
        "network": "trueentropy.harvesters.network.NetworkHarvester",
        "external": "trueentropy.harvesters.external.ExternalHarvester",
        "weather": "trueentropy.harvesters.weather.WeatherHarvester",
        "radioactive": "trueentropy.harvesters.radioactive.RadioactiveHarvester",
    }

    def __init__(self) -> None:
        """Initialize the lazy harvester container."""
        self._instances: dict[str, BaseHarvester] = {}
        self._configs: dict[str, dict] = {}

    def configure(self, name: str, **kwargs) -> None:
        """
        Pre-configure a harvester before it's loaded.

        Args:
            name: Harvester name
            **kwargs: Configuration options to pass to the constructor

        Example:
            >>> harvesters = LazyHarvesters()
            >>> harvesters.configure("weather", api_key="your_key")
            >>> # When accessed, WeatherHarvester will use the api_key
            >>> weather = harvesters.weather
        """
        self._configs[name] = kwargs

    def _load(self, name: str) -> BaseHarvester:
        """
        Load a harvester by name.

        Args:
            name: Harvester name from the registry

        Returns:
            The loaded harvester instance

        Raises:
            KeyError: If harvester name is not in registry
            ImportError: If the harvester module cannot be imported
        """
        if name not in self._REGISTRY:
            raise KeyError(f"Unknown harvester: {name}")

        if name not in self._instances:
            # Import the module and class
            full_path = self._REGISTRY[name]
            module_path, class_name = full_path.rsplit(".", 1)

            # Dynamic import
            import importlib

            module = importlib.import_module(module_path)
            harvester_class = getattr(module, class_name)

            # Get configuration if any
            config = self._configs.get(name, {})

            # Instantiate
            self._instances[name] = harvester_class(**config)

        return self._instances[name]

    @property
    def timing(self) -> BaseHarvester:
        """Get the TimingHarvester (lazy loaded)."""
        return self._load("timing")

    @property
    def system(self) -> BaseHarvester:
        """Get the SystemHarvester (lazy loaded)."""
        return self._load("system")

    @property
    def network(self) -> BaseHarvester:
        """Get the NetworkHarvester (lazy loaded)."""
        return self._load("network")

    @property
    def external(self) -> BaseHarvester:
        """Get the ExternalHarvester (lazy loaded)."""
        return self._load("external")

    @property
    def weather(self) -> BaseHarvester:
        """Get the WeatherHarvester (lazy loaded)."""
        return self._load("weather")

    @property
    def radioactive(self) -> BaseHarvester:
        """Get the RadioactiveHarvester (lazy loaded)."""
        return self._load("radioactive")

    def get(self, name: str) -> BaseHarvester:
        """
        Get a harvester by name (lazy loaded).

        Args:
            name: Harvester name

        Returns:
            The harvester instance
        """
        return self._load(name)

    @property
    def loaded(self) -> list[str]:
        """Get list of currently loaded harvester names."""
        return list(self._instances.keys())

    @property
    def available(self) -> list[str]:
        """Get list of available harvester names."""
        return list(self._REGISTRY.keys())

    def unload(self, name: str) -> None:
        """
        Unload a harvester to free memory.

        Args:
            name: Harvester name to unload
        """
        if name in self._instances:
            del self._instances[name]

    def unload_all(self) -> None:
        """Unload all harvesters."""
        self._instances.clear()

    def collect_all(self, only_loaded: bool = False) -> list:
        """
        Collect entropy from all harvesters.

        Args:
            only_loaded: If True, only collect from already-loaded harvesters

        Returns:
            List of HarvestResult objects
        """
        results = []

        names = self.loaded if only_loaded else self.available

        for name in names:
            try:
                harvester = self._load(name)
                result = harvester.safe_collect()
                results.append(result)
            except Exception:
                continue

        return results


# =============================================================================
# Global Instance
# =============================================================================

_lazy_harvesters: LazyHarvesters | None = None


def get_lazy_harvesters() -> LazyHarvesters:
    """
    Get the global LazyHarvesters instance.

    Returns:
        The global LazyHarvesters singleton
    """
    global _lazy_harvesters
    if _lazy_harvesters is None:
        _lazy_harvesters = LazyHarvesters()
    return _lazy_harvesters


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "LazyHarvesters",
    "get_lazy_harvesters",
]
