# =============================================================================
# TrueEntropy - Background Collector Module
# =============================================================================
#
# This module provides the background entropy collection thread. It runs
# silently in the background, periodically harvesting entropy from all
# available sources and feeding it into the pool.
#
# Benefits:
# - Pool stays full even during heavy random number generation
# - Entropy is collected from diverse sources over time
# - Users don't need to manually manage entropy collection
#
# Usage:
#     from trueentropy import start_collector, stop_collector
#     
#     start_collector(interval=2.0)  # Collect every 2 seconds
#     # ... application runs ...
#     stop_collector()  # Clean shutdown
#
# =============================================================================

"""
Background entropy collector thread.

Provides automatic, continuous entropy collection from all available
sources, keeping the entropy pool full.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import List, Optional

from trueentropy.pool import EntropyPool
from trueentropy.harvesters.base import BaseHarvester, HarvestResult
from trueentropy.harvesters.timing import TimingHarvester
from trueentropy.harvesters.network import NetworkHarvester
from trueentropy.harvesters.system import SystemHarvester
from trueentropy.harvesters.external import ExternalHarvester


# -----------------------------------------------------------------------------
# Module-level Logger
# -----------------------------------------------------------------------------

logger = logging.getLogger("trueentropy.collector")


# -----------------------------------------------------------------------------
# Global State
# -----------------------------------------------------------------------------

# The collector thread (None if not running)
_collector_thread: Optional[threading.Thread] = None

# Event to signal the collector to stop
_stop_event: Optional[threading.Event] = None


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------

def start_background_collector(
    pool: EntropyPool,
    interval: float = 1.0,
    enable_network: bool = True,
    enable_external: bool = True
) -> None:
    """
    Start the background entropy collector thread.
    
    The collector runs in a daemon thread, periodically harvesting
    entropy from all available sources and feeding it into the pool.
    
    Args:
        pool: The EntropyPool to feed entropy into
        interval: Seconds between collection cycles (default: 1.0)
        enable_network: Whether to enable network harvester (default: True)
        enable_external: Whether to enable external API harvester (default: True)
    
    Note:
        - Only one collector can run at a time
        - The collector is a daemon thread (exits when main program exits)
        - Call stop_background_collector() for clean shutdown
    
    Example:
        >>> from trueentropy import get_pool
        >>> from trueentropy.collector import start_background_collector
        >>> pool = get_pool()
        >>> start_background_collector(pool, interval=2.0)
    """
    global _collector_thread, _stop_event
    
    # Check if already running
    if _collector_thread is not None and _collector_thread.is_alive():
        logger.warning("Background collector is already running")
        return
    
    # Create stop event
    _stop_event = threading.Event()
    
    # Create and configure harvesters
    harvesters: List[BaseHarvester] = [
        TimingHarvester(),
        SystemHarvester(),
    ]
    
    if enable_network:
        harvesters.append(NetworkHarvester())
    
    if enable_external:
        harvesters.append(ExternalHarvester())
    
    # Create collector thread
    _collector_thread = threading.Thread(
        target=_collector_loop,
        args=(pool, harvesters, interval, _stop_event),
        name="TrueEntropy-Collector",
        daemon=True  # Allows clean exit when main program ends
    )
    
    # Start the thread
    _collector_thread.start()
    logger.info(
        f"Background collector started with {len(harvesters)} harvesters, "
        f"interval={interval}s"
    )


def stop_background_collector(timeout: float = 5.0) -> bool:
    """
    Stop the background entropy collector thread.
    
    Signals the collector to stop and waits for it to finish.
    
    Args:
        timeout: Maximum seconds to wait for thread to stop
    
    Returns:
        True if the collector stopped cleanly, False if it timed out
    
    Example:
        >>> from trueentropy.collector import stop_background_collector
        >>> success = stop_background_collector()
        >>> print("Stopped cleanly" if success else "Timeout")
    """
    global _collector_thread, _stop_event
    
    if _collector_thread is None or not _collector_thread.is_alive():
        logger.debug("Background collector is not running")
        return True
    
    if _stop_event is None:
        logger.error("Stop event is None but thread is running")
        return False
    
    # Signal the collector to stop
    _stop_event.set()
    logger.debug("Stop signal sent to collector")
    
    # Wait for thread to finish
    _collector_thread.join(timeout=timeout)
    
    if _collector_thread.is_alive():
        logger.warning(f"Collector did not stop within {timeout}s")
        return False
    
    logger.info("Background collector stopped")
    
    # Clean up
    _collector_thread = None
    _stop_event = None
    
    return True


def is_collector_running() -> bool:
    """
    Check if the background collector is currently running.
    
    Returns:
        True if the collector thread is alive
    """
    return _collector_thread is not None and _collector_thread.is_alive()


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------

def _collector_loop(
    pool: EntropyPool,
    harvesters: List[BaseHarvester],
    interval: float,
    stop_event: threading.Event
) -> None:
    """
    Main loop for the background collector thread.
    
    This function runs in a separate thread, periodically calling
    each harvester and feeding the results into the pool.
    
    Args:
        pool: The EntropyPool to feed entropy into
        harvesters: List of harvesters to use
        interval: Seconds between collection cycles
        stop_event: Event to signal when to stop
    """
    logger.debug("Collector loop started")
    
    while not stop_event.is_set():
        # Track timing for this cycle
        cycle_start = time.perf_counter()
        
        # Collect from all harvesters
        total_bits = 0
        successful = 0
        
        for harvester in harvesters:
            # Use safe_collect to handle any exceptions
            result = harvester.safe_collect()
            
            if result.success:
                # Feed the collected entropy into the pool
                pool.feed(result.data, entropy_estimate=result.entropy_bits)
                total_bits += result.entropy_bits
                successful += 1
                logger.debug(
                    f"Harvester '{result.source}' collected "
                    f"{result.entropy_bits} bits"
                )
            else:
                logger.debug(
                    f"Harvester '{result.source}' failed: {result.error}"
                )
        
        # Log cycle summary
        cycle_time = time.perf_counter() - cycle_start
        logger.debug(
            f"Collection cycle complete: {successful}/{len(harvesters)} "
            f"harvesters, {total_bits} bits, {cycle_time:.3f}s"
        )
        
        # Wait for the next cycle (or until stop is signaled)
        # We use wait() instead of sleep() so we can respond to stop quickly
        remaining_interval = max(0, interval - cycle_time)
        stop_event.wait(timeout=remaining_interval)
    
    logger.debug("Collector loop exiting")


def collect_once(pool: EntropyPool) -> int:
    """
    Perform a single collection cycle.
    
    This is useful for manually triggering collection without
    running the background thread.
    
    Args:
        pool: The EntropyPool to feed entropy into
    
    Returns:
        Total entropy bits collected
    """
    harvesters: List[BaseHarvester] = [
        TimingHarvester(),
        SystemHarvester(),
        NetworkHarvester(),
        ExternalHarvester(),
    ]
    
    total_bits = 0
    
    for harvester in harvesters:
        result = harvester.safe_collect()
        
        if result.success:
            pool.feed(result.data, entropy_estimate=result.entropy_bits)
            total_bits += result.entropy_bits
    
    return total_bits
