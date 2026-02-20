"""Tests for request metrics and MetricsTransport."""

import threading
from unittest.mock import MagicMock

import pytest

from odoorpc_toolbox.rpc.metrics import MetricsTransport, RequestMetrics
from odoorpc_toolbox.rpc.transport import TransportResponse, UrllibTransport

# ---- RequestMetrics Tests ----


class TestRequestMetrics:
    """Tests for the RequestMetrics dataclass."""

    def test_initial_values(self):
        m = RequestMetrics()
        assert m.total_requests == 0
        assert m.total_errors == 0
        assert m.total_time_ms == 0.0

    def test_record_success(self):
        m = RequestMetrics()
        m.record(time_ms=50.0)
        assert m.total_requests == 1
        assert m.total_errors == 0
        assert m.total_time_ms == 50.0

    def test_record_error(self):
        m = RequestMetrics()
        m.record(time_ms=100.0, error=True)
        assert m.total_requests == 1
        assert m.total_errors == 1

    def test_record_multiple(self):
        m = RequestMetrics()
        m.record(time_ms=50.0)
        m.record(time_ms=100.0, error=True)
        m.record(time_ms=75.0)
        assert m.total_requests == 3
        assert m.total_errors == 1
        assert m.total_time_ms == 225.0

    def test_avg_time_ms(self):
        m = RequestMetrics()
        m.record(time_ms=50.0)
        m.record(time_ms=100.0)
        assert m.avg_time_ms == 75.0

    def test_avg_time_ms_no_requests(self):
        m = RequestMetrics()
        assert m.avg_time_ms == 0.0

    def test_error_rate(self):
        m = RequestMetrics()
        m.record(time_ms=50.0)
        m.record(time_ms=100.0, error=True)
        assert m.error_rate == 0.5

    def test_error_rate_no_requests(self):
        m = RequestMetrics()
        assert m.error_rate == 0.0

    def test_reset(self):
        m = RequestMetrics()
        m.record(time_ms=50.0)
        m.record(time_ms=100.0, error=True)
        m.reset()
        assert m.total_requests == 0
        assert m.total_errors == 0
        assert m.total_time_ms == 0.0

    def test_thread_safety(self):
        m = RequestMetrics()
        errors = []

        def record_many():
            try:
                for _ in range(100):
                    m.record(time_ms=1.0)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert m.total_requests == 1000
        assert m.total_time_ms == 1000.0


# ---- MetricsTransport Tests ----


class TestMetricsTransport:
    """Tests for the MetricsTransport decorator."""

    def _make_mock_transport(self, status_code=200, body=b"{}"):
        mock = MagicMock()
        mock.request.return_value = TransportResponse(status_code=status_code, body=body, headers={})
        return mock

    def test_wraps_transport(self):
        inner = self._make_mock_transport()
        mt = MetricsTransport(inner)
        assert mt.metrics.total_requests == 0

    def test_records_successful_request(self):
        inner = self._make_mock_transport()
        metrics = RequestMetrics()
        mt = MetricsTransport(inner, metrics)

        mt.request("http://localhost/jsonrpc", data=b"{}")

        assert metrics.total_requests == 1
        assert metrics.total_errors == 0
        assert metrics.total_time_ms > 0

    def test_records_server_error(self):
        inner = self._make_mock_transport(status_code=500)
        metrics = RequestMetrics()
        mt = MetricsTransport(inner, metrics)

        mt.request("http://localhost/jsonrpc", data=b"{}")

        assert metrics.total_requests == 1
        assert metrics.total_errors == 1

    def test_records_exception(self):
        inner = MagicMock()
        inner.request.side_effect = ConnectionError("Connection refused")
        metrics = RequestMetrics()
        mt = MetricsTransport(inner, metrics)

        with pytest.raises(ConnectionError):
            mt.request("http://localhost/jsonrpc", data=b"{}")

        assert metrics.total_requests == 1
        assert metrics.total_errors == 1
        assert metrics.total_time_ms > 0

    def test_creates_default_metrics(self):
        inner = self._make_mock_transport()
        mt = MetricsTransport(inner)
        assert isinstance(mt.metrics, RequestMetrics)

    def test_passes_through_response(self):
        inner = self._make_mock_transport(status_code=200, body=b'{"result": "ok"}')
        mt = MetricsTransport(inner)

        resp = mt.request("http://localhost/jsonrpc")
        assert resp.status_code == 200
        assert resp.body == b'{"result": "ok"}'

    def test_close_delegates(self):
        inner = MagicMock()
        mt = MetricsTransport(inner)
        mt.close()
        inner.close.assert_called_once()

    def test_opener_property_with_urllib(self):
        mock_opener = MagicMock()
        inner = UrllibTransport(opener=mock_opener)
        mt = MetricsTransport(inner)
        assert mt.opener is mock_opener

    def test_opener_property_without_opener(self):
        inner = MagicMock(spec=[])  # No attributes
        mt = MetricsTransport(inner)
        assert mt.opener is None
