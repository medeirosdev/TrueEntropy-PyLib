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
#
# =============================================================================

"""
Entropy harvesters - collectors of real-world randomness.

This package contains various harvester classes that collect entropy
from different sources and feed it into the entropy pool.
"""

from trueentropy.harvesters.base import BaseHarvester
from trueentropy.harvesters.timing import TimingHarvester
from trueentropy.harvesters.network import NetworkHarvester
from trueentropy.harvesters.system import SystemHarvester
from trueentropy.harvesters.external import ExternalHarvester

__all__ = [
    "BaseHarvester",
    "TimingHarvester",
    "NetworkHarvester",
    "SystemHarvester",
    "ExternalHarvester",
]
