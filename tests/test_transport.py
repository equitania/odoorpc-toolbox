"""Tests for the transport abstraction layer."""

import json
from http.cookiejar import CookieJar
from unittest.mock import MagicMock, patch

import pytest

from odoorpc_toolbox.rpc.transport import (
    HttpxTransport,
    RetryConfig,
    Transport,
    TransportResponse,
    UrllibTransport,
    create_transport,
)

# ---- TransportResponse Tests ----


class TestTransportResponse:
    """Tests for the TransportResponse dataclass."""

    def test_basic_attributes(self):
        resp = TransportResponse(status_code=200, body=b"hello", headers={"Content-Type": "text/plain"})
        assert resp.status_code == 200
        assert resp.body == b"hello"
        assert resp.headers == {"Content-Type": "text/plain"}

    def test_default_headers(self):
        resp = TransportResponse(status_code=200, body=b"")
        assert resp.headers == {}

    def test_read_returns_body(self):
        resp = TransportResponse(status_code=200, body=b"test data")
        assert resp.read() == b"test data"

    def test_read_empty_body(self):
        resp = TransportResponse(status_code=204, body=b"")
        assert resp.read() == b""

    def test_json_parsing(self):
        data = {"jsonrpc": "2.0", "result": [1, 2, 3]}
        resp = TransportResponse(status_code=200, body=json.dumps(data).encode("utf-8"))
        assert resp.json() == data

    def test_json_unicode(self):
        data = {"name": "Stra\u00dfe"}
        resp = TransportResponse(status_code=200, body=json.dumps(data).encode("utf-8"))
        result = resp.json()
        assert result["name"] == "Straße"

    def test_json_invalid_raises(self):
        resp = TransportResponse(status_code=200, body=b"not json")
        with pytest.raises(json.JSONDecodeError):
            resp.json()


# ---- UrllibTransport Tests ----


