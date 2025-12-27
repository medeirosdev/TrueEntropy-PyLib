# =============================================================================
# TrueEntropy - Harvesters Package
# =============================================================================
#
# Harvesters are the entropy collectors - they gather randomness from various
# real-world sources and feed it into the entropy pool.
#
# Available Harvesters:
# - TimingHarvester: CPU jitter and scheduling randomness
# - NetworkHarvester: Network latency measurements
# - SystemHarvester: System state (RAM, processes, etc.)
# - ExternalHarvester: External APIs (earthquakes, crypto prices)
# - WeatherHarvester: Weather data (temperature, humidity, pressure)
# - RadioactiveHarvester: random.org / ANU QRNG (quantum randomness)
#
# =============================================================================

"""
Entropy harvesters - collectors of real-world randomness.

This package contains various harvester classes that collect entropy
from different sources and feed it into the entropy pool.
"""

from trueentropy.harvesters.base import BaseHarvester
from trueentropy.harvesters.external import ExternalHarvester
from trueentropy.harvesters.network import NetworkHarvester
from trueentropy.harvesters.radioactive import RadioactiveHarvester
from trueentropy.harvesters.system import SystemHarvester
from trueentropy.harvesters.timing import TimingHarvester
from trueentropy.harvesters.weather import WeatherHarvester

__all__ = [
    "BaseHarvester",
    "TimingHarvester",
    "NetworkHarvester",
    "SystemHarvester",
    "ExternalHarvester",
    "WeatherHarvester",
    "RadioactiveHarvester",
]
