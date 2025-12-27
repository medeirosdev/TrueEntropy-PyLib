# =============================================================================
# TrueEntropy - Base Harvester Class
# =============================================================================
#
# This module defines the abstract base class for all entropy harvesters.
# All harvester implementations must inherit from BaseHarvester and implement
# the collect() method.
#
# Design Philosophy:
# - Harvesters are independent and can fail gracefully
# - Each harvester provides an entropy estimate for its data
# - Harvesters should be lightweight and non-blocking when possible
#
# =============================================================================

"""
Abstract base class for entropy harvesters.

All harvester implementations must inherit from BaseHarvester and
implement the collect() method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class HarvestResult:
    """
    Result of an entropy harvest operation.

    Attributes:
        data: Raw bytes collected from the source
        entropy_bits: Conservative estimate of entropy bits in the data
        source: Name of the source that provided the data
        success: Whether the harvest was successful
        error: Error message if harvest failed, None otherwise
    """

    data: bytes
    entropy_bits: int
    source: str
    success: bool
    error: str | None = None


class BaseHarvester(ABC):
    """
    Abstract base class for entropy harvesters.

    Harvesters are responsible for collecting entropy from various sources
    and packaging it for the entropy pool. Each harvester should:

    1. Collect data from its source (timing, network, system, etc.)
    2. Convert the data to bytes
    3. Estimate the entropy content
    4. Return a HarvestResult

    Subclasses MUST implement:
    - name property: Returns the harvester's name
    - collect() method: Performs the actual collection

    Example:
        >>> class MyHarvester(BaseHarvester):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_harvester"
        ...
        ...     def collect(self) -> HarvestResult:
        ...         data = b"some entropy"
        ...         return HarvestResult(
        ...             data=data,
        ...             entropy_bits=8,
        ...             source=self.name,
        ...             success=True
        ...         )
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of this harvester.

        This is used for logging and identification.
        Names should be lowercase with underscores.

        Returns:
            The harvester's name (e.g., "timing", "network")
        """
        ...

    @abstractmethod
    def collect(self) -> HarvestResult:
        """
        Collect entropy from this source.

        This method should:
        1. Gather data from the entropy source
        2. Convert it to a bytes object
        3. Estimate the entropy content
        4. Return a HarvestResult

        If collection fails, return a HarvestResult with:
        - success=False
        - error="description of what went wrong"
        - data=b"" (empty bytes)
        - entropy_bits=0

        Returns:
            HarvestResult containing the collected entropy
        """
        ...

    def safe_collect(self) -> HarvestResult:
        """
        Safely collect entropy, catching any exceptions.

        This wrapper ensures that harvester failures don't crash
        the entropy collection system. Any exception is caught
        and converted to a failed HarvestResult.

        Returns:
            HarvestResult (always succeeds, but may indicate failure)
        """
        try:
            return self.collect()
        except Exception as e:
            return HarvestResult(
                data=b"", entropy_bits=0, source=self.name, success=False, error=str(e)
            )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(name={self.name!r})"
