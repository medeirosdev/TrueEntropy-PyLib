# Changelog

All notable changes to TrueEntropy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-28

### Added

#### Hybrid Mode
- `configure(mode="HYBRID")` - Switch to high-performance PRNG mode
- `HybridTap` class - PRNG seeded by true entropy from the pool
- `hybrid_reseed_interval` config - Control reseed frequency (default: 60s)
- 83x faster than DIRECT mode (~5M ops/sec vs ~60K ops/sec)

#### Architecture Improvements
- `BaseTap` abstract class - Common interface for tap implementations
- `get_tap()` function - Get current tap instance (EntropyTap or HybridTap)
- Mode switching via `configure(mode="DIRECT"|"HYBRID")`

#### Documentation
- ARCHITECTURE.md updated with Operation Modes section and diagrams
- README.md updated with Hybrid Mode usage and tuning guidelines
- Comprehensive demo script in `examples/demo_comprehensive.py`

### Changed
- `EntropyTap` now inherits from `BaseTap`
- Global `_tap` can now be either `EntropyTap` or `HybridTap`
- `configure()` now supports `mode` and `hybrid_reseed_interval` parameters

## [0.1.1] - 2025-12-27

### Added

#### Offline Mode
- `configure(offline_mode=True)` - Disable all network-dependent harvesters
- `get_config()` - Get current configuration
- `reset_config()` - Reset to defaults
- `TrueEntropyConfig` - Configuration dataclass with per-harvester flags

#### Enhanced Health Monitoring
- `health()` now returns `sources` dict with status of each harvester
- `health()` now returns `offline_mode` boolean
- `print_health_report()` displays source status table

#### Comprehensive Testing
- `test_harvesters_live.py` - Live tests for all harvesters with latency metrics
- Performance benchmarks with detailed reporting
- `BENCHMARKS.md` - Historical benchmark data

### Changed
- `start_background_collector()` now respects global config
- `collect_once()` now respects global config
- Added weather and radioactive harvesters to collector

## [0.1.0] - 2025-12-27

### Added

#### Core Features
- `EntropyPool` - Thread-safe entropy accumulator with SHA-256 mixing
- `EntropyTap` - Extractor for converting entropy to random values
- `entropy_health()` - Pool health monitoring with score and recommendations

#### Random Generation
- `random()` - Float in [0.0, 1.0)
- `randint(a, b)` - Integer in [a, b] with rejection sampling
- `randbool()` - Random boolean
- `choice(seq)` - Random element from sequence
- `randbytes(n)` - Random bytes
- `shuffle(seq)` - Fisher-Yates shuffle
- `sample(seq, k)` - Random sampling without replacement

#### Distributions
- `uniform(a, b)` - Uniform distribution
- `gauss(mu, sigma)` - Normal distribution (Box-Muller)
- `triangular(low, high, mode)` - Triangular distribution
- `exponential(lambd)` - Exponential distribution
- `weighted_choice(seq, weights)` - Weighted random selection

#### Generators
- `random_uuid()` - UUID v4 generation
- `random_token(length, encoding)` - Hex/base64 tokens
- `random_password(length, ...)` - Secure password generation

#### Entropy Harvesters
- `TimingHarvester` - CPU timing jitter
- `NetworkHarvester` - Network latency measurements
- `SystemHarvester` - System state (RAM, CPU, processes)
- `ExternalHarvester` - USGS earthquakes, crypto prices
- `WeatherHarvester` - OpenWeatherMap/wttr.in weather data
- `RadioactiveHarvester` - random.org and ANU QRNG

#### Advanced Features
- `trueentropy.aio` - Async/await support
- `trueentropy.persistence` - Save/load pool state
- `trueentropy.pools` - Multiple isolated pools
- `trueentropy.lazy` - Lazy harvester loading
- `trueentropy.accel` - Optional Cython acceleration

#### Infrastructure
- GitHub Actions CI (tests on Python 3.9-3.12, Linux/Windows/macOS)
- Comprehensive test suite (100+ tests)
- Type hints (PEP 561 compliant)
- Documentation (README, REFERENCES)

### Dependencies
- `requests>=2.25.0`
- `psutil>=5.8.0`

[0.1.0]: https://github.com/medeirosdev/TrueEntropy-PyLib/releases/tag/v0.1.0
