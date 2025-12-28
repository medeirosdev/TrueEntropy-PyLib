# TrueEntropy Architecture

## Overview

TrueEntropy harvests entropy from real-world sources and converts it into cryptographically secure random values. This document explains how each entropy source is collected and transformed into usable random numbers.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PUBLIC API                                     │
│  trueentropy.random() / randint() / choice() / shuffle() / ...          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          ENTROPY TAP (tap.py)                            │
│  Converts raw bytes into usable values (floats, ints, booleans)          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ENTROPY POOL (pool.py)                            │
│  512-byte buffer with SHA-256 whitening and thread-safe access           │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                         HARVESTERS (harvesters/)                         │
│   timing | network | system | external | weather | radioactive           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Operation Modes

TrueEntropy supports two operation modes, selectable via `configure(mode=...)`:

### Mode Comparison

| Aspect | DIRECT Mode | HYBRID Mode |
|--------|-------------|-------------|
| **Speed** | ~60K ops/sec | ~5M ops/sec |
| **Source** | Direct pool extraction | PRNG seeded by pool |
| **Security** | Maximum (true random) | High (periodic reseed) |
| **Use Case** | Crypto keys, wallets | Simulations, games |

### DIRECT Mode (Default)

Every call extracts fresh entropy directly from the pool:

```
trueentropy.random() ──► EntropyTap.random() ──► pool.extract(8) ──► float
```

```
┌────────────────────────────────────────────────────────────────────┐
│                        DIRECT MODE                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   random() ───► EntropyTap ───► Pool ───► 8 bytes ───► float       │
│                                   │                                 │
│                                   ▲                                 │
│                              Harvesters                             │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### HYBRID Mode

Uses a fast PRNG (Mersenne Twister) that re-seeds from the pool periodically:

```
trueentropy.random() ──► HybridTap.random() ──► PRNG.random() ──► float
                                   │
                                   └──► (every N seconds) ──► pool.extract(32) ──► PRNG.seed()
```

```
┌────────────────────────────────────────────────────────────────────┐
│                        HYBRID MODE                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   random() ───► HybridTap ───► PRNG (Mersenne Twister) ───► float   │
│                     │                                               │
│                     ▼ (periodic reseed)                             │
│                   Pool ◄────── Harvesters                           │
│                     │                                               │
│                     └──► 32 bytes ──► PRNG.seed()                   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Configuration

```python
import trueentropy

# DIRECT mode (default) - maximum security
trueentropy.configure(mode="DIRECT")

# HYBRID mode - maximum performance
trueentropy.configure(mode="HYBRID", hybrid_reseed_interval=60.0)

# Combined: Hybrid + Offline (fast, no network)
trueentropy.configure(mode="HYBRID", offline_mode=True)
```

## Entropy Sources

### 1. Timing Jitter (timing.py)

**Source**: CPU instruction timing variations

**How it works**:
```python
measurements = []
for _ in range(iterations):
    start = time.perf_counter_ns()
    # Perform CPU operations
    for _ in range(1000):
        _ = 1 + 1
    end = time.perf_counter_ns()
    measurements.append(end - start)

# Pack as bytes
data = struct.pack(f"!{len(measurements)}Q", *measurements)
```

**Why it's random**:
- CPU scheduling is non-deterministic
- Cache hits/misses vary unpredictably
- Other processes create interference
- Nanosecond precision captures jitter

**Entropy estimate**: ~32 bits per collection

---

### 2. Network Latency (network.py)

**Source**: Round-trip time to remote servers

**How it works**:
```python
targets = ["https://1.1.1.1", "https://8.8.8.8", "https://google.com"]

for target in targets:
    start = time.perf_counter_ns()
    requests.head(target, timeout=2)
    end = time.perf_counter_ns()
    
    latency_ns = end - start  # e.g., 64,197,532 ns
    measurements.append(latency_ns)

data = struct.pack("!QQQ", *measurements)
```

**Why it's random**:
- Network congestion varies constantly
- Routing paths change dynamically
- Server load fluctuates
- Physical infrastructure conditions

**Entropy estimate**: ~8 bits per server

---

### 3. System State (system.py)

**Source**: Volatile system metrics via psutil

**Metrics collected**:
- Available RAM (bytes)
- CPU usage per core (%)
- Process count and PIDs
- Disk I/O counters
- Network I/O counters
- Timestamps (nanoseconds)

**How it works**:
```python
metrics = []
metrics.append(("ram", psutil.virtual_memory().available))
metrics.append(("cpu", psutil.cpu_percent()))
metrics.append(("pids", len(psutil.pids())))
# ... more metrics

for name, value in metrics:
    int_value = int(value * 1000000)  # Preserve precision
    data += struct.pack("!Q", int_value)
```

**Why it's random**:
- RAM allocation changes with every program
- CPU usage fluctuates rapidly
- Processes start/stop constantly

**Entropy estimate**: ~6 bits per metric

---

### 4. External APIs (external.py)

**Sources**:
- USGS Earthquake data (seismic activity)
- Cryptocurrency prices (market volatility)

