# Changelog

All notable changes to TrueEntropy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
