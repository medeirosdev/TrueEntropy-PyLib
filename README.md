# TrueEntropy 🎲

[![PyPI version](https://badge.fury.io/py/trueentropy.svg)](https://badge.fury.io/py/trueentropy)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**True randomness from real-world entropy sources.**

TrueEntropy harvests chaos from the physical world to generate truly random numbers. Unlike pseudo-random number generators (PRNGs) that use deterministic algorithms, TrueEntropy collects entropy from:

- ⏱️ **CPU Timing Jitter** - Nanosecond variations in code execution
- 🌐 **Network Latency** - The "weather" of internet infrastructure  
- 💻 **System State** - RAM, processes, and hardware fluctuations
- 🌍 **External APIs** - Seismic activity (USGS), cryptocurrency prices

All entropy sources are mixed using SHA-256 cryptographic hashing, ensuring uniform distribution and unpredictability.

## Installation

```bash
pip install trueentropy
```

## Quick Start

```python
import trueentropy

# Generate a random float [0.0, 1.0)
value = trueentropy.random()
print(f"Random float: {value}")

# Generate a random integer in range [1, 100]
number = trueentropy.randint(1, 100)
print(f"Random integer: {number}")

# Random boolean (coin flip)
coin = trueentropy.randbool()
print(f"Coin flip: {'Heads' if coin else 'Tails'}")

# Random choice from a sequence
colors = ["red", "green", "blue", "yellow"]
color = trueentropy.choice(colors)
print(f"Random color: {color}")

# Generate random bytes
secret = trueentropy.randbytes(32)
print(f"Random bytes: {secret.hex()}")

# Check entropy health
health = trueentropy.health()
print(f"Entropy health: {health['score']}/100 ({health['status']})")
```

## Background Collector

For applications requiring continuous randomness, start the background collector:

```python
import trueentropy

# Start collecting entropy every 2 seconds
trueentropy.start_collector(interval=2.0)

# ... your application code ...

# Generate random numbers (pool is continuously filled)
for _ in range(1000):
    value = trueentropy.random()

# Stop when done
trueentropy.stop_collector()
```

## Entropy Sources

### Timing Jitter
Measures nanosecond variations in CPU execution time. The operating system's scheduler introduces unpredictable delays that are impossible to reproduce.

### Network Latency  
Pings multiple servers (Cloudflare, Google) and measures response times. Network congestion, routing changes, and physical distance create natural randomness.

### System State
Samples volatile system metrics:
- Available RAM (changes constantly)
- Number of running processes
- CPU usage percentages
- System uptime with high precision

### External APIs (Optional)
Fetches real-world data:
- **USGS Earthquake API** - Latest seismic magnitude readings
- **Cryptocurrency prices** - Bitcoin price with 8 decimal precision

## API Reference

### Core Functions

| Function | Description |
|----------|-------------|
| `random()` | Returns float in [0.0, 1.0) |
| `randint(a, b)` | Returns integer in [a, b] |
| `randbool()` | Returns True or False |
| `choice(seq)` | Returns random element from sequence |
| `randbytes(n)` | Returns n random bytes |
| `shuffle(seq)` | Shuffles sequence in-place |

### Management Functions

| Function | Description |
|----------|-------------|
| `health()` | Returns entropy pool health status |
| `start_collector(interval)` | Starts background entropy collection |
| `stop_collector()` | Stops background collection |
| `feed(data)` | Manually feed entropy into the pool |

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTROPY HARVESTERS                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Timing  │ │ Network  │ │  System  │ │   External   │   │
│  │  Jitter  │ │ Latency  │ │  State   │ │     APIs     │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
│       │            │            │              │            │
│       └────────────┴─────┬──────┴──────────────┘            │
│                          ▼                                   │
│                   ┌─────────────┐                           │
│                   │    MIXER    │  SHA-256 Hashing          │
│                   │  (Whitening)│  Avalanche Effect         │
│                   └──────┬──────┘                           │
│                          ▼                                   │
│              ┌───────────────────────┐                      │
│              │     ENTROPY POOL      │  4096 bits           │
│              │   (Accumulated State) │  Thread-safe         │
│              └───────────┬───────────┘                      │
│                          ▼                                   │
│                   ┌─────────────┐                           │
│                   │  EXTRACTOR  │  Secure extraction        │
│                   │    (Tap)    │  Depletion protection     │
│                   └──────┬──────┘                           │
│                          ▼                                   │
│         ┌────────────────┴────────────────┐                 │
│         ▼                ▼                ▼                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  Float   │    │ Integer  │    │  Bytes   │             │
│   │ [0.0,1.0)│    │  [a, b]  │    │    n     │             │
│   └──────────┘    └──────────┘    └──────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Security Considerations

- **Not a CSPRNG replacement**: While TrueEntropy uses cryptographic primitives, it's designed for applications needing real-world randomness, not as a replacement for `secrets` module in security contexts.
- **Network dependency**: Some entropy sources require network access. The library gracefully degrades when sources are unavailable.
- **Rate limiting**: External APIs may have rate limits. Use the background collector for sustained generation.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Clone the repository
git clone https://github.com/trueentropy/trueentropy.git
cd trueentropy

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/
black --check src/
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Inspired by:
- Linux `/dev/random` and the entropy pool concept
- [random.org](https://random.org) - Atmospheric noise randomness
- Hardware random number generators (HRNGs)

---

**TrueEntropy** - *Because the universe is the best random number generator.* 🌌
