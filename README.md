# TrueEntropy 🎲

![Entropy Visualization Demo](assets/video.gif)

[![PyPI version](https://img.shields.io/pypi/v/trueentropy.svg)](https://pypi.org/project/trueentropy/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**True randomness from real-world entropy sources.**

TrueEntropy harvests chaos from the physical world to generate truly random numbers. Unlike pseudo-random number generators (PRNGs) that use deterministic algorithms, TrueEntropy collects entropy from:

- **CPU Timing Jitter** - Nanosecond variations in code execution
- **Network Latency** - The "weather" of internet infrastructure  
- **System State** - RAM, processes, and hardware fluctuations
- **External APIs** - Seismic activity (USGS), cryptocurrency prices
- **Weather Data** - Temperature, humidity, pressure from OpenWeatherMap/wttr.in
- **Quantum Randomness** - Atmospheric noise (random.org) and quantum vacuum fluctuations (ANU QRNG)

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

## Offline Mode

TrueEntropy can operate without network access using local entropy sources only.

### Sources by Network Requirement

| Source | Requires Network | Description |
|--------|------------------|-------------|
| **Timing Jitter** | ❌ No | CPU timing variations |
| **System State** | ❌ No | RAM, processes, CPU metrics |
| **Network Latency** | ✅ Yes | Ping response times |
| **External APIs** | ✅ Yes | Earthquakes, crypto prices |
| **Weather Data** | ✅ Yes | OpenWeatherMap / wttr.in |
| **Quantum Random** | ✅ Yes | random.org / ANU QRNG |

### Enabling Offline Mode

```python
import trueentropy

# Enable offline mode (disables all network-dependent sources)
trueentropy.configure(offline_mode=True)

# Generate random numbers using local sources only
value = trueentropy.random()
number = trueentropy.randint(1, 100)

# Check which sources are active
health = trueentropy.health()
print(f"Offline mode: {health['offline_mode']}")
for source, info in health['sources'].items():
    status = "✓" if info['enabled'] else "○"
    print(f"  {status} {source}")
```

### Selective Source Configuration

```python
import trueentropy

# Disable only specific sources
trueentropy.configure(
    enable_weather=False,      # Disable weather API
    enable_radioactive=False,  # Disable quantum sources
)

# Or enable only fast local sources
trueentropy.configure(
    offline_mode=True,         # Disable all network sources
    enable_timing=True,        # Keep timing jitter
    enable_system=True,        # Keep system state
)

# Reset to defaults (all sources enabled)
trueentropy.reset_config()
```

### Health Monitoring in Offline Mode

```python
from trueentropy import get_pool
from trueentropy.health import print_health_report

# Configure offline mode
trueentropy.configure(offline_mode=True)

# View detailed health report with source status
print_health_report(get_pool())
```

> **Note**: Offline mode provides reduced entropy diversity. For security-critical applications, consider using all available sources when network access is available.


## Direct vs Hybrid Mode

TrueEntropy offers two modes of operation to balance security and performance:

| Mode | Entropy Source | Performance | Use Case |
|------|---------------|-------------|----------|
| **DIRECT** (Default) | Directly from entropy pool | Slower, blocking | Cryptographic keys, wallets, severe security |
| **HYBRID** | PRNG seeded by pool | Extremely fast | Simulations, games, UI, general purpose |

### Using Hybrid Mode

Hybrid mode uses the TrueEntropy pool to periodically re-seed a fast pseudo-random number generator (PRNG). This provides the best of both worlds: the speed of standard Python random numbers with the entropy quality of our harvesters.

```python
import trueentropy

# Configure Hybrid Mode (re-seed every 60 seconds)
trueentropy.configure(mode="HYBRID", hybrid_reseed_interval=60.0)

# Generate numbers at max speed
# The internal PRNG is automatically re-seeded from the entropy pool
for _ in range(1000000):
   val = trueentropy.random()
```

### Tuning Hybrid Mode

The `hybrid_reseed_interval` should be chosen based on your `offline_mode` setting:

*   **Online (Default)**: Network harvesters take time to collect entropy (latency). Set the interval to **10.0s or higher** to allow the pool to refill between reseeds.
*   **Offline (`offline_mode=True`)**: Local sources are near-instant. You can use lower intervals (e.g., **1.0s - 2.0s**) for frequent reseeding.

> **Tip**: If `health()` reports degraded status with low entropy bits, increase your reseed interval.




## Advanced Features

### Async Support

```python
import asyncio
from trueentropy import aio

async def main():
    value = await aio.random()
    uuid = await aio.random_uuid()
    password = await aio.random_password(16)

asyncio.run(main())
```

### Pool Persistence

Save and restore entropy pool state between runs:

```python
from trueentropy import get_pool
from trueentropy.persistence import save_pool, load_pool

# Save current pool state
save_pool(get_pool(), "entropy_state.bin")

# Later: restore the pool
pool = load_pool("entropy_state.bin")
```

### Multiple Pools

Isolated entropy pools for different purposes:

```python
from trueentropy.pools import PoolManager

manager = PoolManager()
manager.create("crypto")   # For security-critical operations
manager.create("gaming")   # For game mechanics

secure_bytes = manager.randbytes("crypto", 32)
dice_roll = manager.randint("gaming", 1, 6)
```

### Cython Acceleration

Optional C-level performance (10-50x faster for some operations):

```bash
pip install -e ".[cython]"
python setup.py build_ext --inplace
```

```python
from trueentropy.accel import is_accelerated
print(is_accelerated())  # True if compiled
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

### External APIs
Fetches real-world data:
- **USGS Earthquake API** - Latest seismic magnitude readings
- **Cryptocurrency prices** - Bitcoin/Ethereum prices with high precision

### Weather Data
Collects meteorological data from multiple cities:
- Temperature, feels-like, min/max
- Humidity and atmospheric pressure
- Wind speed and direction
- Cloud coverage and visibility
- Supports OpenWeatherMap (with API key) or wttr.in (no key required)

### Quantum Randomness
True random numbers from quantum phenomena:
- **random.org** - Atmospheric noise from radio receivers
- **ANU QRNG** - Quantum vacuum fluctuations (fallback)

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
| `sample(seq, k)` | Returns k unique elements from sequence |

### Distributions

| Function | Description |
|----------|-------------|
| `uniform(a, b)` | Float uniformly distributed in [a, b] |
| `gauss(mu, sigma)` | Gaussian/normal distribution |
| `triangular(low, high, mode)` | Triangular distribution |
| `exponential(lambd)` | Exponential distribution |
| `weighted_choice(seq, weights)` | Weighted random selection |

### Generators

| Function | Description |
|----------|-------------|
| `random_uuid()` | UUID v4 (e.g., `f47ac10b-58cc-4372-...`) |
| `random_token(length, encoding)` | Hex or base64 token |
| `random_password(length, ...)` | Secure password with configurable charset |

### Management Functions

| Function | Description |
|----------|-------------|
| `configure(...)` | Set mode (DIRECT/HYBRID), offline_mode, enable sources |
| `reset_config()` | Reset configuration to defaults |
| `health()` | Returns entropy pool health status |
| `start_collector(interval)` | Starts background entropy collection |
| `stop_collector()` | Stops background collection |
| `feed(data)` | Manually feed entropy into the pool |
| `get_tap()` | Get current tap instance (EntropyTap or HybridTap) |
| `get_pool()` | Get the global entropy pool instance |

## How It Works

```
+-------------------------------------------------------------+
|                    ENTROPY HARVESTERS                        |
|  +----------+ +----------+ +----------+ +--------------+    |
|  |  Timing  | | Network  | |  System  | |   External   |    |
|  |  Jitter  | | Latency  | |  State   | |     APIs     |    |
|  +----+-----+ +----+-----+ +----+-----+ +------+-------+    |
|       |            |            |              |            |
|       +------------+-----+------+--------------+            |
|                          v                                  |
|                   +-----------+                             |
|                   |   MIXER   |  SHA-256 Hashing            |
|                   | (Whitening)|  Avalanche Effect          |
|                   +-----+-----+                             |
|                         v                                   |
|              +-----------------------+                      |
|              |     ENTROPY POOL      |  4096 bits           |
|              |   (Accumulated State) |  Thread-safe         |
|              +-----------+-----------+                      |
|                          v                                  |
|                   +-----------+                             |
|                   | EXTRACTOR |  Secure extraction          |
|                   |   (Tap)   |  DIRECT or HYBRID mode      |
|                   +-----+-----+                             |
|                         v                                   |
|         +---------------+--------------+                    |
|         v               v              v                    |
|   +----------+    +----------+    +----------+              |
|   |  Float   |    | Integer  |    |  Bytes   |              |
|   | [0.0,1.0)|    |  [a, b]  |    |    n     |              |
|   +----------+    +----------+    +----------+              |
+-------------------------------------------------------------+
```

## Security Considerations

- **Not a CSPRNG replacement**: While TrueEntropy uses cryptographic primitives, it's designed for applications needing real-world randomness, not as a replacement for `secrets` module in security contexts.
- **Network dependency**: Some entropy sources require network access. The library gracefully degrades when sources are unavailable.
- **Rate limiting**: External APIs may have rate limits. Use the background collector for sustained generation.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Clone the repository
git clone https://github.com/medeirosdev/TrueEntropy-PyLib.git
cd TrueEntropy-PyLib

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

## Author

**Guilherme de Medeiros** - UNICAMP  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/guilhermedemedeiros/)

## Acknowledgments

Inspired by:
- Linux `/dev/random` and the entropy pool concept
- [random.org](https://random.org) - Atmospheric noise randomness
- Hardware random number generators (HRNGs)

---

**TrueEntropy** - *Because the universe is the best random number generator.*
