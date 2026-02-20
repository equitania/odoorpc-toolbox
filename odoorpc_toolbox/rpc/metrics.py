"""Request metrics and instrumented transport decorator.

Provides thread-safe request metrics collection and a MetricsTransport wrapper
that records timing and error data for any Transport implementation.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from odoorpc_toolbox.rpc.transport import Transport, TransportResponse


@dataclass
class RequestMetrics:
    """Thread-safe request metrics collector.

    Tracks total requests, errors, and cumulative response time.

    Attributes:
        total_requests: Number of completed requests.
        total_errors: Number of failed requests.
        total_time_ms: Cumulative response time in milliseconds.

    Example:
        >>> metrics = RequestMetrics()
        >>> metrics.record(time_ms=45.2)
        >>> metrics.record(time_ms=120.5, error=True)
        >>> metrics.total_requests
        2
        >>> metrics.avg_time_ms
        82.85
    """

    total_requests: int = 0
    total_errors: int = 0
    total_time_ms: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def record(self, time_ms: float, error: bool = False) -> None:
        """Record a completed request.

        Args:
            time_ms: Response time in milliseconds.
            error: Whether the request resulted in an error.
        """
        with self._lock:
            self.total_requests += 1
            self.total_time_ms += time_ms
            if error:
                self.total_errors += 1

    def reset(self) -> None:
        """Reset all metrics to zero."""
        with self._lock:
            self.total_requests = 0
            self.total_errors = 0
            self.total_time_ms = 0.0

    @property
    def avg_time_ms(self) -> float:
        """Average response time in milliseconds. Returns 0.0 if no requests recorded."""
        with self._lock:
            if self.total_requests == 0:
                return 0.0
            return self.total_time_ms / self.total_requests

    @property
    def error_rate(self) -> float:
        """Error rate as a fraction (0.0 to 1.0). Returns 0.0 if no requests recorded."""
        with self._lock:
            if self.total_requests == 0:
                return 0.0
            return self.total_errors / self.total_requests


class MetricsTransport:
    """Decorator transport that records request metrics.

    Wraps any Transport implementation and transparently records
    timing and error data for each request.

    Args:
        transport: The underlying Transport to wrap.
        metrics: RequestMetrics instance. If None, creates a new one.

    Example:
        >>> from odoorpc_toolbox.rpc.transport import UrllibTransport
        >>> inner = UrllibTransport()
        >>> metrics = RequestMetrics()
        >>> transport = MetricsTransport(inner, metrics)
        >>> # Use transport.request() as normal; metrics are recorded automatically
        >>> metrics.total_requests
        0
    """

    def __init__(self, transport: Transport, metrics: RequestMetrics | None = None) -> None:
        self._transport = transport
        self._metrics = metrics or RequestMetrics()

    @property
    def metrics(self) -> RequestMetrics:
        """Return the metrics collector."""
        return self._metrics

    @property
    def opener(self):
        """Return the underlying transport's opener for backward compatibility.

        Raises:
            AttributeError: If the underlying transport has no opener.
        """
        return getattr(self._transport, "opener", None)

    def request(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Execute a request and record metrics.

        Args:
            url: The full URL to request.
            data: Request body as bytes.
            headers: HTTP headers dict.
            timeout: Request timeout in seconds.

        Returns:
            TransportResponse from the underlying transport.
        """
        start = time.monotonic()
        error = False
        try:
            response = self._transport.request(url, data, headers, timeout)
            if response.status_code >= 500:
                error = True
            return response
        except Exception:
            error = True
            raise
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            self._metrics.record(time_ms=elapsed_ms, error=error)

    def close(self) -> None:
        """Close the underlying transport."""
        self._transport.close()
