# TrueEntropy Benchmark History

Performance benchmarks for all entropy harvesters, updated periodically.

## Latest Benchmark

**Date**: 2024-12-27 20:54 (BRT)  
**Platform**: Windows 11, Python 3.11.5  
**Network**: Home broadband

### Results

| Harvester | Type | Time (ms) | Entropy (bits) | Data (bytes) | Status |
|-----------|------|-----------|----------------|--------------|--------|
| timing | Offline | 2 | 182 | 512 | ✓ OK |
| system | Offline | 312 | 132 | 296 | ✓ OK |
| network | Online | 1,916 | 104 | 128 | ✓ OK |
| external | Online | 1,335 | 236 | 320 | ✓ OK |
| weather | Online | 18,044 | 132 | 296 | ✓ OK |
| radioactive | Online | 1,651 | 0 | 0 | ✗ Rate Limited |

**Total**: 5/6 harvesters successful, ~23s total, 786 bits entropy

### Summary Statistics

- **Offline Sources**: ~314ms average, always available
- **Online Sources**: ~5.7s average (excluding weather outlier)
- **Weather API**: Slow (~18s) but reliable
- **Radioactive**: Often rate-limited without API key

---

## Benchmark History

### 2024-12-27 - Initial Benchmark

First comprehensive benchmark after implementing offline mode feature.

| Metric | Value |
|--------|-------|
| Offline harvesters success rate | 100% |
| Online harvesters success rate | 75% (3/4) |
| Total entropy collected | 786 bits |
| Total collection time | 23.26s |

**Notes**:
- radioactive harvester rate-limited (no API key configured)
- weather harvester unusually slow (18s) - wttr.in latency
- All offline sources performing within expected parameters

---

## How to Run Benchmarks

```bash
# Full benchmark with report
pytest tests/test_harvesters_live.py::TestAllHarvesters::test_all_harvesters_benchmark -v -s

# Offline only (fast)
pytest tests/test_harvesters_live.py::TestOfflineHarvesters -v -s

# Online only
pytest tests/test_harvesters_live.py::TestOnlineHarvesters -v -s
```

## Benchmark Template

Copy this template when adding new benchmark entries:

```markdown
### YYYY-MM-DD - Description

| Harvester | Type | Time (ms) | Entropy (bits) | Status |
|-----------|------|-----------|----------------|--------|
| timing | Offline | X | X | ✓/✗ |
| system | Offline | X | X | ✓/✗ |
| network | Online | X | X | ✓/✗ |
| external | Online | X | X | ✓/✗ |
| weather | Online | X | X | ✓/✗ |
| radioactive | Online | X | X | ✓/✗ |

**Notes**: ...
```
