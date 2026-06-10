"""Tests for the configuration file generator."""

import os

import pytest
import yaml

from odoorpc_toolbox.config_generator import generate_config, main


class TestGenerateConfig:
    """Tests for the generate_config function."""

    def test_creates_default_config(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml")
        assert path.exists()
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "Server" in data
        assert data["Server"]["url"] == "https://odoo.example.com"
        assert data["Server"]["port"] == 443

    def test_full_config_has_all_sections(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "Server" in data
        assert "transport" in data
        assert "retry" in data
        assert "timeout" in data
        assert "cache" in data

    def test_api_key_commented_hint_by_default(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml")
        content = path.read_text(encoding="utf-8")
        assert "# api_key:" in content
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "api_key" not in data["Server"]

    def test_api_key_rendered_when_given(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml", api_key="my_secret_key")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["Server"]["api_key"] == "my_secret_key"

    def test_api_key_in_minimal_config(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml", api_key="key123", minimal=True)
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["Server"]["api_key"] == "key123"

    def test_transport_defaults(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["transport"]["backend"] == "auto"
        assert data["transport"]["http2"] is True
        assert data["transport"]["pool_connections"] == 10

    def test_retry_defaults(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["retry"]["max_attempts"] == 3
        assert data["retry"]["backoff_factor"] == 0.5
        assert data["retry"]["retry_on"] == [502, 503, 504]

    def test_timeout_defaults(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["timeout"]["connect"] == 30
        assert data["timeout"]["read"] == 120

    def test_cache_defaults(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["cache"]["maxsize"] == 256
        assert data["cache"]["ttl"] == 3600

    def test_custom_server_values(self, tmp_path):
        path = generate_config(
            tmp_path / "config.yaml",
            url="http://localhost",
            port=8069,
            user="test_user",
            password="test_pw",
            database="test_db",
            protocol="jsonrpc",
        )
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["Server"]["url"] == "http://localhost"
        assert data["Server"]["port"] == 8069
        assert data["Server"]["user"] == "test_user"
        assert data["Server"]["password"] == "test_pw"
        assert data["Server"]["database"] == "test_db"
        assert data["Server"]["protocol"] == "jsonrpc"

    def test_minimal_config(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml", minimal=True)
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "Server" in data
        assert "transport" not in data
        assert "retry" not in data
        assert "timeout" not in data
        assert "cache" not in data

    def test_file_exists_error(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("existing", encoding="utf-8")
        with pytest.raises(FileExistsError, match="already exists"):
            generate_config(path)

    def test_overwrite_existing(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("old content", encoding="utf-8")
        generate_config(path, overwrite=True)
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "Server" in data

    def test_creates_parent_directories(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "config.yaml"
        generate_config(path)
        assert path.exists()

    def test_returns_path_object(self, tmp_path):
        result = generate_config(tmp_path / "config.yaml")
        assert result == tmp_path / "config.yaml"

    def test_string_path_accepted(self, tmp_path):
        path_str = str(tmp_path / "config.yaml")
        result = generate_config(path_str)
        assert result.exists()

    def test_utf8_encoding(self, tmp_path):
        path = generate_config(tmp_path / "config.yaml")
        content = path.read_text(encoding="utf-8")
        assert "Server:" in content

    def test_generated_config_loadable_by_odoo_connection(self, tmp_path):
        """Verify the generated config is compatible with OdooConnection parsing."""
        path = generate_config(tmp_path / "config.yaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        conn = data["Server"]
        assert "url" in conn
        assert "port" in conn
        assert "user" in conn
        assert "password" in conn
        assert "database" in conn
        assert "protocol" in conn


class TestCLI:
    """Tests for the CLI entry point."""

    def test_default_output(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        exit_code = main([])
        assert exit_code == 0
        assert (tmp_path / "odoo_config.yaml").exists()

    def test_custom_output(self, tmp_path):
        output = str(tmp_path / "custom.yaml")
        exit_code = main(["-o", output])
        assert exit_code == 0
        assert os.path.exists(output)

    def test_minimal_flag(self, tmp_path):
        output = str(tmp_path / "minimal.yaml")
        exit_code = main(["-o", output, "--minimal"])
        assert exit_code == 0
        with open(output, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "transport" not in data

    def test_custom_url_and_port(self, tmp_path):
        output = str(tmp_path / "config.yaml")
        exit_code = main(["-o", output, "--url", "http://localhost", "--port", "8069"])
        assert exit_code == 0
        with open(output, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["Server"]["url"] == "http://localhost"
        assert data["Server"]["port"] == 8069

    def test_exists_error_without_force(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        main([])  # Create first
        exit_code = main([])  # Try again
        assert exit_code == 1

    def test_force_overwrites(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        main([])
        exit_code = main(["--force"])
        assert exit_code == 0

    def test_protocol_choice(self, tmp_path):
        output = str(tmp_path / "config.yaml")
        exit_code = main(["-o", output, "--protocol", "jsonrpc+ssl"])
        assert exit_code == 0
        with open(output, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["Server"]["protocol"] == "jsonrpc+ssl"

    def test_database_flag(self, tmp_path):
        output = str(tmp_path / "config.yaml")
        exit_code = main(["-o", output, "--database", "production"])
        assert exit_code == 0
        with open(output, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["Server"]["database"] == "production"
