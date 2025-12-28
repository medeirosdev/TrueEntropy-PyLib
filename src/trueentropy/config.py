# =============================================================================
# TrueEntropy - Configuration Module
# =============================================================================
#
# This module provides configuration options for the TrueEntropy library.
# It allows users to enable/disable specific entropy harvesters and
# configure offline mode for environments without network access.
#
# Usage:
#     import trueentropy
#
#     # Enable offline mode (disables all network-dependent harvesters)
#     trueentropy.configure(offline_mode=True)
#
#     # Or configure individual harvesters
#     trueentropy.configure(enable_network=False, enable_weather=False)
#
# =============================================================================

"""
Configuration for TrueEntropy entropy harvesting.

Provides a configuration system to enable/disable individual entropy
sources and support offline mode operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# -----------------------------------------------------------------------------
# Source Metadata
# -----------------------------------------------------------------------------

# Categorize sources by their network requirements
OFFLINE_SOURCES = frozenset({"timing", "system"})
NETWORK_SOURCES = frozenset({"network", "external", "weather", "radioactive"})
ALL_SOURCES = OFFLINE_SOURCES | NETWORK_SOURCES


# -----------------------------------------------------------------------------
# Configuration Dataclass
# -----------------------------------------------------------------------------


@dataclass
class TrueEntropyConfig:
    """
    Configuration for TrueEntropy entropy collection.

    This dataclass holds all configuration options for the library.
    Users can enable/disable individual harvesters or use offline_mode
    to disable all network-dependent sources at once.

    Attributes:
        enable_timing: Enable CPU timing jitter harvester (offline)
        enable_system: Enable system state harvester (offline)
        enable_network: Enable network latency harvester (requires network)
        enable_external: Enable external API harvester (requires network)
        enable_weather: Enable weather data harvester (requires network)
        enable_radioactive: Enable quantum/radioactive harvester (requires network)

    Example:
        >>> from trueentropy.config import TrueEntropyConfig
        >>> config = TrueEntropyConfig(offline_mode=True)
        >>> config.enable_network
        False
    """

    # Offline sources (always available)
    enable_timing: bool = True
    enable_system: bool = True

    # Mode configuration
    mode: Literal["DIRECT", "HYBRID"] = "DIRECT"
    hybrid_reseed_interval: float = 60.0

    # Network-dependent sources
    enable_network: bool = True
    enable_external: bool = True
    enable_weather: bool = True
    enable_radioactive: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Ensure at least one source is enabled (if in DIRECT mode or collecting)
        if not any(self.enabled_sources):
            # In HYBRID mode, we technically need sources too for reseeding,
            # but we could rely on os.urandom initial seed if desperate.
            # For now, strict validation is safer.
            raise ValueError(
                "At least one entropy source must be enabled. " "Cannot disable all harvesters."
            )

        if self.hybrid_reseed_interval <= 0:
            raise ValueError("hybrid_reseed_interval must be positive")

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def offline_mode(self) -> bool:
        """
        Check if running in offline mode.

        Returns True if all network-dependent sources are disabled.
        """
        return not any(
            [
                self.enable_network,
                self.enable_external,
                self.enable_weather,
                self.enable_radioactive,
            ]
        )

    @property
    def enabled_sources(self) -> set[str]:
        """
        Get the set of currently enabled source names.

        Returns:
            Set of enabled source names (e.g., {"timing", "system"})
        """
        sources = set()
        if self.enable_timing:
            sources.add("timing")
        if self.enable_system:
            sources.add("system")
        if self.enable_network:
            sources.add("network")
        if self.enable_external:
            sources.add("external")
        if self.enable_weather:
            sources.add("weather")
        if self.enable_radioactive:
            sources.add("radioactive")
        return sources

    @property
    def disabled_sources(self) -> set[str]:
        """
        Get the set of currently disabled source names.

        Returns:
            Set of disabled source names
        """
        return set(ALL_SOURCES - self.enabled_sources)

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------

    def get_source_info(self, source: str) -> dict[str, bool]:
        """
        Get information about a specific source.

        Args:
            source: Name of the source (e.g., "timing", "network")

        Returns:
            Dict with 'enabled' and 'requires_network' keys
        """
        enabled_map = {
            "timing": self.enable_timing,
            "system": self.enable_system,
            "network": self.enable_network,
            "external": self.enable_external,
            "weather": self.enable_weather,
            "radioactive": self.enable_radioactive,
        }

        return {
            "enabled": enabled_map.get(source, False),
            "requires_network": source in NETWORK_SOURCES,
        }

    def copy(self, **changes: Any) -> TrueEntropyConfig:
        """
        Create a copy of this config with optional changes.

        Args:
            **changes: Config attributes to override

        Returns:
            New TrueEntropyConfig instance
        """
        from dataclasses import asdict

        current = asdict(self)
        current.update(changes)
        return TrueEntropyConfig(**current)


# -----------------------------------------------------------------------------
# Global Configuration
# -----------------------------------------------------------------------------

# Global configuration instance (used by default)
_global_config: TrueEntropyConfig = TrueEntropyConfig()


def get_config() -> TrueEntropyConfig:
    """
    Get the current global configuration.

    Returns:
        The global TrueEntropyConfig instance
    """
    return _global_config


def configure(
    *,
    mode: Literal["DIRECT", "HYBRID"] | None = None,
    hybrid_reseed_interval: float | None = None,
    offline_mode: bool | None = None,
    enable_timing: bool | None = None,
    enable_system: bool | None = None,
    enable_network: bool | None = None,
    enable_external: bool | None = None,
    enable_weather: bool | None = None,
    enable_radioactive: bool | None = None,
) -> TrueEntropyConfig:
    """
    Configure TrueEntropy globally.

    This function updates the global configuration used by all
    entropy collection functions. You can switch modes, set offline_mode
    to disable all network sources, or configure individual sources.

    Args:
        mode: Operation mode ("DIRECT" or "HYBRID")
        hybrid_reseed_interval: Seconds between re-seeds in HYBRID mode
        offline_mode: If True, disables all network-dependent sources.
                     If False, enables all sources. If None, ignored.
        enable_timing: Enable/disable CPU timing harvester
        enable_system: Enable/disable system state harvester
        enable_network: Enable/disable network latency harvester
        enable_external: Enable/disable external API harvester
        enable_weather: Enable/disable weather data harvester
        enable_radioactive: Enable/disable quantum randomness harvester

    Returns:
        The updated global configuration

    Example:
        >>> import trueentropy
        >>> # Enable hybrid mode for better performance
        >>> trueentropy.configure(mode="HYBRID", hybrid_reseed_interval=120)
        >>> # Enable offline mode
        >>> trueentropy.configure(offline_mode=True)
    """
    global _global_config

    # Start with current config values
    new_config = {
        "mode": _global_config.mode,
        "hybrid_reseed_interval": _global_config.hybrid_reseed_interval,
        "enable_timing": _global_config.enable_timing,
        "enable_system": _global_config.enable_system,
        "enable_network": _global_config.enable_network,
        "enable_external": _global_config.enable_external,
        "enable_weather": _global_config.enable_weather,
        "enable_radioactive": _global_config.enable_radioactive,
    }

    if mode is not None:
        new_config["mode"] = mode
    if hybrid_reseed_interval is not None:
        new_config["hybrid_reseed_interval"] = hybrid_reseed_interval

    # Handle offline_mode convenience flag
    if offline_mode is True:
        # Disable all network sources
        new_config["enable_network"] = False
        new_config["enable_external"] = False
        new_config["enable_weather"] = False
        new_config["enable_radioactive"] = False
    elif offline_mode is False:
        # Enable all sources
        new_config["enable_timing"] = True
        new_config["enable_system"] = True
        new_config["enable_network"] = True
        new_config["enable_external"] = True
        new_config["enable_weather"] = True
        new_config["enable_radioactive"] = True

    # Apply individual overrides (these take precedence)
    if enable_timing is not None:
        new_config["enable_timing"] = enable_timing
    if enable_system is not None:
        new_config["enable_system"] = enable_system
    if enable_network is not None:
        new_config["enable_network"] = enable_network
    if enable_external is not None:
        new_config["enable_external"] = enable_external
    if enable_weather is not None:
        new_config["enable_weather"] = enable_weather
    if enable_radioactive is not None:
        new_config["enable_radioactive"] = enable_radioactive

    # Create and validate new config
    _global_config = TrueEntropyConfig(**new_config)

    return _global_config


def reset_config() -> TrueEntropyConfig:
    """
    Reset configuration to defaults (all sources enabled).

    Returns:
        The reset global configuration
    """
    global _global_config
    _global_config = TrueEntropyConfig()
    return _global_config
