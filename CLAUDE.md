# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**odoorpc-toolbox** is a Python package providing helper functions and utilities for working with OdooRPC. It simplifies common Odoo operations like partner management, state/country lookups, file operations, and sequence management.

- **Author**: Equitania Software GmbH
- **License**: GNU Affero General Public License v3
- **Python**: >= 3.10
- **Current Version**: 0.4.0

## Development Commands

```bash
# Create and activate virtual environment (UV preferred)
uv venv && source .venv/bin/activate.fish  # Fish shell
# Or with aliases: venv+

# Install package in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Build package for PyPI
uv build

# Run from installed package
python -c "from odoorpc_toolbox import EqOdooConnection; print('OK')"
```

## Architecture

```
odoorpc_toolbox/
├── odoo_connection.py   # Base OdooConnection class - handles YAML config, connection setup, authentication
└── base_helper.py       # EqOdooConnection class - extends base with helper methods for Odoo operations
```

### Class Hierarchy

1. **OdooConnection** (`odoo_connection.py`): Base connection class
   - Reads YAML configuration (Server: url, port, user, password, database, protocol)
   - Auto-detects HTTPS and adjusts protocol/port
   - Sets `auto_commit=True`, `active_test=False`, `tracking_disable=True`
   - Stores `odoo_version` as integer for version-specific logic

2. **EqOdooConnection** (`base_helper.py`): Extended class with helper methods
   - Partner operations: `get_res_partner_id()`, `get_res_partner_category_id()`, `get_res_partner_title_id()`
   - Location operations: `get_state_id()`, `extract_street_address_part()`
   - Sequence operations: `get_ir_sequence_number_next_actual()`, `set_ir_sequence_number_next_actual()`
   - File operations: `get_picture()` (BASE64 encoding)
   - Product operations: `get_product_uom_id()`, `set_stock_warehouse_orderpoint()`
   - Utility: `check_if_company_exists()`, `string_contains_numbers()`

## Configuration

YAML configuration file structure (see `yaml_examples/config.yaml`):

```yaml
Server:
  url: https://odoo.com       # Server URL (http:// or https://)
  port: 443                   # Port (443 for SSL, 8069 for local)
  user: admin                 # Username
  password: pw                # Password
  database: db                # Database name
  protocol: jsonrpc           # jsonrpc or jsonrpc+ssl
```

## Usage Example

```python
from odoorpc_toolbox import EqOdooConnection

connection = EqOdooConnection('config.yaml')

# Partner operations
partner_ids = connection.get_res_partner_id(customerno="CUST001")
category_id = connection.get_res_partner_category_id("Retail")

# Location operations
state_id = connection.get_state_id(country_id=21, state_name="California")
street, house_no = connection.extract_street_address_part("123 Main Street")

# File operations
image_data = connection.get_picture("/path/to/image.jpg")
```

## Version-Specific Logic

The package handles Odoo version differences automatically:
- `get_product_uom_id()`: Uses `product.uom` for v10-12, `uom.uom` for v13+

## Git Commit Conventions

- `[ADD]` - New features or extensions
- `[CHG]` - Modifications to existing code
- `[FIX]` - Bug fixes