class TestUrllibTransport:
    """Tests for the UrllibTransport class."""

    def test_creates_default_opener(self):
        transport = UrllibTransport()
        assert transport.opener is not None

    def test_uses_provided_opener(self):
        mock_opener = MagicMock()
        transport = UrllibTransport(opener=mock_opener)
        assert transport.opener is mock_opener

    def test_uses_provided_cookie_jar(self):
        jar = CookieJar()
        transport = UrllibTransport(cookie_jar=jar)
        assert transport.opener is not None

    def test_opener_property_backward_compat(self):
        transport = UrllibTransport()
        opener = transport.opener
        assert opener is not None
        assert hasattr(opener, "open")

    def test_request_with_mock_opener(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"result": "ok"}'
        mock_response.getcode.return_value = 200
        mock_response.headers.items.return_value = [("Content-Type", "application/json")]

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        transport = UrllibTransport(opener=mock_opener)
        result = transport.request("http://localhost:8069/jsonrpc", data=b'{"test": 1}')

        assert isinstance(result, TransportResponse)
        assert result.status_code == 200
        assert result.body == b'{"result": "ok"}'
        mock_opener.open.assert_called_once()

    def test_request_with_headers(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"{}"
        mock_response.getcode.return_value = 200
        mock_response.headers.items.return_value = []

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        transport = UrllibTransport(opener=mock_opener)
        transport.request(
            "http://localhost:8069/jsonrpc",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )

        # Verify the request was created with headers
        call_args = mock_opener.open.call_args
        request_obj = call_args[0][0]
        assert request_obj.get_header("Content-type") == "application/json"

    def test_request_with_timeout(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"{}"
        mock_response.getcode.return_value = 200
        mock_response.headers.items.return_value = []

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        transport = UrllibTransport(opener=mock_opener)
        transport.request("http://localhost:8069/jsonrpc", timeout=30)

        call_args = mock_opener.open.call_args
        assert call_args[1]["timeout"] == 30

    def test_request_without_timeout(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"{}"
        mock_response.getcode.return_value = 200
        mock_response.headers.items.return_value = []

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        transport = UrllibTransport(opener=mock_opener)
        transport.request("http://localhost:8069/jsonrpc")

        call_args = mock_opener.open.call_args
        assert "timeout" not in call_args[1]

    def test_request_get_without_data(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"OK"
        mock_response.getcode.return_value = 200
        mock_response.headers.items.return_value = []

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        transport = UrllibTransport(opener=mock_opener)
        result = transport.request("http://localhost:8069/web")

        assert result.status_code == 200
        assert result.body == b"OK"

    def test_request_status_code_none_defaults_200(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b""
        mock_response.getcode.return_value = None
        mock_response.headers.items.return_value = []

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        transport = UrllibTransport(opener=mock_opener)
        result = transport.request("http://localhost:8069/jsonrpc")
        assert result.status_code == 200

    def test_close_is_noop(self):
        transport = UrllibTransport()
        transport.close()  # Should not raise

    def test_implements_transport_protocol(self):
        transport = UrllibTransport()
        assert isinstance(transport, Transport)


# ---- RetryConfig Tests ----


class TestRetryConfig:
    """Tests for the RetryConfig dataclass."""

    def test_default_values(self):
        cfg = RetryConfig()
        assert cfg.max_attempts == 3
        assert cfg.backoff_factor == 0.5
        assert cfg.retry_on == (502, 503, 504)

    def test_custom_values(self):
        cfg = RetryConfig(max_attempts=5, backoff_factor=1.0, retry_on=(500, 502))
        assert cfg.max_attempts == 5
        assert cfg.backoff_factor == 1.0
        assert cfg.retry_on == (500, 502)


# ---- create_transport Factory Tests ----


class TestCreateTransport:
    """Tests for the create_transport factory function."""

    def test_urllib_backend(self):
        transport = create_transport(backend="urllib")
        assert isinstance(transport, UrllibTransport)

    def test_urllib_with_opener(self):
        mock_opener = MagicMock()
        transport = create_transport(backend="urllib", opener=mock_opener)
        assert isinstance(transport, UrllibTransport)
        assert transport.opener is mock_opener

    def test_urllib_with_cookie_jar(self):
        jar = CookieJar()
        transport = create_transport(backend="urllib", cookie_jar=jar)
        assert isinstance(transport, UrllibTransport)

    def test_auto_falls_back_to_urllib(self):
        with patch.dict("sys.modules", {"httpx": None}):
            transport = create_transport(backend="auto")
            assert isinstance(transport, UrllibTransport)

    def test_invalid_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown transport backend"):
            create_transport(backend="invalid")

    def test_httpx_backend_without_httpx_raises(self):
        with patch.dict("sys.modules", {"httpx": None}):
            with pytest.raises(ImportError):
                create_transport(backend="httpx")


# ---- HttpxTransport Tests (conditional) ----


class TestHttpxTransport:
    """Tests for HttpxTransport (requires httpx)."""

    @pytest.fixture(autouse=True)
    def _check_httpx(self):
        pytest.importorskip("httpx")

    def test_create_httpx_transport(self):
        transport = HttpxTransport(http2=False)
        assert isinstance(transport, Transport)
        transport.close()

    def test_httpx_with_retry_config(self):
        cfg = RetryConfig(max_attempts=2)
        transport = HttpxTransport(http2=False, retry_config=cfg)
        assert transport._retry_config is cfg
        transport.close()

    def test_httpx_close(self):
        transport = HttpxTransport(http2=False)
        transport.close()  # Should not raise

    @patch("httpx.Client")
    def test_httpx_request_post(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"result": "ok"}'
        mock_response.headers = {"Content-Type": "application/json"}

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value = mock_client

        transport = HttpxTransport(http2=False)
        result = transport.request(
            "http://localhost:8069/jsonrpc",
            data=b'{"test": 1}',
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert result.status_code == 200
        assert result.body == b'{"result": "ok"}'
        mock_client.request.assert_called_once_with(
            method="POST",
            url="http://localhost:8069/jsonrpc",
            content=b'{"test": 1}',
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        transport.close()

    @patch("httpx.Client")
    def test_httpx_request_get(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"OK"
        mock_response.headers = {}

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value = mock_client

        transport = HttpxTransport(http2=False)
        result = transport.request("http://localhost:8069/web")

        mock_client.request.assert_called_once_with(
            method="GET",
            url="http://localhost:8069/web",
            content=None,
            headers=None,
            timeout=None,
        )
        assert result.status_code == 200
        transport.close()

    @patch("httpx.Client")
    @patch("time.sleep")
    def test_httpx_retry_on_502(self, mock_sleep, mock_client_cls):
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 502
        mock_response_fail.content = b"Bad Gateway"
        mock_response_fail.headers = {}

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.content = b'{"result": "ok"}'
        mock_response_ok.headers = {}

        mock_client = MagicMock()
        mock_client.request.side_effect = [mock_response_fail, mock_response_ok]
        mock_client_cls.return_value = mock_client

        cfg = RetryConfig(max_attempts=3, backoff_factor=0.1)
        transport = HttpxTransport(http2=False, retry_config=cfg)
        result = transport.request("http://localhost:8069/jsonrpc", data=b"{}")

        assert result.status_code == 200
        assert mock_client.request.call_count == 2
        mock_sleep.assert_called_once()
        transport.close()

    @patch("httpx.Client")
    @patch("time.sleep")
    def test_httpx_retry_exhausted(self, mock_sleep, mock_client_cls):
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 503
        mock_response_fail.content = b"Service Unavailable"
        mock_response_fail.headers = {}

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response_fail
        mock_client_cls.return_value = mock_client

        cfg = RetryConfig(max_attempts=2, backoff_factor=0.01)
        transport = HttpxTransport(http2=False, retry_config=cfg)
        result = transport.request("http://localhost:8069/jsonrpc", data=b"{}")

        # After exhausting retries, returns the last response
        assert result.status_code == 503
        assert mock_client.request.call_count == 2
        transport.close()

    @patch("httpx.Client")
    @patch("time.sleep")
    def test_httpx_retry_on_exception(self, mock_sleep, mock_client_cls):
        import httpx

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.content = b"{}"
        mock_response_ok.headers = {}

        mock_client = MagicMock()
        mock_client.request.side_effect = [
            httpx.ConnectError("Connection refused"),
            mock_response_ok,
        ]
        mock_client_cls.return_value = mock_client

        cfg = RetryConfig(max_attempts=3, backoff_factor=0.01)
        transport = HttpxTransport(http2=False, retry_config=cfg)
        result = transport.request("http://localhost:8069/jsonrpc", data=b"{}")

        assert result.status_code == 200
        assert mock_client.request.call_count == 2
        transport.close()

    @patch("httpx.Client")
    @patch("time.sleep")
    def test_httpx_retry_exception_exhausted(self, mock_sleep, mock_client_cls):
        import httpx

        mock_client = MagicMock()
        mock_client.request.side_effect = httpx.ConnectError("Connection refused")
        mock_client_cls.return_value = mock_client

        cfg = RetryConfig(max_attempts=2, backoff_factor=0.01)
        transport = HttpxTransport(http2=False, retry_config=cfg)

        with pytest.raises(httpx.ConnectError):
            transport.request("http://localhost:8069/jsonrpc", data=b"{}")

        assert mock_client.request.call_count == 2
        transport.close()

    def test_httpx_no_retry_when_not_configured(self):

        transport = HttpxTransport(http2=False, retry_config=None)
        # No retry config means single attempt
        assert transport._retry_config is None
        transport.close()

    def test_auto_selects_httpx_when_available(self):
        transport = create_transport(backend="auto", http2=False)
        assert isinstance(transport, HttpxTransport)
        transport.close()

    def test_httpx_explicit_backend(self):
        transport = create_transport(backend="httpx", http2=False)
        assert isinstance(transport, HttpxTransport)
        transport.close()
