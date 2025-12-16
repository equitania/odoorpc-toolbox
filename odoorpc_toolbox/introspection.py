"""MCP-compatible introspection module for odoorpc-toolbox.

This module provides method discovery functionality compatible with
Model Context Protocol (MCP) servers. It allows external systems to
discover available methods, their parameters, and return types.

Example:
    from odoorpc_toolbox import get_available_methods, get_method_schema

    # Get all available methods
    methods = get_available_methods()

    # Get schema for specific method
    schema = get_method_schema('get_state_id')
"""

import inspect
import re
from typing import Any, Dict, List, Optional, get_type_hints

from ._version import __version__


# Type mapping for JSON Schema
PYTHON_TO_JSON_TYPE = {
    'int': 'integer',
    'str': 'string',
    'bool': 'boolean',
    'float': 'number',
    'list': 'array',
    'dict': 'object',
    'List': 'array',
    'Dict': 'object',
    'Tuple': 'array',
    'None': 'null',
    'NoneType': 'null',
    'Optional': None,  # Handled specially
    'Union': None,  # Handled specially
    'Any': 'any',
}


def _parse_docstring(docstring: Optional[str]) -> Dict[str, Any]:
    """Parse Google-style docstring into structured data.

    Args:
        docstring: The docstring to parse.

    Returns:
        Dictionary with 'description', 'args', and 'returns' keys.
    """
    if not docstring:
        return {'description': '', 'args': {}, 'returns': ''}

    result = {'description': '', 'args': {}, 'returns': ''}

    lines = docstring.strip().split('\n')
    current_section = 'description'
    current_arg = None
    description_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('Args:'):
            current_section = 'args'
            continue
        elif stripped.startswith('Returns:'):
            current_section = 'returns'
            continue
        elif stripped.startswith('Raises:'):
            current_section = 'raises'
            continue
        elif stripped.startswith('Example:'):
            current_section = 'example'
            continue

        if current_section == 'description':
            if stripped:
                description_lines.append(stripped)
        elif current_section == 'args':
            # Match "param_name: description" pattern
            match = re.match(r'^(\w+):\s*(.*)$', stripped)
            if match:
                current_arg = match.group(1)
                result['args'][current_arg] = match.group(2)
            elif current_arg and stripped:
                result['args'][current_arg] += ' ' + stripped
        elif current_section == 'returns':
            if stripped:
                result['returns'] += stripped + ' '

    result['description'] = ' '.join(description_lines)
    result['returns'] = result['returns'].strip()

    return result


def _type_to_json_schema(type_hint: Any) -> Dict[str, Any]:
    """Convert Python type hint to JSON Schema type.

    Args:
        type_hint: Python type hint to convert.

    Returns:
        JSON Schema type definition.
    """
    if type_hint is None:
        return {'type': 'null'}

    type_str = str(type_hint)

    # Handle Optional[X] -> X with nullable
    if 'Optional' in type_str:
        inner_match = re.search(r'Optional\[(\w+)\]', type_str)
        if inner_match:
            inner_type = inner_match.group(1)
            json_type = PYTHON_TO_JSON_TYPE.get(inner_type, 'any')
            return {'type': json_type, 'nullable': True}

    # Handle List[X]
    if 'List' in type_str or 'list' in type_str:
        return {'type': 'array'}

    # Handle Tuple[X, Y]
    if 'Tuple' in type_str or 'tuple' in type_str:
        return {'type': 'array'}

    # Handle Dict[X, Y]
    if 'Dict' in type_str or 'dict' in type_str:
        return {'type': 'object'}

    # Handle basic types
    if hasattr(type_hint, '__name__'):
        type_name = type_hint.__name__
    else:
        type_name = type_str.replace('typing.', '').split('[')[0]

    json_type = PYTHON_TO_JSON_TYPE.get(type_name, 'any')
    return {'type': json_type}


def get_method_schema(method_name: str, cls: type = None) -> Optional[Dict[str, Any]]:
    """Get MCP-compatible JSON Schema for a specific method.

    Args:
        method_name: Name of the method to get schema for.
        cls: Class to inspect (defaults to EqOdooConnection).

    Returns:
        MCP-compatible method schema or None if method not found.
    """
    if cls is None:
        from .base_helper import EqOdooConnection
        cls = EqOdooConnection

    if not hasattr(cls, method_name):
        return None

    method = getattr(cls, method_name)
    if not callable(method):
        return None

    # Skip private/magic methods
    if method_name.startswith('_'):
        return None

    # Get type hints
    try:
        hints = get_type_hints(method)
    except Exception:
        hints = {}

    # Get signature
    try:
        sig = inspect.signature(method)
    except Exception:
        return None

    # Parse docstring
    doc_info = _parse_docstring(method.__doc__)

    # Build parameters schema
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue

        param_schema = {}

        # Get type from hints
        if param_name in hints:
            param_schema = _type_to_json_schema(hints[param_name])
        else:
            param_schema = {'type': 'any'}

        # Add description from docstring
        if param_name in doc_info['args']:
            param_schema['description'] = doc_info['args'][param_name]

        properties[param_name] = param_schema

        # Check if required (no default value)
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    # Build return schema
    return_schema = {'type': 'any'}
    if 'return' in hints:
        return_schema = _type_to_json_schema(hints['return'])
    if doc_info['returns']:
        return_schema['description'] = doc_info['returns']

    return {
        'name': method_name,
        'description': doc_info['description'],
        'parameters': {
            'type': 'object',
            'properties': properties,
            'required': required
        },
        'returns': return_schema
    }


def get_available_methods(cls: type = None, include_inherited: bool = False) -> Dict[str, Any]:
    """Get all available methods with MCP-compatible schema.

    This function returns a complete schema of all available methods
    in the EqOdooConnection class, suitable for MCP server integration.

    Args:
        cls: Class to inspect (defaults to EqOdooConnection).
        include_inherited: Whether to include methods from parent classes.

    Returns:
        MCP-compatible schema with all available methods.
    """
    if cls is None:
        from .base_helper import EqOdooConnection
        cls = EqOdooConnection

    methods = []

    # Get all methods
    for name in dir(cls):
        # Skip private/magic methods
        if name.startswith('_'):
            continue

        attr = getattr(cls, name)
        if not callable(attr):
            continue

        # Skip inherited methods if not requested
        if not include_inherited:
            if name in dir(cls.__bases__[0]):
                continue

        schema = get_method_schema(name, cls)
        if schema:
            methods.append(schema)

    return {
        'schema_version': '1.0',
        'package': 'odoorpc-toolbox',
        'version': __version__,
        'description': 'Helper functions for OdooRPC operations',
        'methods': methods
    }


def print_available_methods(cls: type = None, format: str = 'text') -> None:
    """Print available methods in human-readable or JSON format.

    Args:
        cls: Class to inspect (defaults to EqOdooConnection).
        format: Output format ('text' or 'json').
    """
    import json

    schema = get_available_methods(cls)

    if format == 'json':
        print(json.dumps(schema, indent=2))
    else:
        print(f"odoorpc-toolbox v{schema['version']}")
        print("=" * 50)
        print(f"Available methods: {len(schema['methods'])}\n")

        for method in schema['methods']:
            params = ', '.join(
                f"{name}: {prop.get('type', 'any')}"
                for name, prop in method['parameters']['properties'].items()
            )
            returns = method['returns'].get('type', 'any')

            print(f"  {method['name']}({params}) -> {returns}")
            if method['description']:
                print(f"      {method['description'][:60]}...")
            print()
