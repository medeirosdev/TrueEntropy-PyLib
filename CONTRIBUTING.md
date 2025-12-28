# Contributing to TrueEntropy

First off, thank you for considering contributing to TrueEntropy! 🎉

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/medeirosdev/TrueEntropy-PyLib/issues) as you might find that the bug has already been reported.

When creating a bug report, please include:

- **A clear and descriptive title**
- **Steps to reproduce the behavior**
- **Expected behavior**
- **Actual behavior**
- **Python version** (`python --version`)
- **TrueEntropy version** (`pip show trueentropy`)
- **Operating system**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **A clear and descriptive title**
- **A detailed description of the proposed feature**
- **Why this feature would be useful**
- **Possible implementation approach** (optional)

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Make your changes**
4. **Run the tests**:
   ```bash
   pytest
   ```
5. **Run the linters**:
   ```bash
   ruff check src/
   black --check src/
   ```
6. **Commit your changes** using conventional commits:
   ```
   feat: add new feature
   fix: resolve bug
   docs: update documentation
   test: add tests
   refactor: code improvements
   ```
7. **Push to your fork** and submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/TrueEntropy-PyLib.git
cd TrueEntropy-PyLib

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
ruff check src/
black src/
```

## Project Structure

```
TrueEntropy/
├── src/trueentropy/
│   ├── __init__.py      # Public API
│   ├── pool.py          # Entropy pool
│   ├── tap.py           # Value extraction
│   ├── collector.py     # Background collection
│   ├── health.py        # Health monitoring
│   └── harvesters/      # Entropy sources
│       ├── timing.py
│       ├── network.py
│       ├── system.py
│       ├── external.py
│       ├── weather.py
│       └── radioactive.py
├── tests/               # Test suite
├── README.md
├── ARCHITECTURE.md      # Technical documentation
├── CHANGELOG.md         # Version history
└── pyproject.toml       # Project configuration
```

## Testing Guidelines

- Write tests for all new features
- Maintain test coverage for existing functionality
- Use descriptive test names that explain the behavior being tested
- Group related tests in classes

```python
class TestFeatureName:
    def test_feature_does_something(self) -> None:
        """Feature should do something specific."""
        result = feature()
        assert result == expected
```

## Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://github.com/psf/black) for formatting
- Use [Ruff](https://github.com/astral-sh/ruff) for linting
- Add type hints to all functions
- Write docstrings for public APIs

## Adding a New Harvester

1. Create a new file in `src/trueentropy/harvesters/`
2. Inherit from `BaseHarvester`
3. Implement `name` property and `collect()` method
4. Add tests in `tests/test_harvesters.py`
5. Register in `lazy.py` for lazy loading

```python
from trueentropy.harvesters.base import BaseHarvester, HarvestResult

class MyHarvester(BaseHarvester):
    @property
    def name(self) -> str:
        return "my_harvester"
    
    def collect(self) -> HarvestResult:
        # Collect entropy from your source
        data = self._collect_data()
        return HarvestResult(
            data=data,
            entropy_bits=len(data) * 2,  # Conservative estimate
            source=self.name,
            success=True
        )
```

## Questions?

Feel free to open an issue with the "question" label or reach out to the maintainers.

Thank you for contributing! 🙏
