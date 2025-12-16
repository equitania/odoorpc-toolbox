"""Tests for MCP-compatible introspection module."""

import json
import pytest


class TestGetAvailableMethods:
    """Tests for get_available_methods function."""

    def test_returns_schema(self):
        """Test that get_available_methods returns a valid schema."""
        from odoorpc_toolbox import get_available_methods

        schema = get_available_methods()

        assert 'schema_version' in schema
        assert 'package' in schema
        assert 'version' in schema
        assert 'methods' in schema

    def test_schema_version(self):
        """Test that schema version is 1.0."""
        from odoorpc_toolbox import get_available_methods

        schema = get_available_methods()
        assert schema['schema_version'] == '1.0'

    def test_package_name(self):
        """Test that package name is correct."""
        from odoorpc_toolbox import get_available_methods

        schema = get_available_methods()
        assert schema['package'] == 'odoorpc-toolbox'

    def test_methods_list(self):
        """Test that methods list contains expected methods."""
        from odoorpc_toolbox import get_available_methods

        schema = get_available_methods()
        method_names = [m['name'] for m in schema['methods']]

        # Check for some expected methods
        assert 'get_state_id' in method_names
        assert 'get_country_id' in method_names
        assert 'create_partner' in method_names
        assert 'execute_method' in method_names
        assert 'search_read' in method_names

    def test_method_has_required_fields(self):
        """Test that each method has required schema fields."""
        from odoorpc_toolbox import get_available_methods

        schema = get_available_methods()

        for method in schema['methods']:
            assert 'name' in method
            assert 'description' in method
            assert 'parameters' in method
            assert 'returns' in method

    def test_parameters_structure(self):
        """Test that parameters follow JSON Schema structure."""
        from odoorpc_toolbox import get_available_methods

        schema = get_available_methods()

        for method in schema['methods']:
            params = method['parameters']
            assert params['type'] == 'object'
            assert 'properties' in params
            assert 'required' in params

    def test_json_serializable(self):
        """Test that schema is JSON serializable."""
        from odoorpc_toolbox import get_available_methods

        schema = get_available_methods()

        # Should not raise
        json_str = json.dumps(schema)
        assert len(json_str) > 0

        # Should be parseable back
        parsed = json.loads(json_str)
        assert parsed == schema


class TestGetMethodSchema:
    """Tests for get_method_schema function."""

    def test_existing_method(self):
        """Test getting schema for an existing method."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('get_state_id')

        assert schema is not None
        assert schema['name'] == 'get_state_id'
        assert 'country_id' in schema['parameters']['properties']
        assert 'state_name' in schema['parameters']['properties']

    def test_nonexistent_method(self):
        """Test getting schema for a non-existent method."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('nonexistent_method')
        assert schema is None

    def test_private_method(self):
        """Test that private methods return None."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('_private_method')
        assert schema is None

    def test_parameter_types(self):
        """Test that parameter types are correctly mapped."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('get_state_id')

        props = schema['parameters']['properties']
        assert props['country_id']['type'] == 'integer'
        assert props['state_name']['type'] == 'string'

    def test_return_type(self):
        """Test that return type is correctly mapped."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('get_state_id')

        assert schema['returns']['type'] == 'integer'
        assert schema['returns'].get('nullable') is True

    def test_required_parameters(self):
        """Test that required parameters are correctly identified."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('get_state_id')

        required = schema['parameters']['required']
        assert 'country_id' in required
        assert 'state_name' in required


class TestNewMethods:
    """Tests for new helper methods."""

    def test_get_country_id_schema(self):
        """Test get_country_id method schema."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('get_country_id')

        assert schema is not None
        assert 'country_name' in schema['parameters']['properties']
        assert schema['parameters']['properties']['country_name']['type'] == 'string'

    def test_create_partner_schema(self):
        """Test create_partner method schema."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('create_partner')

        assert schema is not None
        props = schema['parameters']['properties']
        assert 'name' in props
        assert 'is_company' in props
        assert 'email' in props
        assert props['is_company']['type'] == 'boolean'

    def test_execute_method_schema(self):
        """Test execute_method method schema."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('execute_method')

        assert schema is not None
        props = schema['parameters']['properties']
        assert 'model' in props
        assert 'method' in props
        assert props['model']['type'] == 'string'

    def test_search_read_schema(self):
        """Test search_read method schema."""
        from odoorpc_toolbox import get_method_schema

        schema = get_method_schema('search_read')

        assert schema is not None
        props = schema['parameters']['properties']
        assert 'model' in props
        assert 'domain' in props
        assert 'fields' in props
        assert 'limit' in props
