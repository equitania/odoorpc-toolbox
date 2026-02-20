# OdooRPC Toolbox

> **Language / Sprache**: [DE](#deutsche-dokumentation) | [EN](#english-documentation)

[![Python](https://img.shields.io/badge/Python-≥3.10-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-AGPL--3.0-green.svg)](LICENSE.txt)
[![PyPI](https://img.shields.io/pypi/v/odoorpc-toolbox.svg)](https://pypi.org/project/odoorpc-toolbox/)

---

## Deutsche Dokumentation

### Projektübersicht

Ein Python-Paket mit Hilfsfunktionen und vollständig internalisierter OdooRPC-Implementierung für Odoo-Server-Kommunikation. JSON-RPC 2.0 Protokoll, MCP-kompatible Introspektion, TTL-Cache, Batch-Writes und native `search_read`-Optimierung.

**Autor**: Equitania Software GmbH - Pforzheim - Germany
**Lizenz**: GNU Affero General Public License v3
**Python**: >= 3.10
**Version**: 0.6.0

### Funktionen

- **Vollständig internalisiertes OdooRPC** - Keine externe Abhängigkeit, JSON-RPC 2.0
- **TTL-Cache** für wiederholte Lookups (Länder, Bundesländer, UoMs) - bis zu 99x weniger RPC-Calls
- **Batch-Write** Context Manager - N Felder → 1 RPC statt N RPCs
- **Natives `search_read`** - 1 RPC statt search + read = 2 RPCs
- **MCP-kompatible Introspektion** - JSON Schema für alle Helper-Methoden
- **YAML-Konfiguration** mit automatischer HTTPS-Erkennung
- Hilfsfunktionen für häufige Odoo-Operationen:
  - Partner-Verwaltung (Suchen, Erstellen, Kategorien, Titel)
  - Länder- und Bundesland-Abfragen (nach Name oder ISO-Code)
  - Produkt-Operationen (Suche nach Referenz, UoM-Lookup)
  - Sequenzverwaltung (Lesen/Setzen)
  - Dateioperationen (Bilder als BASE64)
  - Generische Methodenausführung via `execute_method`

### Installation

```bash
# Standard
pip install odoorpc-toolbox

# Oder mit UV (empfohlen)
uv pip install odoorpc-toolbox
```

### Konfiguration

Erstellen Sie eine YAML-Konfigurationsdatei:

```yaml
Server:
  url: https://odoo.example.com   # http:// oder https:// (Protokoll wird automatisch erkannt)
  port: 443                        # 443 für SSL, 8069 für lokal
  user: admin
  password: secret
  database: mydb
  protocol: jsonrpc                # jsonrpc oder jsonrpc+ssl
```

### Schnelleinstieg

```python
from odoorpc_toolbox import EqOdooConnection

# Verbindung über YAML-Konfiguration
connection = EqOdooConnection('odoo_config.yaml')

# Native search_read - 1 RPC statt 2
partners = connection.search_read(
    "res.partner",
    [("is_company", "=", True)],
    ["name", "email", "city"],
    limit=10
)
```

### Partner-Operationen

```python
# Partner erstellen
partner_id = connection.create_partner(
    name="Musterfirma GmbH",
    is_company=True,
    email="info@musterfirma.de",
    city="Stuttgart",
    zip_code="70173"
)

# Firma suchen
company_id = connection.check_if_company_exists("Musterfirma GmbH", "70173", "Stuttgart")

# Kategorien abrufen oder erstellen
category_id = connection.get_res_partner_category_id("Einzelhandel")

# Partner-Titel
title_id = connection.get_res_partner_title_id("Herr")
```

### Standort-Operationen

```python
# Bundesland-ID (mit automatischem Cache)
state_id = connection.get_state_id(country_id=21, state_name="Bayern")

# Land nach ISO-Code (gecacht)
de_id = connection.get_country_id_by_code("DE")

# Land nach Name
germany_id = connection.get_country_id("Germany")

# Adresse parsen
strasse, hausnr = connection.extract_street_address_part("Hauptstraße 123")
```

### Performance-Optimierungen (v0.6.0)

```python
from odoorpc_toolbox import batch_write

# Batch-Write: 5 Felder → 1 RPC (statt 5 einzelne RPCs)
with batch_write(connection.odoo):
    record.name = "Neuer Name"
    record.email = "neu@example.com"
    record.phone = "+49 711 1234567"
    record.street = "Königstraße 1"
    record.city = "Stuttgart"

# Cache: 10 identische Lookups → 1 RPC + 9 Cache-Hits
for state in ["Bayern", "Bayern", "Bayern"]:
    state_id = connection.get_state_id(21, state)  # Nur der erste Aufruf macht einen RPC

# Cache leeren (z.B. nach Datenänderung)
connection.clear_cache()
```

### MCP-Introspektion

```python
from odoorpc_toolbox import get_available_methods, print_available_methods

# Alle Methoden als MCP-kompatibles JSON Schema
schema = get_available_methods()

# Menschenlesbare Ausgabe
print_available_methods(format='text')
```

### Sequenz-Verwaltung

```python
# Nächste Sequenznummer lesen (1 RPC)
next_num = connection.get_ir_sequence_number_next_actual("sale.order")

# Sequenznummer setzen (2 RPCs)
connection.set_ir_sequence_number_next_actual("sale.order", 1000)
```

### Direkter ODOO-Zugriff

```python
from odoorpc_toolbox import ODOO

# Direktverbindung ohne YAML
odoo = ODOO('localhost', port=8069)
odoo.login('mydb', 'admin', 'admin')

# Voller Zugriff auf Odoo-Modelle
Partner = odoo.env['res.partner']
partner_ids = Partner.search([('is_company', '=', True)])
```

### Entwicklung

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev,benchmark]"

# Tests (kein Odoo nötig)
pytest tests/ -m "not integration"

# Qualitätsprüfung
ruff check . && black --check .
```

### Abhängigkeiten

- **Runtime**: PyYAML >= 6.0 (einzige Abhängigkeit)
- **OdooRPC**: Vollständig internalisiert - keine externe Abhängigkeit
- **Python**: >= 3.10

---

## English Documentation

### Project Overview

A Python package providing helper functions and a fully internalized OdooRPC implementation for Odoo server communication. JSON-RPC 2.0 protocol, MCP-compatible introspection, TTL cache, batch writes, and native `search_read` optimization.

**Author**: Equitania Software GmbH - Pforzheim - Germany
**License**: GNU Affero General Public License v3
**Python**: >= 3.10
**Version**: 0.6.0

### Features

- **Fully internalized OdooRPC** - No external dependency, JSON-RPC 2.0
- **TTL cache** for repeated lookups (countries, states, UoMs) - up to 99x fewer RPC calls
- **Batch write** context manager - N fields → 1 RPC instead of N RPCs
- **Native `search_read`** - 1 RPC instead of search + read = 2 RPCs
- **MCP-compatible introspection** - JSON Schema for all helper methods
- **YAML configuration** with automatic HTTPS detection
- Helper functions for common Odoo operations:
  - Partner management (search, create, categories, titles)
  - Country and state lookups (by name or ISO code)
  - Product operations (search by reference, UoM lookup)
  - Sequence management (read/set)
  - File operations (images as BASE64)
  - Generic method execution via `execute_method`

### Installation

```bash
# Standard
pip install odoorpc-toolbox

# Or with UV (recommended)
uv pip install odoorpc-toolbox
```

### Configuration

Create a YAML configuration file:

```yaml
Server:
  url: https://odoo.example.com   # http:// or https:// (protocol auto-detected)
  port: 443                        # 443 for SSL, 8069 for local
  user: admin
  password: secret
  database: mydb
  protocol: jsonrpc                # jsonrpc or jsonrpc+ssl
```

### Quick Start

```python
from odoorpc_toolbox import EqOdooConnection

# Connect via YAML configuration
connection = EqOdooConnection('odoo_config.yaml')

# Native search_read - 1 RPC instead of 2
partners = connection.search_read(
    "res.partner",
    [("is_company", "=", True)],
    ["name", "email", "city"],
    limit=10
)
```

### Partner Operations

```python
# Create partner
partner_id = connection.create_partner(
    name="Acme Corp",
    is_company=True,
    email="info@acme.com",
    city="Stuttgart",
    zip_code="70173"
)

# Check if company exists
company_id = connection.check_if_company_exists("Acme Corp", "70173", "Stuttgart")

# Get or create categories
category_id = connection.get_res_partner_category_id("Retail")

# Partner titles
title_id = connection.get_res_partner_title_id("Mr.")
```

### Location Operations

```python
# State ID (automatically cached)
state_id = connection.get_state_id(country_id=233, state_name="California")

# Country by ISO code (cached)
us_id = connection.get_country_id_by_code("US")

# Country by name
usa_id = connection.get_country_id("United States")

# Parse address
street, house_no = connection.extract_street_address_part("123 Main Street")
```

### Performance Optimizations (v0.6.0)

```python
from odoorpc_toolbox import batch_write

# Batch write: 5 fields → 1 RPC (instead of 5 individual RPCs)
with batch_write(connection.odoo):
    record.name = "New Name"
    record.email = "new@example.com"
    record.phone = "+1 555 1234567"
    record.street = "123 Main St"
    record.city = "New York"

# Cache: 10 identical lookups → 1 RPC + 9 cache hits
for state in ["California", "California", "California"]:
    state_id = connection.get_state_id(233, state)  # Only the first call makes an RPC

# Clear cache (e.g., after data changes)
connection.clear_cache()
```

### MCP Introspection

```python
from odoorpc_toolbox import get_available_methods, print_available_methods

# All methods as MCP-compatible JSON Schema
schema = get_available_methods()

# Human-readable output
print_available_methods(format='text')
```

### Sequence Management

```python
# Read next sequence number (1 RPC)
next_num = connection.get_ir_sequence_number_next_actual("sale.order")

# Set sequence number (2 RPCs)
connection.set_ir_sequence_number_next_actual("sale.order", 1000)
```

### Direct ODOO Access

```python
from odoorpc_toolbox import ODOO

# Direct connection without YAML
odoo = ODOO('localhost', port=8069)
odoo.login('mydb', 'admin', 'admin')

# Full access to Odoo models
Partner = odoo.env['res.partner']
partner_ids = Partner.search([('is_company', '=', True)])
```

### Architecture

```
OdooConnection (YAML config, auth)
  └── EqOdooConnection (20+ helper methods, TTL cache, batch write)
        ├── Partner ops: create_partner, check_if_company_exists, categories, titles
        ├── Location ops: get_country_id, get_state_id, extract_street_address_part
        ├── Product ops: get_product_by_ref, get_product_uom_id
        ├── Sequence ops: get/set_ir_sequence_number_next_actual
        ├── Generic: execute_method, search_read (native, 1 RPC)
        └── Cache: TTLCache (configurable maxsize + TTL, thread-safe)

ODOO (internalized OdooRPC)
  ├── Environment → Model → Fields (14 descriptors)
  ├── DB service (dump/restore/create/drop)
  ├── Report service
  ├── Session persistence (~/.odoorpcrc)
  └── RPC (JSON-RPC 2.0 via ConnectorJSONRPC / ConnectorJSONRPCSSL)
```

### API Reference

| Method | Description | RPCs |
|--------|-------------|------|
| `search_read(model, domain, fields, ...)` | Search + read in single call | 1 |
| `create_partner(name, is_company, ...)` | Create partner/company | 1 |
| `check_if_company_exists(name, zip, city)` | Find existing company | 1 |
| `get_state_id(country_id, state_name)` | State lookup (cached) | 1* |
| `get_country_id(country_name)` | Country by name | 1 |
| `get_country_id_by_code(code)` | Country by ISO code (cached) | 1* |
| `get_product_uom_id(uom)` | Unit of measure (cached) | 1* |
| `get_product_by_ref(default_code)` | Product by internal ref | 1 |
| `get_product_template_by_ref(code)` | Product template by ref | 1 |
| `get_res_partner_category_id(name)` | Get/create category (cached) | 1* |
| `get_res_partner_title_id(title)` | Title lookup (cached) | 1* |
| `get_ir_sequence_number_next_actual(code)` | Read sequence number | 1 |
| `set_ir_sequence_number_next_actual(code, val)` | Set sequence number | 2 |
| `execute_method(model, method, ...)` | Generic method call | 1 |
| `get_picture(path, max_size_mb)` | Load image as BASE64 | 0 |
| `extract_street_address_part(street)` | Parse street/house number | 0 |
| `batch_write(odoo)` | Context manager for batched writes | 1 |

*\* Cached methods: First call = 1 RPC, subsequent calls = 0 RPCs (cache hit)*

### Development

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev,benchmark]"

# Unit tests (no Odoo required)
pytest tests/ -m "not integration"

# Integration tests (live Odoo required)
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest tests/integration/ -v

# Benchmarks
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest benchmarks/ -v

# Quality checks
ruff check . && black --check .
```

### Requirements

- **Runtime**: PyYAML >= 6.0 (only dependency)
- **OdooRPC**: Fully internalized - no external dependency
- **Python**: >= 3.10

---

## Performance Benchmarks / Leistungsmessungen

| Scenario | v0.5.1 RPCs | v0.6.0 RPCs | Reduction | Speedup |
|----------|-------------|-------------|-----------|---------|
| batch_write (5 fields) | 5 | 1 | 80% | 5.56x |
| search_read | 2 | 1 | 50% | 1.28-2.09x |
| cached_lookup (100x) | 100 | 1 | 99% | 99.96x |
| state_lookup (10x) | 10 | 1 | 90% | 8.82x |
| get_sequence | 2 | 1 | 50% | 1.92x |

## Contributing / Mitwirken

Contributions are welcome! Please feel free to submit a Pull Request.

Beiträge sind willkommen! Bitte zögern Sie nicht, einen Pull Request einzureichen.

```bash
# Development setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev,benchmark]"
pytest tests/ -m "not integration"
ruff check . && black --check .
```

## License / Lizenz

This project is licensed under the GNU Affero General Public License v3 - see the [LICENSE.txt](LICENSE.txt) file for details.

Dieses Projekt ist unter der GNU Affero General Public License v3 lizenziert - siehe [LICENSE.txt](LICENSE.txt) für Details.
