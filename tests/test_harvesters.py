# =============================================================================
# TrueEntropy - Harvesters Tests
# =============================================================================
#
# Unit tests for all harvester classes.
# Tests cover:
# - Timing harvester
# - Network harvester
# - System harvester
# - External harvester
# - Weather harvester
# - Radioactive harvester
# - Base harvester interface
#
# =============================================================================


from __future__ import annotations

import pytest

from trueentropy.harvesters.base import HarvestResult
from trueentropy.harvesters.external import ExternalHarvester
from trueentropy.harvesters.network import NetworkHarvester
from trueentropy.harvesters.radioactive import RadioactiveHarvester
from trueentropy.harvesters.system import SystemHarvester
from trueentropy.harvesters.timing import TimingHarvester
from trueentropy.harvesters.weather import WeatherHarvester


class TestHarvestResult:
    """Test HarvestResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful result."""
        result = HarvestResult(data=b"test_data", entropy_bits=16, source="test", success=True)

        assert result.data == b"test_data"
        assert result.entropy_bits == 16
        assert result.source == "test"
        assert result.success is True
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test creating a failed result."""
        result = HarvestResult(
            data=b"", entropy_bits=0, source="test", success=False, error="Something went wrong"
        )

        assert result.data == b""
        assert result.entropy_bits == 0
        assert result.success is False
        assert result.error == "Something went wrong"


class TestTimingHarvester:
    """Test TimingHarvester."""

    def test_name(self) -> None:
        """Harvester should have correct name."""
        harvester = TimingHarvester()
        assert harvester.name == "timing"

    def test_collect_returns_result(self) -> None:
        """collect() should return HarvestResult."""
        harvester = TimingHarvester()
        result = harvester.collect()

        assert isinstance(result, HarvestResult)

    def test_collect_succeeds(self) -> None:
        """collect() should succeed (timing is always available)."""
        harvester = TimingHarvester()
        result = harvester.collect()

        assert result.success is True
        assert result.data != b""
        assert result.entropy_bits > 0

    def test_collect_returns_bytes(self) -> None:
        """collect() should return bytes data."""
        harvester = TimingHarvester()
        result = harvester.collect()

        assert isinstance(result.data, bytes)
        assert len(result.data) > 0

    def test_num_samples_configuration(self) -> None:
        """Harvester should respect num_samples config."""
        harvester = TimingHarvester(num_samples=32)
        assert harvester.num_samples == 32

        result = harvester.collect()
        # 32 samples * 8 bytes per sample
        assert len(result.data) == 32 * 8

    def test_different_collections_different_data(self) -> None:
        """Successive collections should return different data."""
        harvester = TimingHarvester()

        results = [harvester.collect().data for _ in range(10)]

        # All should be unique
        assert len(set(results)) == 10

    def test_safe_collect(self) -> None:
        """safe_collect() should never raise."""
        harvester = TimingHarvester()

        # Should not raise
        result = harvester.safe_collect()

        assert isinstance(result, HarvestResult)


class TestSystemHarvester:
    """Test SystemHarvester."""

    def test_name(self) -> None:
        """Harvester should have correct name."""
        harvester = SystemHarvester()
        assert harvester.name == "system"

    def test_collect_returns_result(self) -> None:
        """collect() should return HarvestResult."""
        harvester = SystemHarvester()
        result = harvester.collect()

        assert isinstance(result, HarvestResult)

    def test_collect_returns_data(self) -> None:
        """collect() should return non-empty data."""
        harvester = SystemHarvester()
        result = harvester.collect()

        # Should succeed if psutil is available
        if result.success:
            assert result.data != b""
            assert result.entropy_bits > 0

    def test_list_available_metrics(self) -> None:
        """list_available_metrics() should return list."""
        harvester = SystemHarvester()
        metrics = harvester.list_available_metrics()

        assert isinstance(metrics, list)
        # At minimum, timestamp should be available
        assert "timestamp_ns" in metrics


class TestNetworkHarvester:
    """Test NetworkHarvester."""

    def test_name(self) -> None:
        """Harvester should have correct name."""
        harvester = NetworkHarvester()
        assert harvester.name == "network"

    def test_default_targets(self) -> None:
        """Harvester should have default targets."""
        harvester = NetworkHarvester()

        assert len(harvester.targets) > 0
        assert all(t.startswith("http") for t in harvester.targets)

    def test_custom_targets(self) -> None:
        """Harvester should accept custom targets."""
        targets = ["https://example.com", "https://test.com"]
        harvester = NetworkHarvester(targets=targets)

        assert harvester.targets == targets

    def test_timeout_configuration(self) -> None:
        """Harvester should respect timeout config."""
        harvester = NetworkHarvester(timeout=1.0)
        assert harvester.timeout == 1.0

    def test_collect_returns_result(self) -> None:
        """collect() should return HarvestResult."""
        harvester = NetworkHarvester()
        result = harvester.collect()

        assert isinstance(result, HarvestResult)

    # Note: We don't test actual network calls here to avoid
    # network-dependent test failures. Integration tests would
    # cover that.


class TestExternalHarvester:
    """Test ExternalHarvester."""

    def test_name(self) -> None:
        """Harvester should have correct name."""
        harvester = ExternalHarvester()
        assert harvester.name == "external"

    def test_enable_flags(self) -> None:
        """Harvester should respect enable flags."""
        harvester = ExternalHarvester(enable_earthquake=False, enable_crypto=True)

        assert harvester.enable_earthquake is False
        assert harvester.enable_crypto is True

    def test_timeout_configuration(self) -> None:
        """Harvester should respect timeout config."""
        harvester = ExternalHarvester(timeout=3.0)
        assert harvester.timeout == 3.0

    def test_collect_returns_result(self) -> None:
        """collect() should return HarvestResult."""
        harvester = ExternalHarvester()
        result = harvester.collect()

        assert isinstance(result, HarvestResult)

    # Note: We don't test actual API calls here to avoid
    # network-dependent test failures and rate limiting.


class TestBaseHarvesterInterface:
    """Test that harvesters implement the interface correctly."""

    def test_all_harvesters_have_name(self) -> None:
        """All harvesters should implement name property."""
        harvesters = [
            TimingHarvester(),
            SystemHarvester(),
            NetworkHarvester(),
            ExternalHarvester(),
        ]

        for h in harvesters:
            assert isinstance(h.name, str)
            assert len(h.name) > 0

    def test_all_harvesters_have_collect(self) -> None:
        """All harvesters should implement collect method."""
        harvesters = [
            TimingHarvester(),
            SystemHarvester(),
            NetworkHarvester(),
            ExternalHarvester(),
        ]

        for h in harvesters:
            result = h.collect()
            assert isinstance(result, HarvestResult)

    def test_all_harvesters_have_safe_collect(self) -> None:
        """All harvesters should have safe_collect from base class."""
        harvesters = [
            TimingHarvester(),
            SystemHarvester(),
            NetworkHarvester(),
            ExternalHarvester(),
        ]

        for h in harvesters:
            result = h.safe_collect()
            assert isinstance(result, HarvestResult)

    def test_repr(self) -> None:
        """All harvesters should have useful repr."""
        harvesters = [
            TimingHarvester(),
            SystemHarvester(),
            NetworkHarvester(),
            ExternalHarvester(),
            WeatherHarvester(),
            RadioactiveHarvester(),
        ]

        for h in harvesters:
            repr_str = repr(h)
            assert h.name in repr_str


class TestWeatherHarvester:
    """Test WeatherHarvester."""

    def test_name(self) -> None:
        """Harvester should have correct name."""
        harvester = WeatherHarvester()
        assert harvester.name == "weather"

    def test_collect_returns_result(self) -> None:
        """collect() should return HarvestResult."""
        harvester = WeatherHarvester()
        result = harvester.collect()

        assert isinstance(result, HarvestResult)

    def test_timeout_configuration(self) -> None:
        """Harvester should respect timeout config."""
        harvester = WeatherHarvester(timeout=3.0)
        assert harvester.timeout == 3.0

    def test_api_key_masking(self) -> None:
        """API key should be masked when accessed."""
        harvester = WeatherHarvester(api_key="my_secret_api_key_12345")
        masked = harvester.api_key

        # Should be partially masked
        assert masked is not None
        assert "..." in masked
        assert masked != "my_secret_api_key_12345"

    def test_no_api_key_returns_none(self) -> None:
        """api_key property should return None when not set."""
        harvester = WeatherHarvester()
        assert harvester.api_key is None


class TestRadioactiveHarvester:
    """Test RadioactiveHarvester."""

    def test_name(self) -> None:
        """Harvester should have correct name."""
        harvester = RadioactiveHarvester()
        assert harvester.name == "radioactive"

    def test_collect_returns_result(self) -> None:
        """collect() should return HarvestResult."""
        harvester = RadioactiveHarvester()
        result = harvester.collect()

        assert isinstance(result, HarvestResult)

    def test_timeout_configuration(self) -> None:
        """Harvester should respect timeout config."""
        harvester = RadioactiveHarvester(timeout=15.0)
        assert harvester.timeout == 15.0

    def test_num_integers_configuration(self) -> None:
        """Harvester should respect num_integers config."""
        harvester = RadioactiveHarvester(num_integers=20)
        assert harvester.num_integers == 20

    def test_num_integers_validation(self) -> None:
        """num_integers should have valid range."""
        harvester = RadioactiveHarvester()

        with pytest.raises(ValueError):
            harvester.num_integers = 0

        with pytest.raises(ValueError):
            harvester.num_integers = 1001

    def test_api_key_masking(self) -> None:
        """API key should be masked when accessed."""
        harvester = RadioactiveHarvester(api_key="12345678-abcd-efgh-ijkl")
        masked = harvester.api_key

        assert masked is not None
        assert "..." in masked
