"""Tests for the unified exception hierarchy."""

import pytest

from odoorpc_toolbox.exceptions import (
    Error,
    InternalError,
    OdooAuthError,
    OdooConfigError,
    OdooConnectionError,
    RPCError,
)
from odoorpc_toolbox.rpc.errors import ConnectorError


class TestOdooRPCExceptions:
    """Tests for OdooRPC-level exceptions."""

    def test_error_base(self):
        exc = Error("base error")
        assert str(exc) == "base error"
        assert isinstance(exc, Exception)

    def test_rpc_error(self):
        info = {"message": "Access Denied", "code": 403}
        exc = RPCError("Access Denied", info=info)
        assert str(exc) == "Access Denied"
        assert exc.info == info
        assert isinstance(exc, Error)

    def test_rpc_error_default_info(self):
        exc = RPCError("error")
        assert exc.info is False

    def test_rpc_error_repr(self):
        exc = RPCError("test error")
        assert repr(exc) == "RPCError('test error')"

    def test_internal_error(self):
        exc = InternalError("internal")
        assert str(exc) == "internal"
        assert isinstance(exc, Error)


class TestToolboxExceptions:
    """Tests for toolbox-level exceptions."""

    def test_odoo_connection_error(self):
        exc = OdooConnectionError("conn failed")
        assert str(exc) == "conn failed"
        assert isinstance(exc, Exception)

    def test_config_error_inherits(self):
        assert issubclass(OdooConfigError, OdooConnectionError)
        with pytest.raises(OdooConnectionError):
            raise OdooConfigError("bad config")

    def test_auth_error_inherits(self):
        assert issubclass(OdooAuthError, OdooConnectionError)
        with pytest.raises(OdooConnectionError):
            raise OdooAuthError("bad auth")


class TestConnectorError:
    """Tests for RPC connector error."""

    def test_connector_error(self):
        exc = ConnectorError("connection refused")
        assert str(exc) == "connection refused"
        assert exc.message == "connection refused"
        assert exc.odoo_traceback is None

    def test_connector_error_with_traceback(self):
        exc = ConnectorError("error", odoo_traceback="traceback info")
        assert exc.odoo_traceback == "traceback info"

    def test_connector_error_is_exception(self):
        assert issubclass(ConnectorError, Exception)
