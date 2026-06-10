# OdooRPC Toolbox

> **Language / Sprache**: [DE](#deutsche-dokumentation) | [EN](#english-documentation)

[![Python](https://img.shields.io/badge/Python-≥3.10-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-AGPL--3.0-green.svg)](LICENSE.txt)
[![PyPI](https://img.shields.io/pypi/v/odoorpc-toolbox.svg)](https://pypi.org/project/odoorpc-toolbox/)

---

## Deutsche Dokumentation

### Projektübersicht

Ein Python-Paket mit Hilfsfunktionen und vollständig internalisierter OdooRPC-Implementierung für Odoo-Server-Kommunikation. JSON-RPC 2.0 Protokoll, MCP-kompatible Introspektion, TTL-Cache, Batch-Writes, native `search_read`-Optimierung und pluggbare Transport-Schicht mit optionalem HTTP/2 und Retry-Logik.

**Autor**: Equitania Software GmbH - Pforzheim - Germany
**Lizenz**: GNU Affero General Public License v3
**Python**: >= 3.10
**Version**: 0.8.0

### Funktionen

- **Vollständig internalisiertes OdooRPC** - Keine externe Abhängigkeit, JSON-RPC 2.0
- **Pluggbare Transport-Schicht** (v0.7.0) - urllib (Standard) oder httpx (Connection Pooling, HTTP/2, Retry)
- **TTL-Cache** für wiederholte Lookups (Länder, Bundesländer, UoMs) - bis zu 99x weniger RPC-Calls
- **Batch-Write** Context Manager - N Felder → 1 RPC statt N RPCs
- **Natives `search_read`** - 1 RPC statt search + read = 2 RPCs
- **Request-Metriken** - Thread-safe Tracking von Requests, Fehlern und Latenz
- **Retry mit Exponential Backoff** - Automatische Wiederholung bei 502/503/504
- **MCP-kompatible Introspektion** - JSON Schema für alle Helper-Methoden
- **Erweiterte YAML-Konfiguration** mit Transport, Retry, Timeout und Cache Sections
- **Config-Generator** - CLI-Befehl und Python-Funktion zum Erstellen von Konfigurationsdateien
- Hilfsfunktionen für häufige Odoo-Operationen:
  - Partner-Verwaltung (Suchen, Erstellen, Kategorien, Titel)
  - Länder- und Bundesland-Abfragen (nach Name oder ISO-Code)
  - Produkt-Operationen (Suche nach Referenz, UoM-Lookup)
  - Sequenzverwaltung (Lesen/Setzen)
  - Dateioperationen (Bilder als BASE64)
  - Generische Methodenausführung via `execute_method`

### Installation

```bash
# Standard (nur urllib Transport)
pip install odoorpc-toolbox

# Mit httpx Transport (HTTP/2, Connection Pooling, Retry)
pip install odoorpc-toolbox[httpx]

# Oder mit UV (empfohlen)
uv pip install odoorpc-toolbox[httpx]
```

### Konfiguration

Erstellen Sie eine YAML-Konfigurationsdatei manuell oder per CLI:

```bash
# Config-Datei generieren (alle Sections mit Defaults)
odoorpc-init-config

# Benutzerdefinierter Pfad
odoorpc-init-config -o meine_config.yaml

# Minimale Config (nur Server-Section)
odoorpc-init-config --minimal

# Mit benutzerdefinierten Werten
odoorpc-init-config --url http://localhost --port 8069 --database mydb
```

Oder programmatisch:

```python
from odoorpc_toolbox import generate_config

# Vollständige Config mit allen Sections
generate_config("odoo_config.yaml", url="http://localhost", port=8069, database="mydb")

# Minimale Config (nur Server)
generate_config("odoo_config.yaml", minimal=True)
```

#### Basis-Konfiguration

```yaml
Server:
  url: https://odoo.example.com   # http:// oder https:// (Protokoll wird automatisch erkannt)
  port: 443                        # 443 für SSL, 8069 für lokal
  user: admin
  password: secret
  database: mydb
  protocol: jsonrpc                # jsonrpc oder jsonrpc+ssl
```

#### Erweiterte Konfiguration (v0.7.0)

```yaml
Server:
  url: https://odoo.example.com
  port: 443
  user: admin
  password: secret
  database: mydb

# Transport Backend (optional)
# Benötigt: pip install odoorpc-toolbox[httpx]
transport:
  backend: auto              # "auto" (versucht httpx, Fallback urllib), "urllib" oder "httpx"
  http2: true                # HTTP/2 aktivieren (nur httpx)
  pool_connections: 10       # Max. gepoolte Verbindungen (nur httpx)

# Retry-Konfiguration (optional, nur httpx)
retry:
  max_attempts: 3            # Maximale Versuche (1 = kein Retry)
  backoff_factor: 0.5        # Exponentieller Backoff-Faktor in Sekunden
  retry_on: [502, 503, 504]  # HTTP-Statuscodes für Retry

# Timeout-Konfiguration (optional)
timeout:
  connect: 30                # Verbindungs-Timeout in Sekunden
  read: 120                  # Lese-Timeout in Sekunden

# Cache-Konfiguration (optional)
cache:
  maxsize: 256               # Maximale Cache-Einträge
  ttl: 3600                  # Time-to-Live in Sekunden
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

### Transport-Schicht (v0.7.0)

```python
from odoorpc_toolbox import ODOO, create_transport, RetryConfig

# Automatische Backend-Auswahl (httpx wenn verfügbar, sonst urllib)
odoo = ODOO('localhost', port=8069)

# Explizit httpx mit HTTP/2 und Retry
from odoorpc_toolbox import HttpxTransport
transport = HttpxTransport(
    http2=True,
    retry_config=RetryConfig(max_attempts=3, backoff_factor=0.5),
    pool_connections=10,
)
odoo = ODOO('localhost', port=8069, transport=transport)

# Request-Metriken abfragen
from odoorpc_toolbox import MetricsTransport, RequestMetrics
metrics = RequestMetrics()
mt = MetricsTransport(transport, metrics)
odoo = ODOO('localhost', port=8069, transport=mt)

# Nach einigen Operationen...
print(f"Requests: {metrics.total_requests}")
print(f"Fehler: {metrics.total_errors}")
print(f"Durchschnitt: {metrics.avg_time_ms:.1f} ms")
```

### JSON-2 API mit API-Key (Odoo 19+, v0.8.0)

Ab Odoo 19 nutzt odoorpc-toolbox automatisch die JSON-2 API
(`/json/2/<model>/<method>`) mit Bearer-Token-Authentifizierung.

```yaml
Server:
  url: https://odoo19.example.com
  port: 443
  user: admin
  api_key: IHR_API_KEY        # Settings -> Users -> API Keys -> New
  database: mydb
  protocol: jsonrpc+ssl
```

- **API-Key**: In Odoo unter Einstellungen → Benutzer → eigener Benutzer →
  API-Schlüssel erzeugen. Das `api_key`-Feld hat Vorrang vor `password`;
  ein API-Key im `password`-Feld funktioniert weiterhin (Abwärtskompatibilität).
- **API-only Benutzer**: Bot-Accounts ohne Passwort werden unterstützt —
  der Login läuft komplett über den API-Key (`res.users/context_get`).
- **Named Parameters**: Bekannte ORM-Methoden (search, read, write, …) werden
  automatisch von positionalen auf benannte Parameter gemappt; unbekannte
  Methoden mit positionalen Argumenten fallen mit DeprecationWarning auf das
  Legacy-`/jsonrpc` zurück (Entfernung in Odoo 22, Herbst 2028).
- **DB-Service**: `db.list()` und `db.dump()` nutzen ab v19 die
  `/web/database/*`-Controller; die übrigen DB-Operationen bleiben auf
  `/jsonrpc` (DeprecationWarning ab v19).
- **Report-Download**: Für Odoo ≥ 14 weiterhin nicht über die externe API
  möglich (CSRF/Session erforderlich) — die Fehlermeldung nennt Workarounds.

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

- **Runtime**: PyYAML >= 6.0 (einzige Pflichtabhängigkeit)
- **Optional**: httpx[http2] >= 0.25.0 (für HTTP/2, Connection Pooling, Retry)
- **OdooRPC**: Vollständig internalisiert - keine externe Abhängigkeit
- **Python**: >= 3.10

---

## English Documentation

### Project Overview

A Python package providing helper functions and a fully internalized OdooRPC implementation for Odoo server communication. JSON-RPC 2.0 protocol, MCP-compatible introspection, TTL cache, batch writes, native `search_read` optimization, and pluggable transport layer with optional HTTP/2 and retry logic.

**Author**: Equitania Software GmbH - Pforzheim - Germany
**License**: GNU Affero General Public License v3
**Python**: >= 3.10
**Version**: 0.8.0

### Features

- **Fully internalized OdooRPC** - No external dependency, JSON-RPC 2.0
- **Pluggable transport layer** (v0.7.0) - urllib (default) or httpx (connection pooling, HTTP/2, retry)
- **TTL cache** for repeated lookups (countries, states, UoMs) - up to 99x fewer RPC calls
- **Batch write** context manager - N fields → 1 RPC instead of N RPCs
- **Native `search_read`** - 1 RPC instead of search + read = 2 RPCs
- **Request metrics** - Thread-safe tracking of requests, errors, and latency
- **Retry with exponential backoff** - Automatic retry on 502/503/504
- **MCP-compatible introspection** - JSON Schema for all helper methods
- **Extended YAML configuration** with transport, retry, timeout, and cache sections
- **Config generator** - CLI command and Python function for creating configuration files
- Helper functions for common Odoo operations:
  - Partner management (search, create, categories, titles)
  - Country and state lookups (by name or ISO code)
  - Product operations (search by reference, UoM lookup)
  - Sequence management (read/set)
  - File operations (images as BASE64)
  - Generic method execution via `execute_method`

### Installation

```bash
# Standard (urllib transport only)
pip install odoorpc-toolbox

# With httpx transport (HTTP/2, connection pooling, retry)
pip install odoorpc-toolbox[httpx]

# Or with UV (recommended)
uv pip install odoorpc-toolbox[httpx]
```

### Configuration

Create a YAML configuration file manually or via CLI:

```bash
# Generate config file (all sections with defaults)
odoorpc-init-config

# Custom path
odoorpc-init-config -o my_config.yaml

# Minimal config (Server section only)
odoorpc-init-config --minimal

# With custom values
odoorpc-init-config --url http://localhost --port 8069 --database mydb
```

Or programmatically:

```python
from odoorpc_toolbox import generate_config

# Full config with all sections
generate_config("odoo_config.yaml", url="http://localhost", port=8069, database="mydb")

# Minimal config (Server only)
generate_config("odoo_config.yaml", minimal=True)
```

#### Basic Configuration

```yaml
Server:
  url: https://odoo.example.com   # http:// or https:// (protocol auto-detected)
  port: 443                        # 443 for SSL, 8069 for local
  user: admin
  password: secret
  database: mydb
  protocol: jsonrpc                # jsonrpc or jsonrpc+ssl
```

#### Extended Configuration (v0.7.0)

```yaml
Server:
  url: https://odoo.example.com
  port: 443
  user: admin
  password: secret
  database: mydb

# Transport backend (optional)
# Requires: pip install odoorpc-toolbox[httpx]
transport:
  backend: auto              # "auto" (tries httpx, falls back to urllib), "urllib", or "httpx"
  http2: true                # Enable HTTP/2 (httpx only)
  pool_connections: 10       # Max pooled connections (httpx only)

# Retry configuration (optional, httpx only)
retry:
  max_attempts: 3            # Maximum retry attempts (1 = no retry)
  backoff_factor: 0.5        # Exponential backoff base in seconds
  retry_on: [502, 503, 504]  # HTTP status codes that trigger retry

# Timeout configuration (optional)
timeout:
  connect: 30                # Connection timeout in seconds
  read: 120                  # Read timeout in seconds

# Cache configuration (optional)
cache:
  maxsize: 256               # Maximum number of cached entries
  ttl: 3600                  # Time-to-live in seconds
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

### Transport Layer (v0.7.0)

```python
from odoorpc_toolbox import ODOO, create_transport, RetryConfig

# Automatic backend selection (httpx if available, else urllib)
odoo = ODOO('localhost', port=8069)

# Explicit httpx with HTTP/2 and retry
from odoorpc_toolbox import HttpxTransport
transport = HttpxTransport(
    http2=True,
    retry_config=RetryConfig(max_attempts=3, backoff_factor=0.5),
    pool_connections=10,
)
odoo = ODOO('localhost', port=8069, transport=transport)

# Query request metrics
from odoorpc_toolbox import MetricsTransport, RequestMetrics
metrics = RequestMetrics()
mt = MetricsTransport(transport, metrics)
odoo = ODOO('localhost', port=8069, transport=mt)

# After some operations...
print(f"Requests: {metrics.total_requests}")
print(f"Errors: {metrics.total_errors}")
print(f"Average: {metrics.avg_time_ms:.1f} ms")
```

### JSON-2 API with API Key (Odoo 19+, v0.8.0)

Starting with Odoo 19, odoorpc-toolbox automatically uses the JSON-2 API
(`/json/2/<model>/<method>`) with Bearer token authentication.

```yaml
Server:
  url: https://odoo19.example.com
  port: 443
  user: admin
  api_key: YOUR_API_KEY       # Settings -> Users -> API Keys -> New
  database: mydb
  protocol: jsonrpc+ssl
```

- **API key**: Generate in Odoo under Settings → Users → your user →
  API Keys. The `api_key` field takes precedence over `password`; an API
  key placed in the `password` field keeps working (backward compatibility).
- **API-only users**: Bot accounts without a password are supported - login
  runs entirely on the API key (`res.users/context_get` bootstrap).
- **Named parameters**: Known ORM methods (search, read, write, ...) are
  mapped automatically from positional to named parameters; unknown methods
  with positional arguments fall back to the legacy `/jsonrpc` endpoint with
  a DeprecationWarning (removal scheduled for Odoo 22, fall 2028).
- **DB service**: `db.list()` and `db.dump()` use the `/web/database/*`
  controllers on v19+; the remaining DB operations stay on `/jsonrpc`
  (DeprecationWarning on v19+).
- **Report download**: Still not possible via the external API for
  Odoo >= 14 (CSRF/session required) - the error message lists workarounds.

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
OdooConnection (YAML config, auth, transport builder)
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
  └── RPC Layer
      ├── ConnectorJSONRPC / ConnectorJSONRPCSSL
      ├── Transport (v0.7.0)
      │   ├── UrllibTransport (default, no extra deps)
      │   └── HttpxTransport (HTTP/2, pooling, retry)
      ├── MetricsTransport (request tracking decorator)
      └── RetryConfig (exponential backoff + jitter)
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
| `generate_config(path, ...)` | Generate YAML config file | 0 |

*\* Cached methods: First call = 1 RPC, subsequent calls = 0 RPCs (cache hit)*

### CLI Commands

| Command | Description |
|---------|-------------|
| `odoorpc-init-config` | Generate YAML config file with all sections |
| `odoorpc-init-config -o path.yaml` | Custom output path |
| `odoorpc-init-config --minimal` | Server section only |
| `odoorpc-init-config --force` | Overwrite existing file |

### Development

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev,benchmark]"

# Unit tests (no Odoo required) - 227 tests
pytest tests/ -m "not integration"

# Integration tests (live Odoo required) - 60 tests
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest tests/integration/ -v

# Benchmarks - 16 scenarios
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest benchmarks/ -v

# Quality checks
ruff check . && black --check .
```

### Requirements

- **Runtime**: PyYAML >= 6.0 (only required dependency)
- **Optional**: httpx[http2] >= 0.25.0 (for HTTP/2, connection pooling, retry)
- **OdooRPC**: Fully internalized - no external dependency
- **Python**: >= 3.10

---

## Performance Benchmarks / Leistungsmessungen

| Scenario | v0.5.1 RPCs | v0.6.0+ RPCs | Reduction | Speedup |
|----------|-------------|--------------|-----------|---------|
| batch_write (5 fields) | 5 | 1 | 80% | 5.27x |
| search_read | 2 | 1 | 50% | 1.88-2.23x |
| cached_lookup (100x) | 100 | 1 | 99% | 101.63x |
| state_lookup (10x) | 10 | 1 | 90% | 8.72x |
| get_sequence | 2 | 1 | 50% | 1.93x |

*v0.7.0 transport abstraction introduces zero performance regression.*

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
