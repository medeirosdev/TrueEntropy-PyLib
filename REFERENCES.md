# Mathematical References

This document contains the mathematical foundations and references for the algorithms used in TrueEntropy.

## Table of Contents

1. [Entropy and Information Theory](#entropy-and-information-theory)
2. [Cryptographic Primitives](#cryptographic-primitives)
3. [Random Number Generation](#random-number-generation)
4. [Probability Distributions](#probability-distributions)
5. [Statistical Tests](#statistical-tests)
6. [External Sources](#external-sources)

---

## Entropy and Information Theory

### Shannon Entropy

The entropy of a discrete random variable X is defined as:

```
H(X) = -Σ p(x) log₂ p(x)
```

**References:**
- Shannon, C. E. (1948). "A Mathematical Theory of Communication"
- https://en.wikipedia.org/wiki/Entropy_(information_theory)

### Entropy Estimation

<!-- Add your entropy estimation formulas here -->

---

## Cryptographic Primitives

### SHA-256 Hash Function

Used for mixing entropy in the pool. Properties:
- Output: 256 bits (32 bytes)
- Collision resistance: 2^128 operations
- Preimage resistance: 2^256 operations

**References:**
- FIPS 180-4: Secure Hash Standard
- https://csrc.nist.gov/publications/detail/fips/180/4/final

### Avalanche Effect

A small change in input produces a completely different output:

```
P(bit_i changes | 1 bit input change) ≈ 0.5
```

---

## Random Number Generation

### Uniform Float Generation

Converting n random bits to float in [0, 1):

```
float_value = integer_value / 2^n
```

We use 64 bits for maximum precision (~15-17 significant decimal digits).

### Rejection Sampling (Unbiased Integer Range)

To generate uniform integer in [a, b]:

```
range = b - a + 1
bits_needed = ceil(log₂(range))
mask = 2^bits_needed - 1

repeat:
    raw = extract_bits(bits_needed)
    value = raw & mask
until value < range

return a + value
```

**Why rejection sampling?**
Simple modulo causes bias when range doesn't divide 2^n evenly.

**References:**
- https://en.wikipedia.org/wiki/Rejection_sampling

### Fisher-Yates Shuffle

For uniform random permutation:

```
for i from n-1 down to 1:
    j = random_int(0, i)
    swap(arr[i], arr[j])
```

**References:**
- Fisher, R.A.; Yates, F. (1938). "Statistical Tables"
- https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle

---

## Probability Distributions

### Gaussian (Normal) Distribution

Using Box-Muller transform:

```
Z₀ = √(-2 ln U₁) cos(2π U₂)
Z₁ = √(-2 ln U₁) sin(2π U₂)
```

Where U₁, U₂ ~ Uniform(0, 1)

**References:**
- Box, G. E. P.; Muller, M. E. (1958)
- https://www.statisticshowto.com/box-muller-transform-simple-definition/
- https://en.wikipedia.org/wiki/Box%E2%80%93Muller_transform

### Exponential Distribution

Using inverse transform:

```
X = -ln(U) / λ
```

Where U ~ Uniform(0, 1), λ is rate parameter

**References:**
- https://en.wikipedia.org/wiki/Exponential_distribution

### Triangular Distribution

```
if U < (mode - low) / (high - low):
    X = low + √(U × (high - low) × (mode - low))
else:
    X = high - √((1-U) × (high - low) × (high - mode))
```

**References:**
- https://en.wikipedia.org/wiki/Triangular_distribution

### Weighted Random Selection

Cumulative distribution method:

```
total = sum(weights)
threshold = random() * total
cumulative = 0
for i, weight in enumerate(weights):
    cumulative += weight
    if threshold < cumulative:
        return items[i]
```

---

## Statistical Tests

### Chi-Square Test

For testing uniformity:

```
χ² = Σ (O_i - E_i)² / E_i
```

Where O_i = observed frequency, E_i = expected frequency

### NIST SP 800-22

Statistical test suite for random number generators:
- Frequency (monobit) test
- Block frequency test
- Runs test
- Longest run test
- etc.

**References:**
- https://csrc.nist.gov/publications/detail/sp/800-22/rev-1a/final

---

## External Sources

### Entropy Sources Quality

| Source | Entropy Quality | Notes |
|--------|----------------|-------|
| CPU Timing Jitter | Medium | OS scheduler, cache effects |
| Network Latency | Medium | Congestion, routing variability |
| System State | Low-Medium | Volatile but somewhat predictable |
| Weather APIs | Medium | Chaotic atmospheric systems |
| random.org | High | Atmospheric noise, quantum effects |
| ANU QRNG | Very High | Quantum vacuum fluctuations |

### UUID v4 Generation (RFC 4122)

```
xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx

Where:
- x = random hex digit
- 4 = version (always 4 for random UUID)
- y = variant (8, 9, a, or b)
```

**References:**
- RFC 4122: https://tools.ietf.org/html/rfc4122

---

## Contributing References

Add your mathematical references here following the format:

```markdown
### Topic Name

Formula or algorithm description:

\`\`\`
mathematical_notation_here
\`\`\`

**References:**
- Author (Year). "Title"
- URL
```

---

## Author

**Guilherme de Medeiros** - UNICAMP  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/guilhermedemedeiros/)
