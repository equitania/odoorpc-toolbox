"""Transport abstraction layer for RPC communication.

Provides a unified Transport protocol with UrllibTransport (default) and
HttpxTransport (optional, requires httpx[http2]) implementations.
Supports connection pooling, retry logic, and HTTP/2 via the httpx backend.
"""

from __future__ import annotations

import json as json_mod
import time
import urllib.error
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from typing import Protocol, runtime_checkable
from urllib.request import HTTPCookieProcessor, Request, build_opener


@dataclass
class TransportResponse:
    """Unified response wrapper for both urllib and httpx backends.

    Attributes:
        status_code: HTTP status code.
        body: Raw response body as bytes.
        headers: Response headers as a dict.
    """

    status_code: int
    body: bytes
    headers: dict[str, str] = field(default_factory=dict)

    def read(self) -> bytes:
        """Return the raw body bytes. Backward-compatible with urllib response."""
        return self.body

    def json(self) -> dict:
        """Parse body as JSON and return the result dict."""
        return json_mod.loads(self.body.decode("utf-8"))


@runtime_checkable
class Transport(Protocol):
    """Protocol defining the transport interface for RPC communication."""

    def request(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> TransportResponse: ...

    def close(self) -> None: ...


@dataclass
class RetryConfig:
    """Configuration for request retry behavior.

    Attributes:
        max_attempts: Maximum number of request attempts (default: 3).
        backoff_factor: Base factor for exponential backoff in seconds (default: 0.5).
        retry_on: HTTP status codes that trigger a retry (default: 502, 503, 504).
    """

    max_attempts: int = 3
    backoff_factor: float = 0.5
    retry_on: tuple[int, ...] = (502, 503, 504)


class UrllibTransport:
    """Transport implementation wrapping the standard urllib opener.

    Uses urllib.request with CookieJar for session management.
    This is the default transport and requires no extra dependencies.

    Args:
        opener: Pre-configured urllib opener. If None, creates one with CookieJar.
        cookie_jar: CookieJar instance for cookie handling. Ignored if opener is given.
    """

    def __init__(self, opener=None, cookie_jar: CookieJar | None = None) -> None:
        if opener is not None:
            self._opener = opener
        else:
            if cookie_jar is None:
                cookie_jar = CookieJar()
            self._opener = build_opener(HTTPCookieProcessor(cookie_jar))

    @property
    def opener(self):
        """Return the underlying urllib opener for backward compatibility."""
        return self._opener

    def request(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Execute an HTTP request via urllib.

        Args:
            url: The full URL to request.
            data: Request body as bytes.
            headers: HTTP headers dict.
            timeout: Request timeout in seconds.

        Returns:
            TransportResponse with status, body, and headers.
            HTTP error statuses (4xx/5xx) are returned as responses, not
            raised, matching the HttpxTransport behavior so callers can map
            status codes to exceptions themselves.
        """
        req = Request(url=url, data=data)
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout

        try:
            response = self._opener.open(req, **kwargs)
        except urllib.error.HTTPError as exc:
            # exc.read() is single-use - read once and store
            body = exc.read()
            resp_headers = {k: v for k, v in exc.headers.items()} if exc.headers else {}
            return TransportResponse(status_code=exc.code, body=body, headers=resp_headers)
        body = response.read()
        status_code = response.getcode() or 200
        resp_headers = {k: v for k, v in response.headers.items()}
        return TransportResponse(status_code=status_code, body=body, headers=resp_headers)

    def close(self) -> None:
        """Close the transport. No-op for urllib (no persistent connections)."""
        pass


class HttpxTransport:
    """Transport implementation using httpx with connection pooling and HTTP/2.

    Requires the ``httpx[http2]`` package. Provides synchronous HTTP client
    with configurable retry logic, connection pooling, and optional HTTP/2 support.

    Args:
        http2: Enable HTTP/2 support (default: True).
        retry_config: Retry configuration. None disables retries.
        pool_connections: Maximum number of pooled connections (default: 10).
        pool_maxsize: Maximum pool size (default: 10).
        verify: SSL verification (default: True).

    Raises:
        ImportError: If httpx is not installed.
    """

    def __init__(
        self,
        http2: bool = True,
        retry_config: RetryConfig | None = None,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        verify: bool = True,
    ) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise ImportError(
                "httpx is required for HttpxTransport. " "Install it with: pip install 'httpx[http2]>=0.25.0'"
            ) from exc

        self._retry_config = retry_config
        limits = httpx.Limits(
            max_connections=pool_connections,
            max_keepalive_connections=pool_maxsize,
        )
        self._client = httpx.Client(
            http2=http2,
            limits=limits,
            verify=verify,
        )

    def request(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Execute an HTTP request via httpx with optional retry logic.

        Args:
            url: The full URL to request.
            data: Request body as bytes.
            headers: HTTP headers dict.
            timeout: Request timeout in seconds.

        Returns:
            TransportResponse with status, body, and headers.
        """
        if self._retry_config and self._retry_config.max_attempts > 1:
            return self._request_with_retry(url, data, headers, timeout)
        return self._do_request(url, data, headers, timeout)

    def _do_request(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Execute a single request without retry."""
        import httpx

        method = "POST" if data is not None else "GET"
        try:
            response = self._client.request(
                method=method,
                url=url,
                content=data,
                headers=headers,
                timeout=timeout,
            )
        except httpx.TimeoutException:
            raise
        except httpx.HTTPError:
            raise

        resp_headers = {k: v for k, v in response.headers.items()}
        return TransportResponse(
            status_code=response.status_code,
            body=response.content,
            headers=resp_headers,
        )

    def _request_with_retry(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Execute a request with exponential backoff retry logic."""
        import random

        cfg = self._retry_config
        last_exc = None

        for attempt in range(cfg.max_attempts):
            try:
                response = self._do_request(url, data, headers, timeout)
                if response.status_code not in cfg.retry_on:
                    return response
                if attempt < cfg.max_attempts - 1:
                    backoff = cfg.backoff_factor * (2**attempt)
                    jitter = random.uniform(0, backoff * 0.1)
                    time.sleep(backoff + jitter)
                    continue
                return response
            except Exception as exc:
                last_exc = exc
                if attempt < cfg.max_attempts - 1:
                    backoff = cfg.backoff_factor * (2**attempt)
                    jitter = random.uniform(0, backoff * 0.1)
                    time.sleep(backoff + jitter)
                else:
                    raise

        raise last_exc  # pragma: no cover

    def close(self) -> None:
        """Close the httpx client and release connections."""
        self._client.close()


def create_transport(
    backend: str = "auto",
    opener=None,
    cookie_jar: CookieJar | None = None,
    **kwargs,
) -> Transport:
    """Factory function to create a Transport instance.

    Args:
        backend: Transport backend - 'auto', 'urllib', or 'httpx'.
            'auto' tries httpx first, falls back to urllib.
        opener: Pre-configured urllib opener (only for urllib backend).
        cookie_jar: CookieJar for urllib backend.
        **kwargs: Additional arguments passed to the transport constructor.
            For httpx: http2, retry_config, pool_connections, pool_maxsize, verify.

    Returns:
        A Transport instance.

    Raises:
        ValueError: If backend is not recognized.
        ImportError: If httpx backend is requested but not installed.
    """
    if backend == "urllib":
        return UrllibTransport(opener=opener, cookie_jar=cookie_jar)
    elif backend == "httpx":
        return HttpxTransport(**kwargs)
    elif backend == "auto":
        try:
            return HttpxTransport(**kwargs)
        except ImportError:
            return UrllibTransport(opener=opener, cookie_jar=cookie_jar)
    else:
        raise ValueError(f"Unknown transport backend: '{backend}'. Choose from: 'auto', 'urllib', 'httpx'.")
