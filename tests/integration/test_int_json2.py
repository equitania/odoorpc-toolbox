"""Integration tests for the Odoo 19+ JSON-2 API (Bearer auth).

Requires the ODOO19_TEST_CONFIG environment variable pointing to a YAML
config for a live Odoo 19+ instance (see
yaml_examples/test_config_v19.yaml.example). All tests are skipped when
the variable is unset.

Run with:
    ODOO19_TEST_CONFIG=yaml_examples/test_config_v19.yaml pytest tests/integration/test_int_json2.py -v
"""

from __future__ import annotations

import pytest

from odoorpc_toolbox.exceptions import RPCError


@pytest.mark.integration
@pytest.mark.odoo19
class TestJson2Login:
    """Login bootstrap via res.users/context_get."""

    def test_login_established(self, odoo19):
        """The session fixture logged in - uid and context must be set."""
        assert odoo19.env.uid
        assert isinstance(odoo19.env.context, dict)

    def test_api_key_stored(self, odoo19):
        """After a v19 login the API key is stored for Bearer auth."""
        assert odoo19._api_key

    def test_uid_resolution(self, odoo19):
        """The bootstrapped uid matches the user behind the API key.

        Verifies the open design question whether context_get exposes the
        uid directly or the search fallback was needed - either way the
        resolved uid must identify a real, active user.
        """
        result = odoo19.execute_kw("res.users", "read", args=[[odoo19.env.uid], ["login"]])
        assert result and result[0]["id"] == odoo19.env.uid

    def test_invalid_api_key_raises(self, odoo19_config_path):
        """A wrong API key fails the bootstrap with RPCError (HTTP 401)."""
        import yaml

        from odoorpc_toolbox.odoo import ODOO

        with open(odoo19_config_path, encoding="utf-8") as fh:
            server = yaml.safe_load(fh)["Server"]
        url = server["url"].replace("https://", "").replace("http://", "").strip("/")
        protocol = "jsonrpc+ssl" if server["url"].startswith("https") else "jsonrpc"
        odoo = ODOO(url, protocol=protocol, port=server["port"])
        with pytest.raises(RPCError) as exc_info:
            odoo.login(server["database"], server["user"], api_key="definitely-wrong-key")
        assert exc_info.value.info.get("status_code") in (401, 403)


@pytest.mark.integration
@pytest.mark.odoo19
class TestJson2Execute:
    """execute/execute_kw via /json/2/."""

    def test_execute_kw_search_read_kwargs(self, odoo19):
        result = odoo19.execute_kw(
            "res.partner",
            "search_read",
            kwargs={"domain": [["is_company", "=", True]], "fields": ["name"], "limit": 3},
        )
        assert isinstance(result, list)
        assert all("name" in rec for rec in result)

    def test_execute_kw_positional_mapping(self, odoo19):
        """Positional args of known ORM methods map to named parameters."""
        ids = odoo19.execute_kw("res.partner", "search", args=[[]], kwargs={"limit": 2})
        assert isinstance(ids, list) and ids
        result = odoo19.execute_kw("res.partner", "read", args=[ids, ["name"]])
        assert isinstance(result, list)
        assert {rec["id"] for rec in result} == set(ids)

    def test_execute_positional(self, odoo19):
        """execute() delegates through the mapping table on v19."""
        count = odoo19.execute("res.partner", "search_count", [])
        assert isinstance(count, int)

    def test_create_write_unlink_roundtrip(self, odoo19, odoo19_data_manager):
        """Full CRUD cycle via JSON-2."""
        partner_id = odoo19_data_manager.create("res.partner", {"name": "JSON-2 Test Partner"})
        # create on Odoo 19 may return an int or a single-element list
        if isinstance(partner_id, list):
            partner_id = partner_id[0]
        result = odoo19.execute_kw("res.partner", "write", args=[[partner_id], {"name": "JSON-2 Renamed"}])
        assert result is True
        read_back = odoo19.execute_kw("res.partner", "read", args=[[partner_id], ["name"]])
        assert read_back[0]["name"] == "JSON-2 Renamed"

    def test_unknown_model_raises_rpc_error(self, odoo19):
        """HTTP 404 for an unknown model maps to RPCError."""
        with pytest.raises(RPCError) as exc_info:
            odoo19.execute_kw("nonexistent.model", "search", kwargs={"domain": []})
        assert exc_info.value.info.get("status_code", 0) >= 400

    def test_unmappable_method_falls_back_to_legacy(self, odoo19):
        """Unknown method with positional args uses /jsonrpc with a warning.

        The server rejects the nonexistent method with an RPCError - the
        DeprecationWarning plus a server-side error proves the request
        reached the legacy endpoint instead of failing client-side.
        """
        with pytest.warns(DeprecationWarning, match="Odoo 22"), pytest.raises(RPCError):
            odoo19.execute_kw("res.partner", "nonexistent_custom_method", [1])

    def test_context_propagation(self, odoo19):
        """A context kwarg is accepted by the JSON-2 endpoint."""
        result = odoo19.execute_kw(
            "res.partner",
            "search_read",
            kwargs={"domain": [], "fields": ["name"], "limit": 1, "context": {"lang": "en_US"}},
        )
        assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.odoo19
class TestJson2DbService:
    """DB service routing on Odoo 19+."""

    def test_db_list_via_web_controller(self, odoo19):
        dbs = odoo19.db.list()
        assert isinstance(dbs, list)
        assert odoo19.env.db in dbs


@pytest.mark.integration
@pytest.mark.odoo19
class TestJson2ReportService:
    """Report service behavior on Odoo 19+."""

    def test_download_raises_actionable_error(self, odoo19):
        report_names = odoo19.execute_kw(
            "ir.actions.report",
            "search_read",
            kwargs={"domain": [["report_type", "=", "qweb-pdf"]], "fields": ["report_name"], "limit": 1},
        )
        if not report_names:
            pytest.skip("No qweb-pdf report available on the test instance")
        with pytest.raises(NotImplementedError) as exc_info:
            odoo19.report.download(report_names[0]["report_name"], [1])
        assert "Workarounds" in str(exc_info.value)
