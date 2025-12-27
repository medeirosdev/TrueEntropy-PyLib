#!/usr/bin/env python3
# =============================================================================
# TrueEntropy - Example Usage
# =============================================================================
#
# This script demonstrates the main features of the TrueEntropy library.
# Run it to see true random numbers generated from real-world entropy sources.
#
# =============================================================================

"""
Example script demonstrating TrueEntropy usage.

This script shows how to:
1. Generate various types of random values
2. Check entropy pool health
3. Use the background collector
4. Feed custom entropy
"""

import trueentropy


def main() -> None:
    """Run the TrueEntropy demonstration."""
    
    print("=" * 60)
    print(" TrueEntropy - True Randomness from the Real World")
    print("=" * 60)
    print()
    
    # -------------------------------------------------------------------------
    # Basic Random Value Generation
    # -------------------------------------------------------------------------
    
    print("[*] Basic Random Values")
    print("-" * 40)
    
    # Random float between 0 and 1
    random_float = trueentropy.random()
    print(f"  Random float [0, 1):    {random_float:.10f}")
    
    # Random integer in a range
    random_int = trueentropy.randint(1, 100)
    print(f"  Random int [1, 100]:    {random_int}")
    
    # Random boolean (coin flip)
    coin_flip = trueentropy.randbool()
    print(f"  Coin flip:              {'Heads' if coin_flip else 'Tails'}")
    
    # Random bytes
    random_bytes = trueentropy.randbytes(16)
    print(f"  Random 16 bytes:        {random_bytes.hex()}")
    
    print()
    
    # -------------------------------------------------------------------------
    # Sequence Operations
    # -------------------------------------------------------------------------
    
    print("[*] Sequence Operations")
    print("-" * 40)
    
    # Random choice from a list
    colors = ["Red", "Green", "Blue", "Yellow", "Purple"]
    chosen_color = trueentropy.choice(colors)
    print(f"  Random color:           {chosen_color}")
    
    # Shuffle a list
    cards = ["A", "K", "Q", "J", "10"]
    print(f"  Original cards:         {cards}")
    trueentropy.shuffle(cards)
    print(f"  Shuffled cards:         {cards}")
    
    # Sample without replacement
    lottery_numbers = trueentropy.sample(range(1, 50), 6)
    lottery_numbers.sort()
    print(f"  Lottery (6 from 49):    {lottery_numbers}")
    
    print()
    
    # -------------------------------------------------------------------------
    # Dice Rolling Demonstration
    # -------------------------------------------------------------------------
    
    print("[*] Dice Rolling (100 rolls)")
    print("-" * 40)
    
    # Roll a 6-sided die 100 times
    rolls = [trueentropy.randint(1, 6) for _ in range(100)]
    
    # Count occurrences
    from collections import Counter
    counts = Counter(rolls)
    
    for face in range(1, 7):
        bar = "#" * (counts[face] // 2)
        print(f"  Face {face}: {counts[face]:2d} {bar}")
    
    print()
    
    # -------------------------------------------------------------------------
    # Entropy Health Check
    # -------------------------------------------------------------------------
    
    print("[*] Entropy Pool Health")
    print("-" * 40)
    
    health = trueentropy.health()
    
    # Create visual health bar
    filled = health["score"] // 10
    bar = "#" * filled + "." * (10 - filled)
    
    status_symbol = {
        "healthy": "[OK]",
        "degraded": "[WARN]",
        "critical": "[CRIT]"
    }
    
    print(f"  Score:          [{bar}] {health['score']}/100")
    print(f"  Status:         {status_symbol.get(health['status'], '?')} {health['status'].upper()}")
    print(f"  Entropy bits:   {health['entropy_bits']}")
    print(f"  Pool usage:     {health['pool_utilization']:.1f}%")
    print()
    print(f"  Tip: {health['recommendation']}")
    
    print()
    
    # -------------------------------------------------------------------------
    # Password Generator Example
    # -------------------------------------------------------------------------
    
    print("[*] Password Generator")
    print("-" * 40)
    
    # Generate a strong random password
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(trueentropy.choice(alphabet) for _ in range(16))
    print(f"  Random password:  {password}")
    
    # Generate a passphrase
    words = ["apple", "banana", "cherry", "dragon", "eagle", "falcon",
             "garden", "harbor", "island", "jungle", "kingdom", "lemon"]
    passphrase = "-".join(trueentropy.sample(words, 4))
    print(f"  Passphrase:       {passphrase}")
    
    print()
    
    # -------------------------------------------------------------------------
    # UUID-like Token Generator
    # -------------------------------------------------------------------------
    
    print("[*] Token Generator")
    print("-" * 40)
    
    token = trueentropy.randbytes(16).hex()
    formatted = f"{token[:8]}-{token[8:12]}-{token[12:16]}-{token[16:20]}-{token[20:]}"
    print(f"  Random token:     {formatted}")
    
    print()
    print("=" * 60)
    print(" All random values above were generated from real-world")
    print(" entropy sources: CPU timing, network latency, and more!")
    print("=" * 60)


if __name__ == "__main__":
    main()