**How it works**:
```python
# Earthquake data
response = requests.get("https://earthquake.usgs.gov/...")
earthquakes = response.json()["features"]

for eq in earthquakes:
    magnitude = eq["properties"]["mag"]  # 4.7
    lat = eq["geometry"]["coordinates"][0]
    lon = eq["geometry"]["coordinates"][1]
    
    data += struct.pack("!d", magnitude)
    data += struct.pack("!dd", lat, lon)
```

**Why it's random**:
- Earthquakes are physically unpredictable
- Financial markets are chaotic systems

**Entropy estimate**: ~32 bits per collection

---

### 5. Weather Data (weather.py)

**Sources**: OpenWeatherMap API or wttr.in

**Metrics**: Temperature, humidity, pressure, wind speed

**How it works**:
```python
cities = ["London", "Tokyo", "New York", "Sydney"]

for city in cities:
    weather = fetch_weather(city)
    
    # Multiply to preserve decimal precision
    temp = int(weather["temp"] * 10000)       # 23.47°C → 234700
    humidity = int(weather["humidity"] * 100)  # 67.3% → 6730
    pressure = int(weather["pressure"] * 100)  # 1013.25 → 101325
    
    data += struct.pack("!QQQ", temp, humidity, pressure)
```

**Why it's random**:
- Weather changes constantly
- Decimal places vary unpredictably
- Multiple cities provide independent sources

**Entropy estimate**: ~8 bits per metric

---

### 6. Quantum Random (radioactive.py)

**Sources**:
- ANU QRNG (quantum vacuum fluctuations)
- random.org (atmospheric noise)

**How it works**:
```python
# ANU Quantum RNG - true quantum randomness
response = requests.get(
    "https://qrng.anu.edu.au/API/jsonI.php",
    params={"length": 16, "type": "uint8"}
)
quantum_bytes = bytes(response.json()["data"])
```

**Why it's random**:
- Quantum vacuum fluctuations are fundamentally unpredictable
- Heisenberg uncertainty principle guarantees randomness
- Not pseudo-random - true physical randomness

**Entropy estimate**: 8 bits per byte (full entropy)

---

## Entropy Pool (pool.py)

### Whitening Process

All harvested data passes through SHA-256 mixing:

```python
def feed(self, data: bytes):
    # Combine: current pool + new data + timestamp
    mix_input = self._pool + data + struct.pack("!d", time.time())
    
    # SHA-256 hash for avalanche effect
    hash_digest = hashlib.sha256(mix_input).digest()
    
    # Expand to fill pool
    self._pool = self._expand_to_pool_size(hash_digest)
```

**Properties**:
- Avalanche effect: 1 bit change → ~50% output bits change
- Forward secrecy: Cannot recover old states
- Thread-safe: Lock protects all operations

---

## Value Conversion (tap.py)

### random() → Float [0.0, 1.0)

```python
raw_bytes = pool.extract(8)              # 8 bytes
value = struct.unpack("!Q", raw_bytes)[0] # 64-bit int
return value / 2**64                      # Divide by 2^64
```

### randint(a, b) → Integer [a, b] (Rejection Sampling)

```python
range_size = b - a + 1
bits_needed = range_size.bit_length()
mask = (1 << bits_needed) - 1

while True:
    value = extract_int() & mask
    if value < range_size:  # Accept
        return a + value
    # Reject and retry (eliminates modulo bias)
```

### gauss(mu, sigma) → Normal Distribution (Box-Muller)

```python
u1 = random()  # Uniform (0, 1)
u2 = random()  # Uniform [0, 1)

z0 = sqrt(-2 * ln(u1)) * cos(2π * u2)

return mu + sigma * z0
```

### shuffle(seq) → Fisher-Yates Algorithm

```python
for i in range(n - 1, 0, -1):
    j = randint(0, i)
    seq[i], seq[j] = seq[j], seq[i]
```

Guarantees all N! permutations are equally probable.

---

## Security Properties

| Property | Implementation |
|----------|----------------|
| Forward Secrecy | Pool state updated after each extraction |
| Avalanche Effect | SHA-256 mixing ensures 1 bit → 50% change |
| Thread Safety | All pool operations protected by locks |
| No Modulo Bias | Rejection sampling in randint() |
| Entropy Mixing | Multiple independent sources combined |

---

## Module Summary

| Module | Purpose |
|--------|---------|
| `pool.py` | Accumulates and mixes entropy with SHA-256 |
| `tap.py` | `BaseTap` abstract class + `EntropyTap` (DIRECT mode) |
| `hybrid.py` | `HybridTap` for HYBRID mode (PRNG seeded by pool) |
| `config.py` | `TrueEntropyConfig` dataclass + `configure()` function |
| `collector.py` | Background thread for automatic collection |
| `health.py` | Monitors pool health (score 0-100) |
| `harvesters/` | Collectors for different entropy sources |
| `aio.py` | Async versions of all functions |
| `persistence.py` | Save/restore pool state to disk |
| `pools.py` | Multiple isolated entropy pools |
| `accel.py` | Optional Cython acceleration |
