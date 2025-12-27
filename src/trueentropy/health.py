# =============================================================================
# TrueEntropy - Health Monitoring Module
# =============================================================================
#
# This module provides entropy pool health monitoring. It evaluates the
# current state of the pool and returns a health score along with
# recommendations for improvement.
#
# Health Factors:
# - Entropy bits remaining in the pool
# - Time since last entropy feed
# - Ratio of extraction to feeding
#
# =============================================================================

"""
Health monitoring for the TrueEntropy entropy pool.

Provides functions to assess the current state of entropy collection
and suggest improvements when entropy levels are low.
"""

from __future__ import annotations

import time
from typing import Literal, TypedDict

from trueentropy.pool import EntropyPool


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

class HealthStatus(TypedDict):
    """
    TypedDict representing the health status of an entropy pool.
    
    Attributes:
        score: Health score from 0 to 100
        status: Current status ("healthy", "degraded", or "critical")
        entropy_bits: Estimated bits of entropy in the pool
        pool_utilization: Percentage of pool capacity used (0-100)
        time_since_feed: Seconds since last entropy feed
        recommendation: Suggested action for the user
    """
    score: int
    status: Literal["healthy", "degraded", "critical"]
    entropy_bits: int
    pool_utilization: float
    time_since_feed: float
    recommendation: str


# -----------------------------------------------------------------------------
# Health Check Function
# -----------------------------------------------------------------------------

def entropy_health(pool: EntropyPool) -> HealthStatus:
    """
    Evaluate the health of an entropy pool.
    
    This function analyzes the current state of the pool and returns
    a comprehensive health status. The health score is calculated based
    on multiple factors:
    
    1. **Entropy Level** (60% weight): How much entropy remains in the pool
    2. **Freshness** (40% weight): Time since the last entropy feed
    
    Score Thresholds:
    - 70-100: Healthy - Pool is operating normally
    - 30-69: Degraded - Pool is usable but consider adding entropy
    - 0-29: Critical - Pool is low on entropy, immediate action needed
    
    Args:
        pool: The EntropyPool instance to evaluate
    
    Returns:
        A HealthStatus dictionary with detailed health information
    
    Example:
        >>> from trueentropy import get_pool
        >>> from trueentropy.health import entropy_health
        >>> pool = get_pool()
        >>> status = entropy_health(pool)
        >>> print(f"Health: {status['score']}/100 ({status['status']})")
        Health: 85/100 (healthy)
    """
    # -------------------------------------------------------------------------
    # Gather Pool Statistics
    # -------------------------------------------------------------------------
    
    # Get current entropy level
    entropy_bits = pool.entropy_bits
    max_entropy = pool.POOL_SIZE * 8  # 512 * 8 = 4096 bits
    
    # Calculate pool utilization percentage
    pool_utilization = (entropy_bits / max_entropy) * 100
    
    # Calculate time since last feed
    time_since_feed = time.time() - pool.last_feed_time
    
    # -------------------------------------------------------------------------
    # Calculate Component Scores
    # -------------------------------------------------------------------------
    
    # Entropy level score (0-100)
    # Full pool = 100, empty pool = 0
    entropy_score = min(100, int(pool_utilization))
    
    # Freshness score (0-100)
    # Just fed = 100, stale (> 60 seconds) = 0
    # We use an exponential decay: score = 100 * e^(-t/30)
    # This gives:
    #   - 0 seconds: 100
    #   - 30 seconds: ~37
    #   - 60 seconds: ~14
    #   - 120 seconds: ~2
    import math
    freshness_score = int(100 * math.exp(-time_since_feed / 30))
    freshness_score = max(0, min(100, freshness_score))
    
    # -------------------------------------------------------------------------
    # Calculate Overall Score
    # -------------------------------------------------------------------------
    
    # Weighted average: 60% entropy level, 40% freshness
    # This prioritizes having entropy in the pool, but also rewards
    # regular feeding to maintain diversity
    overall_score = int(0.6 * entropy_score + 0.4 * freshness_score)
    overall_score = max(0, min(100, overall_score))
    
    # -------------------------------------------------------------------------
    # Determine Status and Recommendation
    # -------------------------------------------------------------------------
    
    if overall_score >= 70:
        status: Literal["healthy", "degraded", "critical"] = "healthy"
        recommendation = (
            "Entropy pool is healthy and ready for use. "
            "All systems operating normally."
        )
    elif overall_score >= 30:
        status = "degraded"
        
        # Provide specific recommendations based on what's low
        if entropy_score < 50:
            recommendation = (
                "Entropy level is moderate. Consider starting the background "
                "collector with trueentropy.start_collector() or manually "
                "feeding entropy with trueentropy.feed()."
            )
        else:
            recommendation = (
                "Pool hasn't been fed recently. Consider enabling the "
                "background collector for continuous entropy replenishment."
            )
    else:
        status = "critical"
        
        if entropy_score < 20:
            recommendation = (
                "CRITICAL: Entropy pool is nearly empty! Random values may "
                "have reduced quality. Immediately start the collector with "
                "trueentropy.start_collector() or call pool.reseed()."
            )
        else:
            recommendation = (
                "WARNING: Pool has been stale for too long. Start the "
                "background collector to ensure entropy diversity."
            )
    
    # -------------------------------------------------------------------------
    # Build and Return Result
    # -------------------------------------------------------------------------
    
    return HealthStatus(
        score=overall_score,
        status=status,
        entropy_bits=entropy_bits,
        pool_utilization=round(pool_utilization, 2),
        time_since_feed=round(time_since_feed, 2),
        recommendation=recommendation,
    )


def print_health_report(pool: EntropyPool) -> None:
    """
    Print a formatted health report to stdout.
    
    This is a convenience function for debugging and monitoring.
    It prints a human-readable summary of the pool health.
    
    Args:
        pool: The EntropyPool instance to report on
    
    Example:
        >>> from trueentropy import get_pool
        >>> from trueentropy.health import print_health_report
        >>> print_health_report(get_pool())
        
        ╔══════════════════════════════════════════╗
        ║       TrueEntropy Health Report          ║
        ╠══════════════════════════════════════════╣
        ║ Score:        85/100 [████████░░] healthy║
        ║ Entropy:      3276 bits (80.0%)          ║
        ║ Last Feed:    5.2 seconds ago            ║
        ╠══════════════════════════════════════════╣
        ║ ✓ Pool is healthy and ready for use.     ║
        ╚══════════════════════════════════════════╝
    """
    health = entropy_health(pool)
    
    # Create progress bar
    filled = health["score"] // 10
    bar = "█" * filled + "░" * (10 - filled)
    
    # Status emoji
    if health["status"] == "healthy":
        emoji = "✓"
    elif health["status"] == "degraded":
        emoji = "⚠"
    else:
        emoji = "✗"
    
    # Print report
    print()
    print("╔══════════════════════════════════════════╗")
    print("║       TrueEntropy Health Report          ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║ Score:        {health['score']:3d}/100 [{bar}] {health['status']:8}║")
    print(f"║ Entropy:      {health['entropy_bits']:4d} bits ({health['pool_utilization']:.1f}%)          ║")
    print(f"║ Last Feed:    {health['time_since_feed']:.1f} seconds ago            ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║ {emoji} {health['recommendation'][:40]:40}║")
    print("╚══════════════════════════════════════════╝")
    print()
